import ply.lex as lex

tokens = [
    'MNEMONIC','REGISTER','HEX','DEC','LABEL','IDENT',
    'COMMA','LBRACKET','RBRACKET','NEWLINE'
]

# Ignorar espacios, tabs y retornos de carro
t_ignore  = ' \t\r'

# Ignorar BOM en archivos UTF-8
def t_BOM(t):
    r'\ufeff'
    pass

t_COMMA   = r','

t_LBRACKET = r'\['

t_RBRACKET = r'\]'

def t_HEX(t):
    r'0x[0-9A-Fa-f]+'
    t.value = int(t.value,16); return t

def t_DEC(t):
    r'\d+'
    t.value = int(t.value); return t

def t_REGISTER(t):
    r'R\d+'
    t.value = int(t.value[1:]); return t

def t_LABEL(t):
    r'[A-Za-z_]\w*:'
    t.value = t.value[:-1]; return t

def t_MNEMONIC(t):
    r'[A-Za-z]+'
    t.type = 'MNEMONIC'; t.value = t.value.upper(); return t

def t_COMMENT(t):
    r';.*'; pass

def t_NEWLINE(t):
    r'\n+'; t.lexer.lineno += len(t.value); return t

def t_error(t):
    print(f"Lexical error: {t.value[0]}"); t.lexer.skip(1)

lexer = lex.lex()