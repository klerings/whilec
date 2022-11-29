# Current Status (Working):
- declaration of simple tuples works (test/tuples1.while);
- main issue is the env variable for the eval of Declared Tuple Variables -> we need to add our tupleExor.expr to env at some point
- also consider: when looking up variables from env, use deepcopies

# What is not working
- nested tuples cannot be parsed yet (test/tuples2.while) -> fix "parse_tuple_type()" in parser.py to correctly track location
- nested tuple expressions (test/tuples2.while) -> fix "parse_tuple_expr()" in parser.py to parse nested tuple expressions
- variables (SymExp) inside TupleExpressions are not possible yet (test/tuples3.while), because they have to be evaluated first, in order to check if they have the correct type, but it's unclear how to do the evaluation because it requires a runtime environment with already defined variables, where to get this environment? -> fix "check()" in while_ast.py

# What is not implemented yet
- tuple access via # (parsing of #), see exercise sheet (test/tuples4.while)
- tuple assignment of already declared tuples (test/tuples5.while)-> either extend "parse_assign_stmt()" to also include "parse_tuple_expr()" or extend "parse_expr()" to also handle tuples (in parse.py)

# Good to have
- comma counter to check whether the number of elements in a tuple matches the number of commas (and there is at least one comma per tuple)