# Current Status (Working):
- declaration of simple tuples (test/tuples1.while)
- access of tuples via # operator (test/tuples4.while)
- variables (SymExp) inside TupleExpressions (test/tuples3.while)

# What is not working
- nested tuples cannot be parsed yet (test/tuples2.while) -> fix "parse_tuple_type()" in parser.py to correctly track location
- tuple assignment of already declared tuples (test/tuples5.while)-> either extend "parse_assign_stmt()" to also include "parse_tuple_expr()" or extend "parse_expr()" to also handle tuples (in parse.py)

# Good to have
- comma counter to check whether the number of elements in a tuple matches the number of commas (and there is at least one comma per tuple)