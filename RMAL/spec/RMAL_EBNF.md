# RMAL 3 Core Grammar

```ebnf
program      = { statement } EOF ;
statement    = module | const_decl | let_decl | function | if_stmt | while_stmt
             | return_stmt | print_stmt | assert_stmt | directive | expr_stmt ;
module       = "MODULE" identifier [";"] ;
const_decl   = ("const" | "CONST") identifier "=" expression [";"] ;
let_decl     = "let" identifier "=" expression [";"] ;
function     = "fn" identifier "(" [ identifier {"," identifier} ] ")" block ;
if_stmt      = "if" expression block ["else" block] ;
while_stmt   = "while" expression block ;
return_stmt  = "return" expression [";"] ;
print_stmt   = "print" expression [";"] ;
assert_stmt  = "assert" expression [";"] ;
block        = "{" { statement } "}" ;
expression   = literals | names | calls | unary | binary ;
directive    = directive_name { token-on-same-line } [";"] ;
directive_name = "EXPORT" | "CONTEXT" | "RELATION" | "PRESERVE" | "ALLOW" | "DENY"
               | "CLAIM" | "EVIDENCE" | "COUNTERPROBE" | "VERIFY" | "CONTINUE"
               | "OBLIGATION" | "INVARIANT" | "REMAINDER" | "SURFACE" | "TRACE" ;
```

Expression precedence, high to low:

1. unary `!`, `-`
2. `*`, `/`, `%`
3. `+`, `-`
4. `<`, `<=`, `>`, `>=`
5. `==`, `!=`
6. `&&`
7. `||`

Legacy RMAL line-oriented directives remain accepted without semicolons.

## Semantic boundary

Executable semantics and evidentiary semantics are distinct.

`PARSE != VALIDATE != EXECUTE != EVIDENCE != ADMIT`
