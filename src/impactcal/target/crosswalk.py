"""Year-state ↔ IBTrACS storm crosswalk, version v0 (DC-XWALK-1; CAL-XWALK-01/02).

v0 is **loss-side only**: the affected set comes from CENAPRED-reported events,
matched to IBTrACS storms by `nombre_evento` + season (fallback: date-window
overlap with tracks near Mexico). The canonical hazard-side definition — wind
field above `v_thresh` plus the TCRain cone (CAL-XWALK-01) — requires frozen
hazards and lands in v1 once the timestep test closes (OQ-CAL-01); the column
`sids_cono_lluvia` is therefore left empty in v0.

Family-assignment rule implemented (v0 proxy of CAL-XWALK-02, date-window in
place of the rain cone): a year-state whose only events are LLUV/INUND is
`ciclonica` when all those events overlap a matched storm window of that year
(rain filed under inundación perils — the inland CDMX case), `fluvial` when
none do, and `mixta_flag` otherwise.

CLI::

    python -m impactcal.target.crosswalk [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, write_provenance

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


def match_events(
    eventos: pd.DataFrame, storm_index: pd.DataFrame, *, buffer_dias: int = 3
) -> pd.DataFrame:
    """Event-level match of CT events against the IBTrACS per-storm index.

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


def build_crosswalk(
    eventos: pd.DataFrame, storm_index: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Build the v0 crosswalk from the CENAPRED event table and the storm index.

    Returns `(crosswalk año×estado, event-level match table, summary dict)`.
    `eventos` is the frozen `eventos_cenapred_climada.csv` as strings.
    """
    cfg = config["crosswalk"]
    ciclonicos = set(cfg["subtipos_ciclonicos"])
    fluviales = set(cfg["subtipos_fluviales"])
    buffer = pd.Timedelta(days=int(cfg["buffer_dias"]))
    version = cfg["version"]

    universo = eventos[
        (eventos["en_alcance_climatico"] == "si")
        & (eventos["subtipo"].isin(ciclonicos | fluviales))
    ].copy()
    universo["anio"] = universo["anio"].astype(int)

    ct = universo[universo["subtipo"] == "CT"]
    match = match_events(ct, storm_index, buffer_dias=int(cfg["buffer_dias"]))
    sids_por_evento = dict(zip(match["evento_id"], match["sids"], strict=True))
    flags_por_evento = dict(zip(match["evento_id"], match["flag_evento"], strict=True))

    # Matched storm windows per year (national), for the rain-in-storm-window rule.
    sids_anio: dict[int, set[str]] = {}
    for _, m in match.iterrows():
        if m["sids"]:
            sids_anio.setdefault(m["anio"], set()).update(m["sids"].split(";"))
    ventanas_anio = {
        anio: storm_index[storm_index["sid"].isin(sids)][["fecha_inicio", "fecha_fin"]]
        for anio, sids in sids_anio.items()
    }

    def _en_ventana_tormenta(ev: pd.Series) -> bool | None:
        ini = pd.to_datetime(ev["fecha_inicio"], errors="coerce")
        fin = pd.to_datetime(ev["fecha_fin"], errors="coerce")
        if pd.isna(ini):
            return None
        ventanas = ventanas_anio.get(int(ev["anio"]))
        if ventanas is None or ventanas.empty:
            return False
        return any(
            _ventanas_solapan(ini, fin, v.fecha_inicio - buffer, v.fecha_fin + buffer)
            for v in ventanas.itertuples()
        )

    exploded, no_localizados = _explotar_estados(universo)

    filas = []
    for (anio, cve_ent), grupo in exploded.groupby(["anio", "cve_ent"]):
        es_cic = grupo["subtipo"].isin(ciclonicos)
        es_flu = grupo["subtipo"].isin(fluviales)
        flags: set[str] = set()

        sids: set[str] = set()
        for eid in grupo.loc[grupo["subtipo"] == "CT", "evento_id"]:
            if sids_por_evento.get(eid):
                sids.update(sids_por_evento[eid].split(";"))
            flags.update(f for f in flags_por_evento.get(eid, "").split(";") if f)

        solapes = [_en_ventana_tormenta(ev) for _, ev in grupo[es_flu].iterrows()]
        if any(s is None for s in solapes):
            flags.add("fecha_faltante")
        solapes_bool = [bool(s) for s in solapes]

        if es_cic.any() and not es_flu.any():
            familia, regla = "ciclonica", "ct_reportado"
        elif es_flu.any() and not es_cic.any():
            if solapes_bool and all(solapes_bool):
                familia, regla = "ciclonica", "lluvia_en_ventana_tormenta"
            elif any(solapes_bool):
                familia, regla = "mixta_flag", "mixto_parcial_ventana"
            else:
                familia, regla = "fluvial", "fluvial_independiente"
        else:
            if solapes_bool and all(solapes_bool):
                familia, regla = "ciclonica", "ct_y_lluvia_en_ventana"
            else:
                familia, regla = "mixta_flag", "mixto"

        filas.append(
            {
                "anio": anio,
                "cve_ent": cve_ent,
                "sids_viento": ";".join(sorted(sids)),
                "sids_cono_lluvia": "",  # v1: requires TCRain (CAL-XWALK-01, OQ-CAL-01)
                "familia_asignada": familia,
                "flag_revision": ";".join(sorted(flags)),
                "regla_aplicada": regla,
                "version_crosswalk": version,
            }
        )

    xwalk = pd.DataFrame(filas).sort_values(["anio", "cve_ent"])
    xwalk = xwalk.reset_index(drop=True)

    resumen = {
        "n_eventos_universo": int(len(universo)),
        "n_eventos_ct": int(len(ct)),
        "match_por_metodo": match["metodo_match"].value_counts().to_dict(),
        "n_anio_estado": int(len(xwalk)),
        "familias": xwalk["familia_asignada"].value_counts().to_dict(),
        "entidades_no_localizadas": no_localizados,
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
    ibtracs_dir = paths.data / "ibtracs" / "crudos"
    eventos = pd.read_csv(eventos_csv, dtype=str, na_filter=False)
    storm_index = load_storm_index(
        ibtracs_dir,
        season_min=int(config["periodo"]["anio_inicial"]),
        bbox=cfg["bbox_mexico"],
    )

    xwalk, match, resumen = build_crosswalk(eventos, storm_index, config)

    out_dir = paths.data / "crosswalk"
    out_dir.mkdir(parents=True, exist_ok=True)
    salida_xwalk = out_dir / "crosswalk_anio_estado_tormentas.csv"
    salida_match = out_dir / "eventos_sid_match.csv"
    xwalk.to_csv(salida_xwalk, index=False)
    match.to_csv(salida_match, index=False)

    insumos = {
        eventos_csv.name: _sha256(eventos_csv),
        **{f.name: _sha256(f) for f in sorted(ibtracs_dir.glob("ibtracs.*.csv"))},
    }
    for salida in (salida_xwalk, salida_match):
        write_provenance(
            salida,
            source="impactcal.target.crosswalk (determinista, v0 lado-pérdidas)",
            insumos=insumos,
            version_crosswalk=cfg["version"],
            regla="CAL-XWALK-01/02 v0: nombre+temporada, fallback ventana de fechas",
        )

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"crosswalk_{cfg['version']}_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Crosswalk v0: determinista (sin RNG); semilla registrada por CAL-GEN-05.",
    ).write(paths.manifests, paths.root)

    print(f"crosswalk: {salida_xwalk}")
    print(f"match eventos: {salida_match}")
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
