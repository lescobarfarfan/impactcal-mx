"""Revisión de calidad — CNSF agrícola (emisión + siniestros), toda la base 2008-2024.

Generaliza el hallazgo Maíz dulce/Sinaloa/2015 (error de magnitud ×1000 en superficies,
`scraps/cnsf_outliers_corn_sinaloa/`) a un barrido sistemático de los consolidados CNSF del
ramo agrícola (repo hermano climateCCR). NO modifica los datos: produce un inventario
itemizado de hallazgos y una propuesta de corrección renglón a renglón, para decisión manual.

Salidas (junto al script; idempotente):
  - hallazgos_agricola.csv            un renglón por (chequeo, celda año×entidad×cultivo)
  - renglones_correccion_propuesta.csv  renglones del crudo con corrección ÷1000 propuesta
  - resumen_hallazgos.md              reporte agrupado por chequeo, con conteos y ejemplos

Uso: python revision_calidad_agricola.py
"""

import unicodedata
from pathlib import Path

import pandas as pd

DATA_DIR = Path(
    "/Users/lescobarfarfan/Documents/projects/Thesis_MScQF/climateCCR/"
    "data/hazard_mx/datos_CNSF/consolidados/agricola_y_animales"
)
OUT = Path(__file__).resolve().parent

SUP_EM = "SUPERFICIE ASEGURADA\n(HECTÁREAS)"
SUP_SI = "SUPERFICIE SINIESTRADA\n(HECTÁREAS)"

BANDA_MXN_HA = (1_000, 200_000)  # valor asegurado implícito plausible (MXN/ha, moneda Nacional)
BANDA_SIN_MXN_HA = (50, 500_000)  # monto ocurrido/pagado implícito por ha siniestrada
MIN_SUP_HA = 10  # SESA reporta superficies <1 ha como "1"; bajo 10 ha el implícito es ruido
Z_ROBUSTA_UMBRAL = 8  # salto interanual atípico (leave-one-out, mediana/MAD)
MIN_ANIOS_SERIE = 6

# Áreas estatales (ha): Marco Geoestadístico congelado del repo (00ent.shp → EPSG:6372).
# Cota física dura: la superficie asegurada de UN cultivo no puede exceder el territorio.
AREA_ESTATAL_HA = {
    "AGUASCALIENTES": 555_867,
    "BAJA CALIFORNIA": 7_340_616,
    "BAJA CALIFORNIA SUR": 7_140_714,
    "CAMPECHE": 5_726_983,
    "CHIAPAS": 7_361_736,
    "CHIHUAHUA": 24_697_336,
    "CIUDAD DE MEXICO": 147_706,
    "COAHUILA": 15_067_122,
    "COLIMA": 575_412,
    "DURANGO": 12_213_120,
    "GUANAJUATO": 3_033_977,
    "GUERRERO": 6_357_194,
    "HIDALGO": 2_065_455,
    "JALISCO": 7_796_977,
    "MEXICO": 2_222_685,
    "MICHOACAN": 5_830_145,
    "MORELOS": 486_854,
    "NAYARIT": 2_782_501,
    "NUEVO LEON": 6_355_885,
    "OAXACA": 9_396_766,
    "PUEBLA": 3_415_267,
    "QUERETARO": 1_158_927,
    "QUINTANA ROO": 4_457_237,
    "SAN LUIS POTOSI": 6_049_996,
    "SINALOA": 5_681_563,
    "SONORA": 18_063_384,
    "TABASCO": 2_470_124,
    "TAMAULIPAS": 7_944_717,
    "TLAXCALA": 397_339,
    "VERACRUZ": 7_146_742,
    "YUCATAN": 3_942_365,
    "ZACATECAS": 7_447_971,
}
ALIAS_ENTIDAD = {"DISTRITO FEDERAL": "CIUDAD DE MEXICO", "ESTADO DE MEXICO": "MEXICO"}
NO_ESTADO = {"EN EL EXTRANJERO", "EXTRANJERO"}


