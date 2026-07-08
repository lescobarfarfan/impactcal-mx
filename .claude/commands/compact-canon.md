Periodic canon compaction (00_README_CONTEXT.md §4e). With my confirmation at each step:

1. Read all `context/*.md`; list duplications, stale/superseded lines still marked live, contradictions, IDs out of order.
2. Propose a deduplicated reorganization per file (promote-don't-duplicate; superseded history kept only if load-bearing).
3. Verify every decision still has a reference key or `[eng]`; every `[ref?]` is tracked in `OQ-CAL-08`; every `DC-*` status tag is current.
4. Run the link-check pass over the canon.
5. Apply diffs file by file after confirmation; update "Last compaction" in `00_README_CONTEXT.md`; single commit `canon: compaction YYYY-MM-DD`.
