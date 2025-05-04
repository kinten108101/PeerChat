## Message

A message is a UTF8-encoded string that must satisfy the BNF form below:

```ebnf
message : id ':' body ;
id : [a-z\_]+ ;
body : /* a JSON text */ ;
```

## Examples

Here are some example messages, all are correct with the protocol specification:
- `submit_info:{"stable_port":2000}`
- `get_list:{}`. Notice: the body is an empty dictionary; the body part of the message is not ommitted even when a message doesn't need a body.
