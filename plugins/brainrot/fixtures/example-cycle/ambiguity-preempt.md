## Ambiguity audit — 30d

### Incidents
| axis | type | count | example (paraphrase) | chats |
|---|---|---|---|---|
| MACHINE | WRONG-GUESS | 2 | assumed laptop; user meant remote box | chat://example-c, chat://example-d |

### Drafted rules
| axis | rule |
|---|---|
| MACHINE | When MACHINE is unspecified, default to the remote dev box; state the chosen default inline in the response; ask only if the action is destructive or irreversible. |
