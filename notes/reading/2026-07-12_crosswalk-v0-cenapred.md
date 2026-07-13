# Read-log — 2026-07-12 — crosswalk v0 + ingesta congelada CENAPRED/IBTrACS

Session deliverables: `CAL-XWALK-03/04` (crosswalk v0, loss-side), `CAL-TARGET-04` (frozen CENAPRED interface), `OQ-CAL-14` opened. What to read to back or challenge each, with citation keys from [[REFERENCES]].

**[Eberenz2021] §2.2–2.3 (event–country matching against EM-DAT)** — backs `CAL-XWALK-03`: our evento↔SID matching by name+season with date fallback is the state-level analog of their storm↔country-year assignment; read their handling of unmatched and multi-storm cases before deciding the fate of the 68 multi-candidate date matches and the 2 `sin_match` events of 2000.

**[Knapp2010] + IBTrACS v04r01 technical docs (column definitions: `SID`, `NAME`, `TRACK_TYPE`, provisional tracks)** — backs the per-storm index in `impactcal.hazard.ibtracs`: confirm that dropping `spur` entries and collapsing basin-crossers to one `SID` matches the intended v04 semantics, and how numbered depressions are named (relevant to the `ONCE-E` → `ELEVEN-E` translation in `extract_storm_names`).

**CENAPRED source note (climateCCR `notes/sources/cenapred.md` §5–§6bis)** — backs `CAL-TARGET-04` and `OQ-CAL-14`: the two output structures (panel A vs eventos B), the no-splitting principle for multi-state events, and the capture protocol for the 2016+ extensos that must run upstream before the panel covers the full `CAL-TARGET-02` period.

**[GelmanHill2007] (measurement/assignment error discussion)** — challenges `CAL-XWALK-04`: the date-window proxy misclassifies rain events between `ciclonica` and `fluvial`; think of `familia_asignada` v0 as a noisy label whose misclassification rate the v1 rain cone ($P_{\text{acc}}$ above threshold, `CAL-XWALK-01`) will estimate — the 220 `mixta_flag` year-states bound that error from above.

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · Home: [[_INDEX]]
#arm/cal #type/reading
