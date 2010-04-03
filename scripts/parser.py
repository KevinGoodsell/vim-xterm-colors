import re

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
        r'\s*(cterm[fb]g|c?term|start|stop|gui(fg|bg|sp)?|font)'
        return t

    def t_VALUE(self, t):
        r"""=(
            [^' \t]+
            |
            '[^']*'
        )"""
        return t

    def t_GROUPNAME(self, t):
        r'\s*[A-Za-z0-9]+'
        return t

    def t_COMMENT(self, t):
        r'\s*".*|\s+' # also handles trailing whitespace
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
        self.params = {}
        for (param, value) in params:
            value = value[1:] # remove '='
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            self.params[param.strip()] = value.strip()

    def formatted(self):
        raise NotImplementedError()

    def format_params(self, params):
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
        Highlight.__init__(self, grpname.strip(), params)

        # Save original formatting
        formatted = [cmd, grpname]
        for (param, value) in params:
            formatted.append('%s%s' % (param, value))

        self._formatted_head = ''.join(formatted)
        self._formatted_tail = comment

    def formatted(self):
        return FormattedHighlight(self._formatted_head, self._formatted_tail)

class HighlightOutput(Highlight):
    def __init__(self, grpname, params):
        Highlight.__init__(self, grpname, params)

    def formatted(self):
        head = 'hi %s %s' % (self.grpname, self.format_params(self.params))
        return FormattedHighlight(head, '')

class FormattedHighlight(object):
    def __init__(self, head, tail):
        self._head = head
        self._tail = tail

    def _fix_value(self, value):
        # Quote value if necessary
        if ' ' in value:
            return "'%s'" % value
        return value

    _attr_matcher = re.compile(r'''
        (?P<attr>cterm[fb]g|c?term|start|stop|gui(fg|bg|sp)?|font)
        =
        (?P<value>[^' \t]+|'[^']*')
    ''', re.VERBOSE)

    def _replace(self, attrs, match):
        attr = match.group('attr')
        if attr in attrs:
            # There's a replacement attr for this one
            value = attrs[attr]
            result = '%s=%s' % (attr, self._fix_value(value))
            # Used this attr, so remove it
            attrs.pop(attr)
        else:
            # No replacement, keep as-is
            result = match.group()

        return result

    def text(self, new_attrs):
        attrs = dict(new_attrs)
        repl = lambda m: self._replace(attrs, m)
        head = self._attr_matcher.sub(repl, self._head)
        # Use the remaining attrs for middle.
        middle = []
        for (attr, value) in attrs.items():
            middle.append('%s=%s' % (attr, self._fix_value(value)))
        middle = ' '.join(middle)
        if middle:
            middle = ' ' + middle

        return '%s%s%s' % (head, middle, self._tail)

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
