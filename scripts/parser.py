from ply import lex, yacc

class Lexer(object):
    def __init__(self):
        self.lexer = lex.lex(module=self)

    tokens = (
        'XXX',
        'HIGHLIGHT',
        'PARAMETER',
        'VALUE',
        'GROUPNAME',
        'COMMENT',
    )

    def t_XXX(self, t):
        r'\s*xxx'
        return t

    def t_HIGHLIGHT(self, t):
        r'\s*hi(g(h(l(i(g(ht?)?)?)?)?)?)?'
        return t

    def t_PARAMETER(self, t):
        r'\s*(c?term|start|stop|cterm[fb]g|gui(fg|bg|sp)?|font)'
        t.value = t.value.strip()
        return t

    def t_VALUE(self, t):
        r'''=(
            [^" \t]+
            |
            "[^"]*"
        )'''
        t.value = t.value[1:]
        if t.value.startswith('"') and t.value.endswith('"'):
            t.value = t.value[1:-1]
        return t

    def t_GROUPNAME(self, t):
        r'\s*[A-Za-z]+'
        return t

    def t_COMMENT(self, t):
        r'\s*".*'
        return t

    def t_error(self, t):
        raise ValueError('Non-tokenizable line (position %d)' % t.lexpos)

def lex_test(data):
    lexer = Lexer()
    lexer.lexer.input(data)
    return list(lexer.lexer)

class HighlightExpr(object):
    def __init__(self, cmd, grpname, params, comment=''):
        self.cmd = cmd
        self.grpname = grpname
        self.params = dict(params)
        self.comment = comment

class HighlightOutput(object):
    def __init__(self, grpname, params):
        self.grpname = grpname
        self.params = dict(params)

class Parser(object):
    def __init__(self):
        self.yacc = yacc.yacc(module=self)

    tokens = Lexer.tokens

    def p_line(self, p):
        '''
        line : hi_expr
             | hi_output
        '''
        p[0] = p[1]

    def p_expr(self, p):
        'hi_expr : HIGHLIGHT GROUPNAME param_list'
        p[0] = HighlightExpr(p[1], p[2], p[3])

    def p_expr_comment(self, p):
        'hi_expr : HIGHLIGHT GROUPNAME param_list COMMENT'
        p[0] = HighlightExpr(p[1], p[2], p[3], p[4])

    def p_output(self, p):
        'hi_output : GROUPNAME XXX param_list'
        p[0] = HighlightOutput(p[1], p[3])

    def p_params(self, p):
        'param_list : PARAMETER VALUE param_list'
        p[0] = [(p[1], p[2])] + p[3]

    def p_params_single(self, p):
        'param_list : PARAMETER VALUE'
        p[0] = [(p[1], p[2])]

    def p_error(self, p):
        raise ValueError('Non-parsable line (position %d)' % p.lexpos)

def parse(data):
    lexer = Lexer()
    lexer.lexer.input(data)
    parser = Parser()
    return parser.yacc.parse(lexer=lexer.lexer)
