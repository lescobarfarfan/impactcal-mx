# Read-log — 2026-07-18 · Inspección genérica de datos QA (`CAL-GEN-14`)

**Leys, C., Ley, C., Klein, O., Bernard, P., & Licata, L. (2013), *Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median*, Journal of Experimental Social Psychology 49(4) — todo el artículo (es corto); en particular la constante de consistencia y los umbrales recomendados.** Why: backs the core flagging rule of `impactcal.inspeccion` (`CAL-GEN-14`): $z = 0.6745\,(x - \tilde{x})/\mathrm{MAD}$, flag on $|z| > u$; they recommend conservative cutoffs (2.24–3) for inference-cleaning while we run $u=5$ for gross-error hunting — the gap is deliberate and worth citing when documenting the threshold. `[Leys2013-ref?]` — verify DOI/pages before manuscript (`OQ-CAL-08`).

**Hampel filter framing (via the references of Leys 2013; Hampel 1974 is the origin).** Why: the per-group-over-time check in `impactcal.inspeccion._check_panel` is a Hampel-type decision filter applied to aggregated año×grupo panels; the original framing also explains the near-constant-series pathology (MAD → 0 makes trivial deviations explode) that we patched with the relative scale floor (`rel_floor = 0.01`). No citation key yet — only add one if the manuscript discusses the filter genealogy.

**ydata-profiling documentation (docs.profiling.ydata.ai) + Great Expectations documentation — capability scan, not deep reading.** Why: `CAL-GEN-14` deliberately builds a thin custom layer instead of adopting these tools: per-column HTML profiles and declared-rule validation cover neither per-group temporal outliers nor derived-ratio unit-error checks — the two detectors that caught Maíz dulce Sinaloa 2015 and its ×1000 sibling cluster in the CNSF consolidados. The optional `--perfil` hook keeps ydata-profiling as a complement (and it stays uninstalled in the working envs: its pins would bump numpy/pandas/scipy/matplotlib).

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · Home: [[_INDEX]]
#arm/cal #type/reading
