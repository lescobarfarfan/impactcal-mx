"""Year-state ↔ IBTrACS storm crosswalk, version v1 (DC-XWALK-1; CAL-XWALK-01/02).

v1 is **hazard-side** (CAL-XWALK-01, unblocked by the frozen `haz_tc.h5` /
`haz_rain.h5`): the affected set per year-state comes from the per-state
footprints of the frozen hazards (`impactcal.hazard.footprints`) —
`sids_viento` = storms with wind above `v_thresh` over the state,
`sids_cono_lluvia` = storms whose rain cone (TCRain above
`crosswalk.umbral_lluvia_mm`) reaches it. CENAPRED events still anchor the
loss side: CT events are matched to SIDs by nombre+temporada (with a
conservative fuzzy fallback for typos, flagged `nombre_fuzzy`), then by
date-window overlap; date-window candidates are disambiguated by whether
their footprint actually touches the event's states.

Family-assignment rule (CAL-XWALK-02, v1): an LLUV/INUND event is
cyclone-related when a storm's rain cone reaches the state that year **and**
the event window overlaps that storm's window (±buffer) — the v0 national
date-window proxy is superseded by the actual cone. Year-states in the
affected set with no CENAPRED event are kept with empty familia and flagged
`tormenta_sin_perdida` (inside the panel) or `fuera_panel_cenapred` (after
it); CT-reported year-states that no modeled storm touches are flagged
`perdida_sin_tormenta_modelada` (CAL-XWALK-01 verification).

CLI::

    python -m impactcal.target.crosswalk [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

# Claves INEGI (DC-CONV-5), keyed by the entity names as normalized by the
# climateCCR CENAPRED pipeline (`limpieza_cnsf.clasificar_entidad`), plus
# long-form official aliases for robustness.
ENTIDAD_A_CVE = {
    "Aguascalientes": "01",
    "Baja California": "02",
    "Baja California Sur": "03",
    "Campeche": "04",
    "Coahuila": "05",
    "Coahuila de Zaragoza": "05",
    "Colima": "06",
    "Chiapas": "07",
    "Chihuahua": "08",
    "Ciudad de México": "09",
    "Distrito Federal": "09",
    "Durango": "10",
    "Guanajuato": "11",
    "Guerrero": "12",
    "Hidalgo": "13",
    "Jalisco": "14",
    "Estado de México": "15",
    "México": "15",
    "Michoacán": "16",
    "Michoacán de Ocampo": "16",
    "Morelos": "17",
    "Nayarit": "18",
    "Nuevo León": "19",
    "Oaxaca": "20",
    "Puebla": "21",
    "Querétaro": "22",
    "Quintana Roo": "23",
    "San Luis Potosí": "24",
    "Sinaloa": "25",
    "Sonora": "26",
    "Tabasco": "27",
    "Tamaulipas": "28",
    "Tlaxcala": "29",
    "Veracruz": "30",
    "Veracruz de Ignacio de la Llave": "30",
    "Yucatán": "31",
    "Zacatecas": "32",
}

# Type words dropped when extracting the storm proper name from `nombre_evento`.
_PALABRAS_TIPO = {
    "CICLON",
    "HURACAN",
    "TORMENTA",
    "DEPRESION",
    "TROPICAL",
    "REMANENTES",
    "REMANENTE",
    "ONDA",
    "DE",
    "DEL",
    "EL",
    "LA",
    "TT",
    "DT",
    "TD",
}

# Numbered depressions: CENAPRED in Spanish ("Once-E") vs IBTrACS/ATCF in English.
_NUMERAL_ES_EN = {
    "UNO": "ONE",
    "DOS": "TWO",
    "TRES": "THREE",
    "CUATRO": "FOUR",
    "CINCO": "FIVE",
    "SEIS": "SIX",
    "SIETE": "SEVEN",
    "OCHO": "EIGHT",
    "NUEVE": "NINE",
    "DIEZ": "TEN",
    "ONCE": "ELEVEN",
    "DOCE": "TWELVE",
    "TRECE": "THIRTEEN",
    "CATORCE": "FOURTEEN",
    "QUINCE": "FIFTEEN",
    "DIECISEIS": "SIXTEEN",
    "DIECISIETE": "SEVENTEEN",
    "DIECIOCHO": "EIGHTEEN",
    "DIECINUEVE": "NINETEEN",
    "VEINTE": "TWENTY",
}

# Conservative cutoff for the fuzzy name fallback (CENAPRED typos, e.g.
# "Julette" → JULIETTE); accepted only when the season has a single close name.
_FUZZY_CUTOFF = 0.8


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def extract_storm_names(nombre_evento: str) -> list[str]:
    """IBTrACS-comparable storm name(s) from a CENAPRED `nombre_evento`.

    "Ciclón Odile" → ["ODILE"]; "Ingrid y Manuel" → ["INGRID", "MANUEL"];
    "Depresión Once-E" → ["ELEVEN-E"]; no proper name left → [].
    """
    if not nombre_evento or not nombre_evento.strip():
        return []
    plano = _sin_acentos(nombre_evento).upper().replace(",", " Y ")
    nombres = []
    for parte in plano.split(" Y "):
        tokens = [t for t in parte.replace(".", " ").split() if t and t not in _PALABRAS_TIPO]
        if not tokens:
            continue
        nombre = "-".join(" ".join(tokens).split())
        base, _, sufijo = nombre.partition("-")
        if base in _NUMERAL_ES_EN:
            nombre = _NUMERAL_ES_EN[base] + (f"-{sufijo}" if sufijo else "")
        nombres.append(nombre)
    return nombres


def _ventanas_solapan(
    ini_a: pd.Timestamp, fin_a: pd.Timestamp, ini_b: pd.Timestamp, fin_b: pd.Timestamp
) -> bool:
    if pd.isna(ini_a) or pd.isna(ini_b):
        return False
    fin_a = fin_a if pd.notna(fin_a) else ini_a
    fin_b = fin_b if pd.notna(fin_b) else ini_b
    return ini_a <= fin_b and ini_b <= fin_a


def _claves_evento(estados: str) -> set[str]:
    return {ENTIDAD_A_CVE[e.strip()] for e in str(estados).split("|") if e.strip() in ENTIDAD_A_CVE}


def match_events(
    eventos: pd.DataFrame,
    storm_index: pd.DataFrame,
    *,
    buffer_dias: int = 3,
    sids_por_estado: dict[str, set[str]] | None = None,
) -> pd.DataFrame:
    """Event-level match of CT events against the IBTrACS per-storm index.

    Name matches get a conservative fuzzy fallback (`nombre_fuzzy`). When
    `sids_por_estado` (state → SIDs with any hazard footprint) is given,
    multi-candidate date matches keep only candidates whose footprint touches
    one of the event's states (`candidatos_filtrados_huella`); if none does,
    the candidates are kept and flagged `candidatos_sin_huella`.

    Returns one row per event: `evento_id, anio, nombre_evento, nombre_extraido,
    metodo_match {nombre|fechas|sin_match}, sids (';'-sep), flag_evento`.
    """
    buffer = pd.Timedelta(days=buffer_dias)
    filas = []
    for _, ev in eventos.iterrows():
        anio = int(ev["anio"])
        temporada = storm_index[storm_index["season"] == anio]
        nombres = extract_storm_names(ev["nombre_evento"])
        sids: list[str] = []
        flags: list[str] = []
        metodo = "sin_match"
        for nombre in nombres:
            cand = temporada[temporada["name"].str.upper() == nombre]
            if cand.empty:
                cercanos = difflib.get_close_matches(
                    nombre,
                    temporada["name"].str.upper().unique().tolist(),
                    n=2,
                    cutoff=_FUZZY_CUTOFF,
                )
                if len(cercanos) == 1:
                    cand = temporada[temporada["name"].str.upper() == cercanos[0]]
                    flags.append("nombre_fuzzy")
            sids.extend(cand["sid"].tolist())
        if sids:
            metodo = "nombre"
            if len(sids) > len(nombres):
                flags.append("sid_ambiguo")
        else:
            if nombres:
                flags.append("nombre_sin_sid")
            ini = pd.to_datetime(ev["fecha_inicio"], errors="coerce")
            fin = pd.to_datetime(ev["fecha_fin"], errors="coerce")
            if pd.isna(ini):
                flags.append("fecha_faltante")
            else:
                cerca = temporada[temporada["toca_mexico"]]
                cand = cerca[
                    [
                        _ventanas_solapan(ini, fin, s.fecha_inicio - buffer, s.fecha_fin + buffer)
                        for s in cerca.itertuples()
                    ]
                ]
                sids = cand["sid"].tolist()
                if sids:
                    metodo = "fechas"
                    if len(sids) > 1 and sids_por_estado is not None:
                        tocan = {
                            s
                            for cve in _claves_evento(ev.get("estados", ""))
                            for s in sids_por_estado.get(cve, set())
                        }
                        filtrados = [s for s in sids if s in tocan]
                        if filtrados and len(filtrados) < len(sids):
                            sids = filtrados
                            flags.append("candidatos_filtrados_huella")
                        elif not filtrados:
                            flags.append("candidatos_sin_huella")
                    if len(sids) > 1:
                        flags.append("candidatos_multiples")
        if not sids:
            flags.append("ct_sin_sid")
        filas.append(
            {
                "evento_id": ev["evento_id"],
                "anio": anio,
                "nombre_evento": ev["nombre_evento"],
                "nombre_extraido": ";".join(nombres),
                "metodo_match": metodo,
                "sids": ";".join(sorted(set(sids))),
                "flag_evento": ";".join(sorted(set(flags))),
            }
        )
    return pd.DataFrame(filas)


def _explotar_estados(eventos: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """One row per (event, state); returns also the unmapped entity labels."""
    df = eventos.copy()
    df["entidad"] = df["estados"].str.split("|")
    df = df.explode("entidad")
    df["entidad"] = df["entidad"].str.strip()
    df["cve_ent"] = df["entidad"].map(ENTIDAD_A_CVE)
    no_localizados = sorted(df.loc[df["cve_ent"].isna(), "entidad"].unique())
    return df.dropna(subset=["cve_ent"]), no_localizados


def _afectados(
    huellas: pd.DataFrame, peril: str, umbral: float, temporada_sid: dict[str, int]
) -> dict[tuple[int, str], set[str]]:
    """(año, estado) → SIDs whose `peril` footprint exceeds `umbral` there."""
    sel = huellas[(huellas["peril"] == peril) & (huellas["int_max"] > umbral)]
    afect: dict[tuple[int, str], set[str]] = {}
    for fila in sel.itertuples():
        if fila.sid in temporada_sid:
            afect.setdefault((int(temporada_sid[fila.sid]), fila.cve_ent), set()).add(fila.sid)
    return afect


def build_crosswalk(
    eventos: pd.DataFrame,
    storm_index: pd.DataFrame,
    config: dict[str, Any],
    huellas: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Build the v1 crosswalk from CENAPRED events, the storm index and the
    per-state hazard footprints.

    Returns `(crosswalk año×estado, event-level match table, summary dict)`.
    `eventos` is the frozen `eventos_cenapred_climada.csv` as strings;
    `huellas` the `huellas_estatales.csv` table (sid, cve_ent, peril, int_max).
    """
    cfg = config["crosswalk"]
    ciclonicos = set(cfg["subtipos_ciclonicos"])
    fluviales = set(cfg["subtipos_fluviales"])
    buffer = pd.Timedelta(days=int(cfg["buffer_dias"]))
    version = cfg["version"]
    v_thresh = float(config["impacto"]["v_thresh"])
    if cfg.get("umbral_lluvia_mm") is None:
        raise ValueError("crosswalk.umbral_lluvia_mm sin decidir (OQ-CAL-02)")
    umbral_lluvia = float(cfg["umbral_lluvia_mm"])

    temporada_sid = dict(zip(storm_index["sid"], storm_index["season"], strict=True))
    ventana_sid = {s.sid: (s.fecha_inicio, s.fecha_fin) for s in storm_index.itertuples()}
    afect_v = _afectados(huellas, "viento", v_thresh, temporada_sid)
    afect_r = _afectados(huellas, "lluvia", umbral_lluvia, temporada_sid)
    presencia = huellas.groupby("cve_ent")["sid"].agg(set).to_dict()

    universo = eventos[
        (eventos["en_alcance_climatico"] == "si")
        & (eventos["subtipo"].isin(ciclonicos | fluviales))
    ].copy()
    universo["anio"] = universo["anio"].astype(int)
    # El panel termina donde CENAPRED deja de ser utilizable, no donde deja de
    # haber filas: 2024 sólo tiene resumen ejecutivo (CAL-TARGET-06), así que
    # `periodo.anio_final` manda cuando está fijado.
    anio_final = config.get("periodo", {}).get("anio_final")
    panel_max = (
        min(int(universo["anio"].max()), int(anio_final))
        if anio_final
        else int(universo["anio"].max())
    )

    ct = universo[universo["subtipo"] == "CT"]
    match = match_events(
        ct, storm_index, buffer_dias=int(cfg["buffer_dias"]), sids_por_estado=presencia
    )
    flags_por_evento = dict(zip(match["evento_id"], match["flag_evento"], strict=True))

    def _lluvia_ciclonica(ev: pd.Series, anio: int, cve_ent: str) -> bool | None:
        """CAL-XWALK-02 v1: cone reaches the state AND event overlaps that
        storm's window (±buffer). None = event dates missing."""
        ini = pd.to_datetime(ev["fecha_inicio"], errors="coerce")
        fin = pd.to_datetime(ev["fecha_fin"], errors="coerce")
        if pd.isna(ini):
            return None
        return any(
            _ventanas_solapan(ini, fin, ventana_sid[s][0] - buffer, ventana_sid[s][1] + buffer)
            for s in afect_r.get((anio, cve_ent), set())
            if s in ventana_sid
        )

    exploded, no_localizados = _explotar_estados(universo)

    filas = []
    for (anio, cve_ent), grupo in exploded.groupby(["anio", "cve_ent"]):
        es_cic = grupo["subtipo"].isin(ciclonicos)
        es_flu = grupo["subtipo"].isin(fluviales)
        flags: set[str] = set()

        for eid in grupo.loc[grupo["subtipo"] == "CT", "evento_id"]:
            flags.update(f for f in flags_por_evento.get(eid, "").split(";") if f)

        solapes = [_lluvia_ciclonica(ev, anio, cve_ent) for _, ev in grupo[es_flu].iterrows()]
        if any(s is None for s in solapes):
            flags.add("fecha_faltante")
        solapes_bool = [bool(s) for s in solapes]

        if es_cic.any() and not es_flu.any():
            familia, regla = "ciclonica", "ct_reportado"
        elif es_flu.any() and not es_cic.any():
            if solapes_bool and all(solapes_bool):
                familia, regla = "ciclonica", "lluvia_en_cono_tormenta"
            elif any(solapes_bool):
                familia, regla = "mixta_flag", "mixto_parcial_cono"
            else:
                familia, regla = "fluvial", "fluvial_independiente"
        else:
            if solapes_bool and all(solapes_bool):
                familia, regla = "ciclonica", "ct_y_lluvia_en_cono"
            else:
                familia, regla = "mixta_flag", "mixto"

        sids_v = afect_v.get((anio, cve_ent), set())
        sids_r = afect_r.get((anio, cve_ent), set())
        if es_cic.any() and not sids_v and not sids_r:
            flags.add("perdida_sin_tormenta_modelada")

        filas.append(
            {
                "anio": anio,
                "cve_ent": cve_ent,
                "sids_viento": ";".join(sorted(sids_v)),
                "sids_cono_lluvia": ";".join(sorted(sids_r)),
                "familia_asignada": familia,
                "flag_revision": ";".join(sorted(flags)),
                "regla_aplicada": regla,
                "version_crosswalk": version,
            }
        )

    claves_perdida = {(f["anio"], f["cve_ent"]) for f in filas}
    for anio, cve_ent in sorted(set(afect_v) | set(afect_r)):
        if (anio, cve_ent) in claves_perdida:
            continue
        filas.append(
            {
                "anio": anio,
                "cve_ent": cve_ent,
                "sids_viento": ";".join(sorted(afect_v.get((anio, cve_ent), set()))),
                "sids_cono_lluvia": ";".join(sorted(afect_r.get((anio, cve_ent), set()))),
                "familia_asignada": "",
                "flag_revision": (
                    "tormenta_sin_perdida" if anio <= panel_max else "fuera_panel_cenapred"
                ),
                "regla_aplicada": "afectado_solo_hazard",
                "version_crosswalk": version,
            }
        )

    xwalk = pd.DataFrame(filas).sort_values(["anio", "cve_ent"]).reset_index(drop=True)
    # Un año-estado más allá del panel utilizable nunca debe parecer una fila normal,
    # tenga o no pérdida reportada (2024 = sólo resumen ejecutivo, CAL-TARGET-06).
    fuera = (xwalk["anio"] > panel_max) & ~xwalk["flag_revision"].str.contains(
        "fuera_panel_cenapred"
    )
    xwalk.loc[fuera, "flag_revision"] = (
        xwalk.loc[fuera, "flag_revision"] + ";fuera_panel_cenapred"
    ).str.lstrip(";")

    resumen = {
        "n_eventos_universo": int(len(universo)),
        "n_eventos_ct": int(len(ct)),
        "match_por_metodo": match["metodo_match"].value_counts().to_dict(),
        "n_anio_estado": int(len(xwalk)),
        "familias": xwalk["familia_asignada"].value_counts().to_dict(),
        "reglas": xwalk["regla_aplicada"].value_counts().to_dict(),
        "entidades_no_localizadas": no_localizados,
        "v_thresh_ms": v_thresh,
        "umbral_lluvia_mm": umbral_lluvia,
        "version_crosswalk": version,
    }
    return xwalk, match, resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    from impactcal.hazard.ibtracs import load_storm_index

    config = load_config(args.config)
    paths = ProjectPaths()
    cfg = config["crosswalk"]

    eventos_csv = paths.data / "cenapred" / "consolidados" / "eventos_cenapred_climada.csv"
    huellas_csv = paths.data / "crosswalk" / "huellas_estatales.csv"
    ibtracs_dir = paths.data / "ibtracs" / "crudos"
    if not verify_provenance(huellas_csv):
        raise RuntimeError(
            f"Huellas corruptas o sin procedencia (impactcal.hazard.footprints): {huellas_csv}"
        )
    eventos = pd.read_csv(eventos_csv, dtype=str, na_filter=False)
    huellas = pd.read_csv(huellas_csv, dtype={"cve_ent": str})
    storm_index = load_storm_index(
        ibtracs_dir,
        season_min=int(config["periodo"]["anio_inicial"]),
        bbox=cfg["bbox_mexico"],
    )

    xwalk, match, resumen = build_crosswalk(eventos, storm_index, config, huellas)

    out_dir = paths.data / "crosswalk"
    out_dir.mkdir(parents=True, exist_ok=True)
    salida_xwalk = out_dir / "crosswalk_anio_estado_tormentas.csv"
    salida_match = out_dir / "eventos_sid_match.csv"
    xwalk.to_csv(salida_xwalk, index=False)
    match.to_csv(salida_match, index=False)

    insumos = {
        eventos_csv.name: _sha256(eventos_csv),
        huellas_csv.name: _sha256(huellas_csv),
        **{f.name: _sha256(f) for f in sorted(ibtracs_dir.glob("ibtracs.*.csv"))},
    }
    for salida in (salida_xwalk, salida_match):
        write_provenance(
            salida,
            source="impactcal.target.crosswalk (determinista, v1 lado-hazard)",
            insumos=insumos,
            version_crosswalk=cfg["version"],
            regla=(
                "CAL-XWALK-01/02 v1: huellas hazard (viento>v_thresh, cono lluvia>umbral) "
                "+ nombre/temporada con fuzzy + ventana de fechas desambiguada por huella"
            ),
            v_thresh_ms=float(config["impacto"]["v_thresh"]),
            umbral_lluvia_mm=float(cfg["umbral_lluvia_mm"]),
        )

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"crosswalk_{cfg['version']}_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Crosswalk v1: determinista (sin RNG); semilla registrada por CAL-GEN-05.",
    ).write(paths.manifests, paths.root)

    print(f"crosswalk: {salida_xwalk}")
    print(f"match eventos: {salida_match}")
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
