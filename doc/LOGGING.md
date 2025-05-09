Format: all format messages follow this format

```bnf
log: '[' timestamp ']' ' ' header ':' ' ' message;
timestamp: /* locale time format */;
header: domain | domain '/' portnum;
domain: STRING;
message: STRING;
```

All log will be saved to `/var/node_agent-[id]` where id is defined per application tier:
- If tier is front-end, id is `gui-session-[sessionid]`
