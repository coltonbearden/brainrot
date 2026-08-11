# Claim Audit — 2026-08-01
Coverage: 30d · 41 chats · FULL

## Incidents
| id | asserted claim | correction | domain | root cause | chat |
|---|---|---|---|---|---|
| 1 | said CLI flag --fast exists | user: no such flag | API/FLAG | STALE-TRAINING | example thread A (chat://example-a) |
| 2 | quoted old default port | user: changed last release | VERSION | STALE-TRAINING | example thread B (chat://example-b) |

## Prevention rules (memory-paste-ready)
Verify flags, defaults, and versions against current docs before asserting them.