def _ascii_upper(s: pd.Series) -> pd.Series:
    def fold(x: str) -> str:
        return (
            unicodedata.normalize("NFKD", str(x).strip()).encode("ascii", "ignore").decode().upper()
        )

    return s.map(fold)


def canon_entidad(s: pd.Series) -> pd.Series:
    n = _ascii_upper(s)
    return n.map(lambda x: ALIAS_ENTIDAD.get(x, x))


def cargar(nombre: str, col_tipo: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / f"{nombre}.csv", encoding="utf-8-sig", low_memory=False)
    df["fila_csv"] = df.index  # índice 0-based en el consolidado, para trazar correcciones
    df["TIPO_N"] = _ascii_upper(df[col_tipo].fillna(""))
    df["ENT_N"] = canon_entidad(df["ENTIDAD"])
    df["CUL_N"] = _ascii_upper(df["CULTIVO"].fillna(""))
    return df


hallazgos: list[dict] = []


def flag(chequeo, severidad, ambito, accion, detalle, anio="", entidad="", cultivo="", valor=""):
    hallazgos.append(
        {
            "chequeo": chequeo,
            "severidad": severidad,
            "ambito": ambito,
            "anio": anio,
            "entidad": entidad,
            "cultivo": cultivo,
            "valor": valor,
            "detalle": detalle,
            "accion_propuesta": accion,
        }
    )


def variantes_categoricas(df: pd.DataFrame, cols: list[str], ambito: str) -> None:
    """A1: valores que colapsan al normalizar (espacios/mayúsculas/acentos) fragmentan series."""
    for col in cols:
        s = df[col].dropna().astype(str)
        grupos = s.groupby(_ascii_upper(s)).unique()
        for norm, vals in grupos.items():
            if len(vals) > 1:
                conteos = s.value_counts()[list(vals)].to_dict()
                flag(
                    "A1_variantes_categoricas",
                    "media",
                    ambito,
                    "normalizar",
                    f"{col}: {conteos} colapsan a '{norm}'",
                    valor=len(vals),
                )


