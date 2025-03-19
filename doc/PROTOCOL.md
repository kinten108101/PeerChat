## Message

A message is a UTF8-encoded string that must satisfy the BNF form below:

```ebnf
message : id ':' body ;
id : [a-z\_]+ ;
body : /* a JSON text */ ;
```
