Format: all format messages follow this format

```bnf
log: header ':' ' ' message;
header: domain | domain '/' portnum;
domain: STRING;
message: STRING;
```

All log will be saved to `/var/[id]` where id is defined per application tier:
- If tier is back-end, id is port number
- If tier is front-end, id is `gui-session-[sessionid]`
