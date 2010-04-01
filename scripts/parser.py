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
        return t

    def t_VALUE(self, t):
        r"""=(
            [^' \t]+
            |
            '[^']*'
        )"""
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

class Highlight(object):
    '''Simple object representing a parse result'''
    def __init__(self, grpname, params):
        self.grpname = grpname
        self.params = params

    def text(self, extra_params):
        raise NotImplementedError()

    @staticmethod
    def _format_params(params):
        if isinstance(params, dict):
            params = params.items()

        pieces = []
        for (param, value) in params:
            if ' ' in value or '\t' in value:
                value = "'%s'" % value
            pieces.append('%s=%s' % (param, value))

        return ' '.join(pieces)

class HighlightExpr(Highlight):
    def __init__(self, cmd, grpname, params, comment=''):
        # params has whitespace for original formatting
        formatted = []
        unformatted = {}
        for (param, value) in params:
            formatted.append('%s%s' % (param, value))
            value = value[1:] # remove '='
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            unformatted[param.strip()] = value.strip()
        Highlight.__init__(self, grpname, unformatted)
        self.cmd = cmd
        self.comment = comment
        self._formatted_params = ''.join(formatted)

    def text(self, extra_params):
        extra_str = self._format_params(extra_params)
        if extra_str:
            extra_str = ' ' + extra_str
        return '%s%s%s%s%s' % (self.cmd, self.grpname, self._formatted_params,
                               extra_str, self.comment)

class HighlightOutput(Highlight):
    def __init__(self, grpname, params):
        self.grpname = grpname
        self.params = params

    def text(self, extra_params):
        param_str = self._format_params(self.params)
        extra_str = self._format_params(extra_params)
        if extra_str:
            extra_str = ' ' + extra_str
        return 'hi %s %s%s' % (self.grpname, param_str, extra_str)

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
        pos = 'end' if p is None else p.lexpos
        raise ValueError('Non-parsable line (position %s)' % pos)

def parse(data):
    lexer = Lexer()
    lexer.lexer.input(data)
    parser = Parser()
    return parser.yacc.parse(lexer=lexer.lexer)
