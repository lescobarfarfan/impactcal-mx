"""GloFAS river-flood footprints on the shared centroids (DC-CAL-HAZ-1, CAL-RF-03).

Second fluvial segment of the panel, computed with the petals `rf_glofas`
pipeline from the frozen GloFAS-ERA5 v4.0 daily discharge (`CAL-RF-03`):

    descarga diaria dis24 -> máximo anual -> periodo de retorno (ajuste Gumbel)
    -> regrid a la malla de mapas JRC -> protección (`none`/`flopros`)
    -> profundidad de inundación por interpolación de los mapas JRC

The annual maximum is taken **before** the return-period step, matching the
annual-maximum resolution of the ISIMIP2a segment (`CAL-RF-01`) and the
año×estado calibration unit (`CAL-TARGET-02`).

Two details that are silent traps and are handled here explicitly:

- GloFAS-ERA5 NetCDFs carry longitude in the **0-360** convention; the Gumbel
  fit and JRC maps use -180..180. Converted before anything else.
- The 30 arcsec JRC flood grid is exactly 5x finer than the 150 arcsec LitPop
  centroids (`CAL-EXP-04`), so each centroid cell holds 25 flood cells. They
  are aggregated the way ISIMIP2a reports its pair: `intensity` = mean depth
  over the **wet** subcells, `fraction` = wet subcells / total subcells. Cells
  with no JRC map coverage (not a floodplain) count as dry.

Both protection variants are frozen while `OQ-CAL-16` is open. Writes
`data/hazard/haz_rf_glofas_{none,flopros}.h5` + `_procedencia.json` + manifest.
Idempotent: an artifact that verifies is skipped (`--forzar` to regenerate).

CLI (run inside the CLIMADA env)::

    python -m impactcal.hazard.rf_glofas [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np

from impactcal.hazard.glofas import _dest_name
from impactcal.hazard.tc import load_shared_centroids
from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

# petals expone la variante sin protección y la protegida como dos variables
VARIABLE_POR_PROTECCION = {"none": "flood_depth", "flopros": "flood_depth_flopros"}

_FUENTE_RF_GLOFAS = (
    "Inundación fluvial petals rf_glofas sobre centroides LitPop congelados, descarga "
    "GloFAS-ERA5 v4.0 (EWDS) + ajuste Gumbel 1979-2023 (ETH) + mapas JRC "
    "[Harrigan2020][Dottori2016-ref?][Scussolini2016-ref?]"
)


def annual_max_discharge(nc_paths: dict[int, Path]):
    """Annual maximum dis24 per year, longitudes normalized to -180..180."""
    import xarray as xr

    por_anio = []
    for anio, path in sorted(nc_paths.items()):
        with xr.open_dataset(path) as ds:
            da = ds["dis24"]
            da = da.assign_coords(longitude=(((da.longitude + 180) % 360) - 180))
            da = da.sortby("longitude")
            amax = da.max("valid_time").expand_dims(year=[anio]).rename("dis24")
            por_anio.append(amax.drop_vars([c for c in ("surface",) if c in amax.coords]).load())
    return xr.concat(por_anio, dim="year")


def bbox_desde_area(area: list[float]) -> dict[str, float]:
    """`glofas.area` viene como [N, W, S, E] (convención CDS/EWDS)."""
    norte, oeste, sur, este = area
    return {"lat_min": sur, "lat_max": norte, "lon_min": oeste, "lon_max": este}


def crop_flood_maps(flood_maps, bbox: dict[str, float]):
    """Crop the global JRC maps to the hazard bbox (the regrid target stops being global)."""
    desc = bool(flood_maps.latitude[0] > flood_maps.latitude[-1])
    lat_sl = (
        slice(bbox["lat_max"], bbox["lat_min"]) if desc else slice(bbox["lat_min"], bbox["lat_max"])
    )
    return flood_maps.sel(latitude=lat_sl, longitude=slice(bbox["lon_min"], bbox["lon_max"]))


def to_centroid_grid(depth, lat_cent: np.ndarray, lon_cent: np.ndarray, res_deg: float):
    """Aggregate a fine flood-depth grid onto the coarse centroid cells.

    Returns `(intensity, fraction)`, both `(n_anios, n_centroides)`: mean depth
    over wet subcells, and wet-subcell share of each centroid cell.
    """
    lat_f = depth["latitude"].values
    lon_f = depth["longitude"].values
    # índice de celda-centroide de cada celda fina (redondeo al centro más cercano)
    lat0, lon0 = lat_cent.min(), lon_cent.min()
    i_f = np.rint((lat_f - lat0) / res_deg).astype(np.int64)
    j_f = np.rint((lon_f - lon0) / res_deg).astype(np.int64)
    i_c = np.rint((lat_cent - lat0) / res_deg).astype(np.int64)
    j_c = np.rint((lon_cent - lon0) / res_deg).astype(np.int64)

    # tabla de búsqueda (i, j) -> índice de centroide; -1 = fuera de la exposición
    n_i = int(max(i_f.max(), i_c.max())) + 1
    n_j = int(max(j_f.max(), j_c.max())) + 1
    tabla = np.full((n_i, n_j), -1, dtype=np.int64)
    dentro = (i_c >= 0) & (j_c >= 0)
    tabla[i_c[dentro], j_c[dentro]] = np.flatnonzero(dentro)
    i_ok = (i_f >= 0) & (i_f < n_i)
    j_ok = (j_f >= 0) & (j_f < n_j)
    idx = np.full((lat_f.size, lon_f.size), -1, dtype=np.int64)
    idx[np.ix_(i_ok, j_ok)] = tabla[np.ix_(i_f[i_ok], j_f[j_ok])]
    idx = idx.ravel()
    valido = idx >= 0
    idx_v = idx[valido]

    n_cent = lat_cent.size
    intensidad = np.zeros((depth.sizes["year"], n_cent), dtype=np.float32)
    fraccion = np.zeros_like(intensidad)
    total = np.bincount(idx_v, minlength=n_cent).astype(np.float32)
    total[total == 0] = np.nan  # centroide sin celdas finas: queda seco, sin dividir por cero

    for k in range(depth.sizes["year"]):
        plano = np.nan_to_num(depth.isel(year=k).values.ravel()[valido], nan=0.0)
        mojada = plano > 0
        suma = np.bincount(idx_v, weights=plano, minlength=n_cent)
        n_mojadas = np.bincount(idx_v, weights=mojada.astype(np.float64), minlength=n_cent)
        with np.errstate(invalid="ignore", divide="ignore"):
            intensidad[k] = np.where(n_mojadas > 0, suma / np.maximum(n_mojadas, 1), 0.0)
            fraccion[k] = np.nan_to_num(n_mojadas / total, nan=0.0)
    return intensidad, fraccion


def build_hazard(intensidad: np.ndarray, fraccion: np.ndarray, anios: list[int], cent):
    """CLIMADA `Hazard` (haz_type 'RF') with one event per panel year."""
    from climada.hazard import Hazard
    from scipy import sparse

    return Hazard(
        haz_type="RF",
        units="m",
        centroids=cent,
        event_id=np.arange(1, len(anios) + 1),
        event_name=[str(a) for a in anios],
        date=np.array([dt.date(a, 12, 31).toordinal() for a in anios]),
        orig=np.ones(len(anios), dtype=bool),
        # sin significado aquí (eventos anuales observados), igual que el segmento ISIMIP2a
        frequency=np.ones(len(anios)) / len(anios),
        intensity=sparse.csr_matrix(intensidad),
        fraction=sparse.csr_matrix(fraccion),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="regenera aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    cfg = config["glofas"]
    out_dir = paths.data / "hazard"
    salidas = {p: out_dir / f"haz_rf_glofas_{p}.h5" for p in VARIABLE_POR_PROTECCION}
    pendientes = {
        prot: ruta for prot, ruta in salidas.items() if args.forzar or not verify_provenance(ruta)
    }
    if not pendientes:
        print(f"intactos (usa --forzar para regenerar): {', '.join(map(str, salidas.values()))}")
        return 0

    crudos_dir = paths.data / "glofas" / "crudos"
    aux_dir = paths.data / "glofas" / "auxiliares"
    nc_paths = {}
    for anio in cfg["anios"]:
        p = crudos_dir / _dest_name(anio, cfg)
        if not verify_provenance(p):
            raise RuntimeError(f"Descarga GloFAS ausente o sin procedencia (CAL-GEN-12): {p}")
        nc_paths[anio] = p
    for aux in ("flood-maps.nc", "gumbel-fit.nc"):
        if not verify_provenance(aux_dir / aux):
            raise RuntimeError(f"Insumo estático rf_glofas corrupto: {aux_dir / aux}")

    res_as = int(config["exposure"]["resolucion_arcsec"])
    exp_path = paths.data / "exposures" / f"litpop_mex_{res_as}as.hdf5"
    cent = load_shared_centroids(exp_path)
    res_deg = res_as / 3600.0

    from importlib.metadata import version

    from climada_petals.hazard.rf_glofas.river_flood_computation import RiverFloodInundation

    anios = sorted(nc_paths)
    rf = RiverFloodInundation(data_dir=aux_dir, cache_dir=paths.root / "results" / ".rf_cache")
    rf.flood_maps = crop_flood_maps(rf.flood_maps, bbox_desde_area(cfg["area"]))

    # Año por año: la malla fina (≈8.7M celdas × 2 variantes) nunca se acumula, sólo su
    # reducción a centroides. Con 24 años, hacerlo de golpe pediría ~1.7 GB de rejilla viva.
    por_prot: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {p: [] for p in pendientes}
    for anio in anios:
        descarga = annual_max_discharge({anio: nc_paths[anio]})
        profundidad = rf.compute(discharge=descarga, apply_protection="both").compute()
        for prot in pendientes:
            var = VARIABLE_POR_PROTECCION[prot]
            por_prot[prot].append(to_centroid_grid(profundidad[var], cent.lat, cent.lon, res_deg))
        print(f"  {anio}: profundidad calculada")

    out_dir.mkdir(parents=True, exist_ok=True)
    for prot, salida in pendientes.items():
        intensidad = np.vstack([i for i, _ in por_prot[prot]])
        fraccion = np.vstack([f for _, f in por_prot[prot]])
        haz = build_hazard(intensidad, fraccion, anios, cent)
        haz.write_hdf5(str(salida))
        write_provenance(
            salida,
            source=_FUENTE_RF_GLOFAS,
            modelo=(
                "dis24 GloFAS-ERA5 v4.0 -> máximo anual -> periodo de retorno (Gumbel 1979-2023) "
                "-> regrid a mapas JRC -> profundidad interpolada"
            ),
            unidades="m (intensity) + fracción inundada (fraction)",
            proteccion=prot,
            anios=f"{anios[0]}-{anios[-1]}",
            n_eventos=len(anios),
            n_centroides=int(cent.size),
            n_centroides_con_agua=int((intensidad > 0).any(axis=0).sum()),
            agregacion=(
                f"malla JRC 30as -> centroides {res_as}as: intensity = profundidad media de "
                "subceldas mojadas, fraction = subceldas mojadas / subceldas totales"
            ),
            nota_frecuencia="frequency sin significado aquí: eventos anuales observados",
            descargas_sha256={p.name: _sha256(p) for p in nc_paths.values()},
            gumbel_sha256=_sha256(aux_dir / "gumbel-fit.nc"),
            flood_maps_sha256=_sha256(aux_dir / "flood-maps.nc"),
            centroides_archivo=exp_path.name,
            centroides_sha256=_sha256(exp_path),
            climada_version=version("climada"),
            climada_petals_version=version("climada-petals"),
        )
        print(
            f"hazard fluvial GloFAS ({prot}): {salida} "
            f"({len(anios)} años, {int((intensidad > 0).any(axis=0).sum())} centroides con agua)"
        )

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"haz_rf_glofas_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Huellas fluviales GloFAS: deterministas (sin RNG); semilla por CAL-GEN-05.",
    ).write(paths.manifests, paths.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
