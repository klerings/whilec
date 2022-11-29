"""
Parses a stream of tokens generated by the lexer.
"""

from enum import IntEnum, auto

from while_ast import Prog,                                 \
    DeclStmt, AssignStmt, StmtList, WhileStmt,              \
    IfStmt, IfElseStmt,                                     \
    BinExpr, UnaryExpr, BoolExpr, LitExpr, SymExpr, ErrExpr,\
    TupleExpr, TupleType, BaseType
from lexer import Lexer
from tok import Tag, Tok
from loc import Loc
from err import err

class Prec(IntEnum):
    BOT   = auto()
    OR    = auto()
    AND   = auto()
    NOT   = auto()
    REL   = auto()
    ADD   = auto()
    MUL   = auto()
    UNARY = auto()

class Parser:
    def __init__(self, file):
        self.lexer = Lexer(file)
        self.ahead = self.lexer.lex()
        self.prev  = None

        self.prec = {
            Tag.K_OR : [Prec.OR , Prec.AND],
            Tag.K_AND: [Prec.AND, Prec.NOT],
            Tag.T_EQ : [Prec.REL, Prec.ADD],
            Tag.T_NE : [Prec.REL, Prec.ADD],
            Tag.T_LT : [Prec.REL, Prec.ADD],
            Tag.T_LE : [Prec.REL, Prec.ADD],
            Tag.T_GT : [Prec.REL, Prec.ADD],
            Tag.T_GE : [Prec.REL, Prec.ADD],
            Tag.T_ADD: [Prec.ADD, Prec.MUL],
            Tag.T_SUB: [Prec.ADD, Prec.MUL],
            Tag.T_MUL: [Prec.MUL, Prec.UNARY],
            Tag.T_SELECT: [Prec.ADD, Prec.MUL],
        }

    # helpers to track loc

    class Tracker:
        def __init__(self, begin, parser):
            self.begin  = begin
            self.parser = parser

        def loc(self):
            return Loc(self.parser.ahead.loc.file, self.begin, self.parser.prev)

    def track(self):
        return self.Tracker(self.ahead.loc.begin, self)

    # helpers get next Tok from Lexer

    def lex(self):
        result     = self.ahead
        self.prev  = result.loc.begin
        self.ahead = self.lexer.lex()
        return result

    def accept(self, tag):
        return self.lex() if self.ahead.isa(tag) else None

    def eat(self, tag):
        assert self.ahead.isa(tag)
        return self.lex()

    def err(self, expected = None, got = None, ctxt = None):
        if ctxt is None:
            self.err(expected, self.ahead, got)
        else:
            err(got.loc, f"expected {expected}, got '{got}' while parsing {ctxt}")

    def expect(self, tag, ctxt):
        if self.ahead.isa(tag): return self.lex()
        self.err(f"'{tag}'", ctxt)
        return None

    # entry

    def parse_prog(self):
        t    = self.track()
        stmt = self.parse_stmt()
        self.expect(Tag.K_RETURN, "program")
        ret  = self.parse_expr("return expression")
        self.expect(Tag.T_SEMICOLON, "at the end of the final return of the program")
        self.expect(Tag.M_EOF, "at the end of the program")
        return Prog(t.loc(), stmt, ret)

    def parse_sym(self, ctxt=None):
        if (tok := self.accept(Tag.M_SYM)) is not None: return tok
        if ctxt is not None:
            self.err("identifier", ctxt)
            return Tok(self.ahead.loc, "<error>")
        return None

    # Stmt

    def parse_stmt(self):
        t     = self.track()
        stmts = []

        while True:
            while self.accept(Tag.T_SEMICOLON):
                pass

            if self.ahead.isa(Tag.K_INT) or self.ahead.isa(Tag.K_BOOL) or self.ahead.isa(Tag.D_PAREN_L):
                stmts.append(self.parse_decl_stmt())
            elif self.ahead.isa(Tag.M_SYM):
                stmts.append(self.parse_assign_stmt())
            elif self.ahead.isa(Tag.K_WHILE):
                stmts.append(self.parse_while_stmt())
            elif self.ahead.isa(Tag.K_IF):
                stmts.append(self.parse_if_else_stmt())
            else:
                break

        return StmtList(t.loc(), stmts)

    def parse_assign_stmt(self):
        t    = self.track()
        sym  = self.eat(Tag.M_SYM)
        self.expect(Tag.T_ASSIGN, "assignment statement")
        expr = self.parse_expr("right-hand side of an assignment statement")
        self.expect(Tag.T_SEMICOLON, "end of an assignment statement")
        return AssignStmt(t.loc(), sym, expr)

    def parse_decl_stmt(self):
        t    = self.track()
        is_tuple = False
        
        # TUPLE declaration
        if self.ahead.isa(Tag.D_PAREN_L):
            is_tuple = True  
            left_par = self.lex().tag          
            ty = self.parse_tuple_type(t)
            print(f'ty: {ty}')
                
        # BASE TYPE declaration
        else:
            next_token   = self.lex()
            ty = BaseType(next_token.loc, next_token.tag)

        sym  = self.parse_sym("identifier of a declaration statement")
        self.expect(Tag.T_ASSIGN, "declaration statement")
        if is_tuple:
            expr = self.parse_tuple_expr("right-hand side of tuple declaration statement")
        else:
            expr = self.parse_expr("right-hand side of basetype declaration statement")
        self.expect(Tag.T_SEMICOLON, "end of a declaration statement")
        return DeclStmt(t.loc(), ty, sym, expr)

    def parse_while_stmt(self):
        t    = self.track()
        self.eat(Tag.K_WHILE)
        cond = self.parse_expr("condition of a while statement")
        self.expect(Tag.D_BRACE_L, "while statement")
        body = self.parse_stmt()
        self.expect(Tag.D_BRACE_R, "while statement")
        return WhileStmt(t.loc(), cond, body)

    def parse_if_else_stmt(self):
        t    = self.track()
        self.eat(Tag.K_IF)
        cond = self.parse_expr("condition of an if statement")
        self.expect(Tag.D_BRACE_L, "if statement")
        body = self.parse_stmt()
        self.expect(Tag.D_BRACE_R, "if statement")
        if not self.ahead.isa(Tag.K_ELSE):
            return IfStmt(t.loc(), cond, body)
        else:
            self.eat(Tag.K_ELSE)
            self.expect(Tag.D_BRACE_L, "else statement")
            alt_body = self.parse_stmt()
            self.expect(Tag.D_BRACE_R, "else statement")
            return IfElseStmt(t.loc(), cond, body, alt_body)

    # Expr

    def parse_expr(self, ctxt = None, cur_prec = Prec.BOT):
        t   = self.track()
        lhs = self.parse_primary_or_unary_expr(ctxt)

        while self.ahead.is_bin_op():
            (l_prec, r_prec) = self.prec[self.ahead.tag]
            if l_prec < cur_prec:
                break
            op  = self.lex().tag
            rhs = self.parse_expr("right-hand side of operator '{op}'", r_prec)
            lhs = BinExpr(t.loc(), lhs, op, rhs)

        return lhs

    def parse_primary_or_unary_expr(self, ctxt):
        t = self.track()
        
        if (tok := self.accept(Tag.K_FALSE)) is not None: return BoolExpr(tok.loc, False  )
        if (tok := self.accept(Tag.K_TRUE )) is not None: return BoolExpr(tok.loc, True   )
        if (tok := self.accept(Tag.M_SYM  )) is not None: return SymExpr (tok.loc, tok    )
        if (tok := self.accept(Tag.M_LIT  )) is not None: return LitExpr (tok.loc, tok.val)
        
        if self.ahead.tag.is_unary():
            op  = self.lex().tag
            rhs = self.parse_expr("unary expression", Prec.NOT if op is Tag.K_NOT else Prec.UNARY)
            return UnaryExpr(t.loc(), op, rhs)

        if self.accept(Tag.D_PAREN_L):
            expr = self.parse_expr()
            self.expect(Tag.D_PAREN_R, "parenthesized expression")
            return expr 

        if ctxt is not None:
            self.err("primary or unary expression", ctxt)
            return ErrExpr(self.ahead.loc)
        assert False

    def parse_tuple_type(self, t, types_in_tuple=[]):
        """parses the left side of tuple declarations to find the tupletype, can be used recursively"""
        #t    = self.track()
        print(f'function call parse-tuple-expr with {types_in_tuple}')
        #comma_count = 0
        next_token = self.lex()
        while not next_token.isa(Tag.D_PAREN_R):
            print(f'next token before check: {next_token} ({t.loc()})')
            if next_token.is_type():
                types_in_tuple.append(BaseType(next_token.loc, next_token.tag))
            elif next_token.isa(Tag.D_PAREN_L):
                types_in_tuple.append(self.parse_tuple_type(t, types_in_tuple))
            print(f'next token after check: {next_token} ({next_token.isa(Tag.D_PAREN_R)}) ({t.loc()})')
            next_token = self.lex()
        ty = TupleType(loc=t.loc(), type=types_in_tuple)
        print(f'function returns {ty}')
        return ty

    def parse_tuple_expr(self, ctxt):
        """parses the right side of tuple declarations or assignments, can be used recursively for tuples in tuples"""
        t = self.track()

        exprs = []
        comma_count = 0
        next_token = self.lex()
        while not self.ahead.isa(Tag.D_PAREN_R):
            expr = self.parse_expr()
            exprs.append(expr)
            if (tok := self.accept(Tag.T_COMMA)) is not None:
                comma_count += 1
        
        if (len(exprs) == 1 and comma_count == 1) or (len(exprs) > 1 and len(exprs) == comma_count + 1):
            self.expect(Tag.D_PAREN_R, "tuple expression")
            return TupleExpr(t.loc(), exprs)
        elif len(exprs) > 1 and len(exprs) == comma_count:
            # todo raise error
            print("error: number of expressions doesnt match number of commas")
        else:
            self.expect(Tag.D_PAREN_R, "parenthesized expression")
            return exprs[0]