def barrido_estructural(em: pd.DataFrame, si: pd.DataFrame) -> None:
    variantes_categoricas(
        em,
        ["ENTIDAD", "TIPO SEGURO", "MONEDA", "CICLO DE CULTIVO", "ESQUEMA DE ASEGURAMIENTO"],
        "emision",
    )
    variantes_categoricas(
        si,
        ["ENTIDAD", "TIPO DE SEGURO", "MONEDA", "CICLO DE CULTIVO", "CAUSA DEL SINIESTRO"],
        "siniestros",
    )

    for df, ambito, monto in (
        (em, "emision", "SUMA ASEGURADA"),
        (si, "siniestros", "MONTO PAGADO"),
    ):
        ext = df[df["ENT_N"].isin(NO_ESTADO)]
        if len(ext):
            flag(
                "A2_entidad_no_estatal",
                "media",
                ambito,
                "excluir_de_vistas_estatales",
                f"{len(ext)} renglones ENTIDAD∈{sorted(ext['ENTIDAD'].unique())}, "
                f"{monto}={ext[monto].sum():,.0f}",
                valor=len(ext),
            )
        sin_ent = df[~df["ENT_N"].isin(NO_ESTADO) & ~df["ENT_N"].isin(AREA_ESTATAL_HA)]
        if len(sin_ent):
            flag(
                "A2_entidad_no_reconocida",
                "alta",
                ambito,
                "revisar",
                f"valores: {sorted(sin_ent['ENTIDAD'].unique())}",
                valor=len(sin_ent),
            )

    for df, ambito, monto in (
        (em, "emision", "SUMA ASEGURADA"),
        (si, "siniestros", "MONTO PAGADO"),
    ):
        mon = _ascii_upper(df["MONEDA"].fillna(""))
        no_nac = df[mon != "NACIONAL"]
        if len(no_nac):
            por_anio = (
                no_nac.groupby("anio")[monto].sum() / df.groupby("anio")[monto].sum() * 100
            ).round(1)
            peores = por_anio.nlargest(3).to_dict()
            flag(
                "A3_moneda_no_nacional",
                "alta",
                ambito,
                "separar_moneda",
                f"{len(no_nac)} renglones MONEDA≠Nacional ({sorted(no_nac['MONEDA'].unique())}); "
                f"% de {monto} por año, peores: {peores}",
                valor=len(no_nac),
            )

    num_em = ["NÚMERO DE PÓLIZAS", SUP_EM, "PRIMA EMITIDA", "SUMA ASEGURADA"]
    num_si = ["NÚMERO DE SINIESTROS", SUP_SI, "MONTO DEL SINIESTRO OCURRIDO", "MONTO PAGADO"]
    for df, ambito, cols in ((em, "emision", num_em), (si, "siniestros", num_si)):
        for col in cols:
            neg = df[pd.to_numeric(df[col], errors="coerce") < 0]
            if len(neg):
                flag(
                    "A4_valores_negativos",
                    "baja",
                    ambito,
                    "revisar",
                    f"{col}: {len(neg)} renglones, suma={neg[col].sum():,.0f} "
                    f"(años {sorted(neg['anio'].unique())})",
                    valor=len(neg),
                )
        dup = df.drop(columns=["fila_csv"]).duplicated().sum()
        if dup:
            flag(
                "A5_renglones_duplicados",
                "media",
                ambito,
                "revisar",
                f"{dup} renglones idénticos (posible doble carga)",
                valor=int(dup),
            )

    sup0 = em[(em[SUP_EM] == 0) & (em["SUMA ASEGURADA"] > 0)]
    flag(
        "A6_superficie_cero_con_suma",
        "baja",
        "emision",
        "revisar",
        f"{len(sup0)} renglones agrícolas con superficie 0 y SUMA ASEGURADA>0 "
        f"(pólizas no por-hectárea o superficie faltante); distorsionan MXN/ha",
        valor=len(sup0),
    )


