# REPO_STRUCTURE — impactcal-mx

```
impactcal-mx/
├── CLAUDE.md                 # Claude Code instructions (read each session)
├── README.md                 # project map + setup
├── OBSIDIAN_SETUP.md         # vault conventions
├── _INDEX.md                 # vault home note
├── CAL_MOC.md                # the hub (map of content)
├── context/                  # THE CANON (single source of truth)
├── notes/
│   ├── theory/               # master design doc + theory notes
│   ├── reading/              # session read-logs (YYYY-MM-DD_slug.md)
│   └── pipelines/            # per-pipeline working notes
├── literature/               # papers, refs.bib
├── src/impactcal/
│   ├── infra/                # ✅ built: seeds, paths, manifests, provenance
│   ├── hazard/               # frozen CLIMADA hazards (TC, surge, rain, RF)
│   ├── exposure/             # LitPop + sumas-aseguradas disaggregation
│   ├── target/               # loss tables, INPC deflation, crosswalk
│   ├── calibrate/            # null model (climada.util.calibrate) + surfaces
│   ├── bayes/                # PyMC hierarchical model (+ Stan replication)
│   └── combine/              # multi-peril union-of-damage aggregation
├── configs/calibracion.yaml  # all parameters (CAL-GEN-06)
├── tests/                    # pytest; infra layer covered
├── data/                     # git-ignored; <fuente>/{crudos,consolidados}; or IMPACTCAL_DATA_ROOT
└── results/manifests/        # run manifests (tracked dir, ignored contents)
```

Wiring: `target` + `hazard` + `exposure` → `calibrate` (surfaces) → `bayes` (posteriors) →
`combine` enters inside the surface computation for the joint multi-peril likelihood → canonical
export per `DC-CAL-OUT-1`.

## Related
[[README]] · [[00_README_CONTEXT]] · Home: [[_INDEX]]
#arm/cal #type/workflow
