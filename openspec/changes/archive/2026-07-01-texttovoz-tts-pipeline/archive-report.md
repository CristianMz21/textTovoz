# Archive Report: texttovoz-tts-pipeline

**Archived at**: 2026-07-01T05:52:51-05:00
**Change**: `texttovoz-tts-pipeline`
**Final status**: OK
**Verify report**: [`verify-report.md`](verify-report.md)
**Pull request**: PR opened on `feat/texttovoz-tts-pipeline` against `main`.

## Summary

The `texttovoz-tts-pipeline` SDD change completed planning, implementation, verification, and archive readiness checks. Verification status is OK/PASS WITH WARNINGS, with no CRITICAL issues. All implementation task checkboxes are complete in `tasks.md`.

## Specs Synced

| Domain | Action | Details |
|---|---|---|
| `tts-pipeline` | Created canonical spec | Synced full delta spec from `openspec/changes/texttovoz-tts-pipeline/specs/tts-pipeline/spec.md` to `openspec/specs/tts-pipeline/spec.md`. |

## Artifacts Archived

- `explore.md`
- `proposal.md`
- `specs/tts-pipeline/spec.md`
- `design.md`
- `tasks.md`
- `apply-progress.md`
- `verify-report.md`
- `archive-report.md`

## Verification Snapshot

- Status: OK
- Verdict: PASS WITH WARNINGS
- Critical issues: 0
- Tasks complete: 25/25 implementation tasks reported complete in verify; status contract reported all task checkboxes complete.
- Quality gates: `ruff check .`, `ruff format --check .`, full pytest, smoke pytest, validator help/docs-path checks, coverage sanity, suppression scan, and notebook JSON validation passed.

## Follow-up Items

Warnings and suggestions from verification remain non-blocking follow-up work:

- Coverage target is still missed for several modules: `audio_io.py`, `config.py`, `ingest.py`, and `normalize.py`.
- Some required scenarios remain untested: ingest rejection, manifest collision refusal, slice regeneration, reproducible bytes, Colab cold-start/GPU fit, and future consent hook behavior.
- spaCy remains optional in the verified implementation and is not proven with real `es_core_news_sm` installation/runtime locally.
- Consent gate deferred hook is not represented in code for a future cloning path.
- Add focused tests for validation branches, audio I/O branches, manifest edge cases, ingest failures, manifest collision, and slice regeneration.
- Clarify whether spaCy is primary in Colab or update spec/design wording to make regex fallback the primary verified MVP path.
- Reconcile historical OpenSpec design lines that still mention `output/manifest.jsonl` as the manifest validator path.

## Archive Notes

OpenSpec archive policy was followed: task completion gate passed, delta spec sync completed before archive move, and no CRITICAL verification issues were present.