def celda(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.groupby(["anio", "ENT_N", "CUL_N"])[cols].sum().reset_index()


def barrido_magnitud(em: pd.DataFrame, si: pd.DataFrame) -> pd.DataFrame:
    """B: imposibilidad física, valor implícito, consistencia cruzada, saltos atípicos."""
    cel_em = celda(em, [SUP_EM, "SUMA ASEGURADA", "PRIMA EMITIDA"])
    cel_si = celda(si, [SUP_SI, "MONTO DEL SINIESTRO OCURRIDO", "MONTO PAGADO"])

    # B1 — superficie > territorio estatal (cota dura, Marco Geoestadístico)
    for cel, sup, ambito in ((cel_em, SUP_EM, "emision"), (cel_si, SUP_SI, "siniestros")):
        area = cel["ENT_N"].map(AREA_ESTATAL_HA)
        imp = cel[cel[sup] > area]
        for _, r in imp.iterrows():
            flag(
                "B1_superficie_mayor_al_estado",
                "critica",
                ambito,
                "corregir_o_excluir",
                f"{sup.splitlines()[0]}={r[sup]:,.0f} ha > territorio "
                f"{AREA_ESTATAL_HA[r['ENT_N']]:,.0f} ha",
                r["anio"],
                r["ENT_N"],
                r["CUL_N"],
                round(r[sup]),
            )

    # B2 — valor asegurado implícito fuera de banda (solo moneda Nacional)
    em_nac = em[_ascii_upper(em["MONEDA"].fillna("")) == "NACIONAL"]
    cel_nac = celda(em_nac, [SUP_EM, "SUMA ASEGURADA"])
    ok = cel_nac[SUP_EM] >= MIN_SUP_HA
    impl = cel_nac["SUMA ASEGURADA"] / cel_nac[SUP_EM]
    bajo = cel_nac[ok & (impl < BANDA_MXN_HA[0]) & (impl > 0)]
    alto = cel_nac[ok & (impl > BANDA_MXN_HA[1])]
    for _, r in bajo.iterrows():
        v = r["SUMA ASEGURADA"] / r[SUP_EM]
        div1000 = BANDA_MXN_HA[0] <= v * 1000 <= BANDA_MXN_HA[1]
        flag(
            "B2_valor_implicito_bajo",
            "critica" if div1000 else "alta",
            "emision",
            "corregir_div1000" if div1000 else "revisar",
            f"{v:,.0f} MXN/ha (sup {r[SUP_EM]:,.0f} ha); ÷1000 daría {v * 1000:,.0f} MXN/ha"
            + (" → dentro de banda" if div1000 else ""),
            r["anio"],
            r["ENT_N"],
            r["CUL_N"],
            round(v),
        )
    for _, r in alto.iterrows():
        v = r["SUMA ASEGURADA"] / r[SUP_EM]
        # p95 empírico ≈ 468k MXN/ha: 200k-1M puede ser cultivo de alto valor legítimo
        flag(
            "B2_valor_implicito_alto",
            "alta" if v > 1_000_000 else "media",
            "emision",
            "revisar",
            f"{v:,.0f} MXN/ha (sup {r[SUP_EM]:,.0f} ha; suma {r['SUMA ASEGURADA']:,.0f}): "
            "posible sub-reporte de superficie o suma inflada",
            r["anio"],
            r["ENT_N"],
            r["CUL_N"],
            round(v),
        )

    # B3 — siniestrada > asegurada (validación SESA violada a nivel celda). Cautela: una póliza
    # emitida en t-1 (ciclo Otoño-Invierno) puede siniestrarse en t, así que no es imposible
    # estrictamente; se separa el caso sin emisión correspondiente y se gradúa por ratio.
    j = cel_si.merge(cel_em, on=["anio", "ENT_N", "CUL_N"], how="left")
    b3 = j[(j[SUP_SI] > j[SUP_EM].fillna(0) * 1.001) & (j[SUP_SI] >= MIN_SUP_HA)]
    for _, r in b3.iterrows():
        aseg = 0 if pd.isna(r[SUP_EM]) else r[SUP_EM]
        if aseg == 0:
            flag(
                "B3b_siniestro_sin_emision",
                "media",
                "ambos",
                "revisar",
                f"siniestrada {r[SUP_SI]:,.0f} ha sin emisión ese año (¿ciclo previo o etiqueta "
                "de cultivo distinta entre archivos?)",
                r["anio"],
                r["ENT_N"],
                r["CUL_N"],
                round(r[SUP_SI]),
            )
        else:
            ratio = r[SUP_SI] / aseg
            flag(
                "B3_siniestrada_mayor_asegurada",
                "alta" if ratio >= 2 else "media",
                "ambos",
                "revisar",
                f"siniestrada {r[SUP_SI]:,.0f} ha > asegurada {aseg:,.0f} ha (ratio {ratio:,.1f})",
                r["anio"],
                r["ENT_N"],
                r["CUL_N"],
                round(r[SUP_SI]),
            )

    # B4 — monto pagado > suma asegurada (celda, moneda Nacional)
    si_nac = si[_ascii_upper(si["MONEDA"].fillna("")) == "NACIONAL"]
    j2 = celda(si_nac, ["MONTO PAGADO"]).merge(
        celda(em_nac, ["SUMA ASEGURADA"]), on=["anio", "ENT_N", "CUL_N"], how="left"
    )
    b4 = j2[j2["MONTO PAGADO"] > j2["SUMA ASEGURADA"].fillna(0) * 1.001]
    for _, r in b4.iterrows():
        flag(
            "B4_pagado_mayor_suma",
            "media",
            "ambos",
            "revisar",
            f"pagado {r['MONTO PAGADO']:,.0f} > suma asegurada "
            f"{0 if pd.isna(r['SUMA ASEGURADA']) else r['SUMA ASEGURADA']:,.0f}",
            r["anio"],
            r["ENT_N"],
            r["CUL_N"],
            round(r["MONTO PAGADO"]),
        )

    # B5 — salto interanual atípico en superficie (leave-one-out, mediana/MAD, escala natural)
    ya = {
        (h["anio"], h["entidad"], h["cultivo"])
        for h in hallazgos
        if h["chequeo"].startswith(("B1", "B2"))
    }
    for (ent, cul), g in cel_em.groupby(["ENT_N", "CUL_N"]):
        s = g.set_index("anio")[SUP_EM]
        if len(s) < MIN_ANIOS_SERIE:
            continue
        for anio, x in s.items():
            if x < 1000:
                continue
            resto = s.drop(index=anio)
            mad = (resto - resto.median()).abs().median()
            if not mad:
                continue
            z = 0.6745 * (x - resto.median()) / mad
            if z >= Z_ROBUSTA_UMBRAL and (anio, ent, cul) not in ya:
                flag(
                    "B5_salto_superficie_atipico",
                    "media",
                    "emision",
                    "revisar",
                    f"sup {x:,.0f} ha vs mediana resto {resto.median():,.0f} ha (z≈{z:,.0f})",
                    anio,
                    ent,
                    cul,
                    round(x),
                )
    return cel_em


def propuesta_renglones(em: pd.DataFrame, si: pd.DataFrame) -> pd.DataFrame:
    """Renglones del crudo cuya superficie ÷1000 devuelve el implícito a banda plausible."""
    props = []
    # renglones ya corregidos por limpieza_cnsf (consolidados *_corregida.csv): no re-proponer
    for df in (em, si):
        if "dq_correccion" in df.columns:
            df.drop(df.index[df["dq_correccion"].fillna("") != ""], inplace=True)
    em_n = em[_ascii_upper(em["MONEDA"].fillna("")) == "NACIONAL"]
    sup, monto = em_n[SUP_EM], em_n["SUMA ASEGURADA"]
    v = monto / sup.where(sup > 0)
    cand = em_n[(sup >= MIN_SUP_HA * 100) & (v > 0) & (v < BANDA_MXN_HA[0] / 10)]
    for _, r in cand.iterrows():
        antes = r["SUMA ASEGURADA"] / r[SUP_EM]
        if BANDA_MXN_HA[0] <= antes * 1000 <= BANDA_MXN_HA[1]:
            props.append(
                {
                    "archivo": "emision",
                    "fila_csv": r["fila_csv"],
                    "anio": r["anio"],
                    "entidad": r["ENT_N"],
                    "cultivo": r["CUL_N"],
                    "archivo_origen": r["archivo_origen"],
                    "campo": SUP_EM.splitlines()[0],
                    "valor_actual": r[SUP_EM],
                    "valor_propuesto": r[SUP_EM] / 1000,
                    "mxn_ha_antes": round(antes, 1),
                    "mxn_ha_despues": round(antes * 1000),
                }
            )
    # Siniestros: mismo criterio con el monto ocurrido (o pagado) por ha siniestrada
    si_n = si[_ascii_upper(si["MONEDA"].fillna("")) == "NACIONAL"]
    sup_s = si_n[SUP_SI]
    num = si_n[["MONTO DEL SINIESTRO OCURRIDO", "MONTO PAGADO"]].max(axis=1)
    v_s = num / sup_s.where(sup_s > 0)
    cand_s = si_n[(sup_s >= MIN_SUP_HA * 100) & (v_s > 0) & (v_s < BANDA_SIN_MXN_HA[0])]
    for _, r in cand_s.iterrows():
        antes = max(r["MONTO DEL SINIESTRO OCURRIDO"], r["MONTO PAGADO"]) / r[SUP_SI]
        if antes * 1000 >= BANDA_SIN_MXN_HA[0]:
            props.append(
                {
                    "archivo": "siniestros",
                    "fila_csv": r["fila_csv"],
                    "anio": r["anio"],
                    "entidad": r["ENT_N"],
                    "cultivo": r["CUL_N"],
                    "archivo_origen": r["archivo_origen"],
                    "campo": SUP_SI.splitlines()[0],
                    "valor_actual": r[SUP_SI],
                    "valor_propuesto": r[SUP_SI] / 1000,
                    "mxn_ha_antes": round(antes, 2),
                    "mxn_ha_despues": round(antes * 1000),
                }
            )
    return pd.DataFrame(props)


def escribir_resumen(hz: pd.DataFrame, props: pd.DataFrame) -> str:
    orden_sev = {"critica": 0, "alta": 1, "media": 2, "baja": 3}
    lineas = [
        "# Revisión de calidad — CNSF agrícola (emisión + siniestros, 2008-2024)",
        "",
        "Barrido sistemático de los consolidados; generaliza el hallazgo Maíz dulce/Sinaloa/2015.",
        "**Estado 2026-07-18: correcciones aprobadas y APLICADAS en climateCCR** — 915 renglones",
        "(÷1000 superficies y ÷FIX sumas 2022-2024) vía `limpieza_cnsf.py` §6 +",
        "`corregir_consolidados_agricola.py`, en copia (`*_corregida.csv` + `_correcciones_dq.csv`);",
        "caveat completo en `referencias_riesgo_catastrofico.md` §4 (v0.19) y",
        "`detalle_suma_inflada_2022_2024.md` §4. Este reporte describe los consolidados CRUDOS.",
        f"Consolidados leídos de `{DATA_DIR}`.",
        "",
        f"**Total hallazgos: {len(hz)}** · propuestas de corrección ÷1000 a nivel renglón: "
        f"{len(props)} (`renglones_correccion_propuesta.csv`)",
        "",
        "| chequeo | severidad | n | acción propuesta |",
        "|---|---|---|---|",
    ]
    resumen = (
        hz.groupby(["chequeo", "severidad", "accion_propuesta"], as_index=False)
        .size()
        .sort_values(["severidad", "chequeo"], key=lambda c: c.map(orden_sev).fillna(c))
    )
    for _, r in resumen.iterrows():
        lineas.append(
            f"| {r['chequeo']} | {r['severidad']} | {r['size']} | {r['accion_propuesta']} |"
        )
    lineas.append("")

    for chequeo, g in hz.groupby("chequeo", sort=True):
        lineas += [f"## {chequeo} — {len(g)} hallazgos", ""]
        cols = ["anio", "entidad", "cultivo", "valor", "detalle", "accion_propuesta"]
        top = g.sort_values(
            "valor", ascending=False, key=lambda c: pd.to_numeric(c, errors="coerce")
        )
        lineas += ["```", top[cols].head(15).to_string(index=False), "```"]
        if len(g) > 15:
            lineas.append(f"(+{len(g) - 15} más en `hallazgos_agricola.csv`)")
        lineas.append("")
    return "\n".join(lineas)


def main() -> None:
    em = cargar("emision", "TIPO SEGURO")
    si = cargar("siniestros", "TIPO DE SEGURO")
    em_ag = em[em["TIPO_N"] == "AGRICOLA"].copy()
    si_ag = si[si["TIPO_N"] == "AGRICOLA"].copy()
    print(f"emision agrícola: {len(em_ag)} renglones | siniestros agrícola: {len(si_ag)}")

    barrido_estructural(em_ag, si_ag)
    barrido_magnitud(em_ag, si_ag)
    props = propuesta_renglones(em_ag, si_ag)

    hz = pd.DataFrame(hallazgos)
    hz.to_csv(OUT / "hallazgos_agricola.csv", index=False)
    props.to_csv(OUT / "renglones_correccion_propuesta.csv", index=False)
    (OUT / "resumen_hallazgos.md").write_text(escribir_resumen(hz, props), encoding="utf-8")
    print(f"{len(hz)} hallazgos, {len(props)} correcciones propuestas → {OUT}")


if __name__ == "__main__":
    main()
