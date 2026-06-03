# True bisect plan (Sordland scene, full corpus)

## Goal

Run **true A/B bisect over 100% of extractable/translatable Sordland TMP text**.
No visibility filter, no hand-picked subset.

## Hard gates

The bisect prep step fails loudly if either gate fails:

1. Extractable unique TMP text from Sordland scene is not fully represented in translation map.
2. Any extractable source has empty final translation target.

If either happens, script exits non-zero and prints concrete missing samples.

## Workflow

1. Prepare full corpus and split A/B:
   - `true_bisect_sordland.py prepare`
   - Generates:
     - `docs/sordland-full-bisect.tsv`
     - `docs/sordland-full-bisect-a.tsv`
     - `docs/sordland-full-bisect-b.tsv`

2. Apply A half:
   - `true_bisect_sordland.py apply --tsv docs/sordland-full-bisect-a.tsv`
   - Test load-game stability.

3. If A crashes: recurse on A.
   If A is stable: apply B and recurse on B only if B crashes.

4. Continue split/test recursively until the offending subset is isolated.

## Notes

- This plan bisects **full-corpus candidates**, not curated subsets.
- Mainmenu/Rizia policy remains unchanged; this script targets Sordland bundle only.
