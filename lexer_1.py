import ply.lex as lex

reserved = {
    'stre': 'KEYWORD_STRE',
    'sikas': 'KEYWORD_SIKAS',
    'while_stre': 'KEYWORD_WHILE_STRE',
    'again_stre': 'KEYWORD_AGAIN_STRE',
    'pasum_stre': 'KEYWORD_PASUM_STRE',
    'jump_stre': 'KEYWORD_JUMP_STRE',
    'por_stre_in': 'KEYWORD_POR_STRE_IN',
    'siks': 'SIKS',
    'fals': 'FALS',
    'nimi': 'NIMI',
    'procers': 'FUNC_PROCERS',
    'multicotomizar': 'FUNC_MULTICOTOMIZAR',
    'contarRachas': 'FUNC_CONTARRACHAS',
    'colectR': 'FUNC_COLECTR',
    'colectavgB': 'FUNC_COLECTAVGB',
    'colectaddT': 'FUNC_COLECTADDT',
    'colectavgM': 'FUNC_COLECTAVGM',
    'int': 'KEYWORD_INT',
    'float': 'KEYWORD_FLOAT',
    'bool': 'KEYWORD_BOOL',
    'cadena': 'KEYWORD_CADENA',
    'colect': 'KEYWORD_COLECT',
    'mtix': 'KEYWORD_MTIX',
    'repeat': 'REPEAT',
    'persist': 'PERSIST',
    'break': 'BREAK',
    'identity': 'IDENTITY',
    'true': 'BOOLEAN',
    'false': 'BOOLEAN',
    'null': 'NULL',
}

tokens = [
    'IDENTIFIER',
    'NUMBER',
    'FLOAT',
    'STRING',

    # Operadores
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'POWER', 'POWER3',
    'RANGE', 'SHIFT_LEFT', 'SHIFT_RIGHT', 'TILDE_ARROW',
    'BREAK_RACHA', 'COMPARE_ID', 'JOIN', 'LENRACHA',

    # Lógicos
    'AND', 'OR', 'NOT',

    # Otros
    'EQUALS',
    'LPAREN', 'RPAREN',
    'LBRACE', 'RBRACE',
    'SEMICOLON', 'COMMA',

    'LINE_COMMENT', 'BLOCK_COMMENT',
] + list(reserved.values())

t_PLUS           = r'\+'
t_MINUS          = r'-'
t_TIMES          = r'\*'
t_DIVIDE         = r'/'
t_MOD            = r'%'
t_EQ             = r'=='
t_NE             = r'!='
t_LT             = r'<'
t_LE             = r'<='
t_GT             = r'>'
t_GE             = r'>='
t_POWER          = r'\^\^'
t_POWER3         = r'\^\^\^'
t_RANGE          = r':->'
t_SHIFT_LEFT     = r'<<<'
t_SHIFT_RIGHT    = r'>>>'
t_TILDE_ARROW    = r'~~>'
t_BREAK_RACHA    = r'!!'
t_COMPARE_ID     = r'\?=\?'
t_JOIN           = r'\&join'
t_LENRACHA       = r'\#stre'

t_AND            = r'yy'
t_OR             = r'oo'
t_NOT            = r'YO'

t_EQUALS         = r'='
t_LPAREN         = r'\('
t_RPAREN         = r'\)'
t_LBRACE         = r'\{\{'
t_RBRACE         = r'\}\}'
t_SEMICOLON      = r';'
t_COMMA          = r','

t_ignore = ' \t\r'

def t_FLOAT(t):
    r'-?\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'-?\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'"[^"\n]*"'
    t.value = t.value[1:-1]
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_LINE_COMMENT(t):
    r'//[^\n]*'
    pass

def t_BLOCK_COMMENT(t):
    r'/\*[^*]*\*/'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()
