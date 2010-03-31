from ply import lex, yacc

class Lexer(object):
    def __init__(self):
        self.lexer = lex.lex(module=self)

    # PLY stuff
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
        r'\s*c?term|start|stop|cterm[fb]g|gui(fg|bg|sp)?|font'
        return t

    def t_VALUE(self, t):
        r'''=(
            [^" \t]+
            |
            "[^"]*"
        )'''
        return t

    def t_GROUPNAME(self, t):
        r'\s*[A-Za-z]+'
        return t

    def t_COMMENT(self, t):
        r'\s*".*'
        return t

def lex_test(data):
    lexer = Lexer()
    lexer.lexer.input(data)
    return list(lexer.lexer)
