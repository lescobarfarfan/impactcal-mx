Audit the Obsidian vault (context/, notes/, literature/, root hubs):

1. Broken wikilinks: every `[[target]]` must resolve to an existing basename.
2. Orphans: every note reachable from `[[_INDEX]]` or `[[CAL_MOC]]`.
3. Footers: every note ends with `## Related` (+ `Home: [[_INDEX]]`) and carries `#arm/cal` + one `#type/*` tag.
4. MOC coverage: every `notes/**/*.md` linked from `[[CAL_MOC]]`.
Report findings as a checklist; propose minimal diffs; apply only after I confirm.
