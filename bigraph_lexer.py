import ply.lex as lex
from dataclasses import dataclass

def t_ignore_COMMENT_LINE(t):
    r'//.*'
    t.lexer.lineno += 1
    # simplemente descartamos el token
    pass

 # Comentarios de bloque: /* ... */
def t_ignore_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass


"""
TOKENS NO UTILIZADOS ACTUALMENTE EN EL PARSER:
==============================================
Los siguientes tokens están definidos en el lexer pero no se usan en las reglas 
de gramática del parser actual. Están preparados para futuras extensiones:

OPERADORES DE BIGRAFOS:
- BIND          (@)   - bind a nombre
- CLOSURE       (/)   - closure de nombres  
- COMPOSE       (|)   - composición paralela
- CONTAIN       (<-)  - containment
- DARROW        (<=>) - flecha doble
- DOT           (.)   - punto/composición secuencial
- MERGE         (+)   - merge de interfaces
- RELEASE       (->)  - release from container
- SEQUENCE      (.)   - composición secuencial
- SHARE         (&)   - compartir enlace
- TENSOR        (*)   - producto tensorial
- UNLINK        (!)   - desenlace
- EQUALS        (=)   - igualdad

CONSTRUCTORES Y ELEMENTOS:
- EDGE          - edge (arista)
- HOLE          - hole (agujero)
- IDLE          - idle (bigrafo vacío)
- LINK          (~)   - enlace/binding
- NODE          - node (nodo)
- PORT          - port (puerto)
- ROOT          - root (raíz)
- SITE          - site (sitio)

CUANTIFICADORES Y MODALIDADES:
- EXISTS        - exists (cuantificador existencial)
- FORALL        - forall (cuantificador universal)
- GLOBAL        - global (alcance global)
- LOCAL         - local (alcance local)
- MOBILE        - mobile (elemento móvil)
- STATIC        - static (elemento estático)

DELIMITADORES:
- LANGLE        (<)   - ángulo izquierdo
- LBRACKET      ([)   - corchete izquierdo  
- RANGLE        (>)   - ángulo derecho
- RBRACKET      (])   - corchete derecho

ESTRUCTURAS DE CONTROL:
- NEST          (<<)  - anidamiento
- REACTION      - reaction (reacción)
- THEN          - then (entonces)
- UNNEST        (>>)  - des-anidamiento
- WHEN          - when (cuando)
- WHERE         - where (donde)

TIPOS DE DATOS:
- FLOAT         - números flotantes
- STRING        - cadenas de texto

OTROS:
- NEWLINE       - saltos de línea

TOTAL: 41 tokens no utilizados actualmente
Los tokens actualmente EN USO son: IDENTIFIER, INTEGER, ATOMIC, CONTROL, 
SIGNATURE, RULE, BIGRAPH, LPAREN, RPAREN, LBRACE, RBRACE, COMMA, SEMICOLON, 
COLON, ARROW
"""

@dataclass
class Token:
    type: str
    value: any
    lineno: int
    column: int
    lexpos: int
    text: str

def find_column(input_text, lexpos):
    last_cr = input_text.rfind('\n', 0, lexpos)
    return lexpos - last_cr

# Tokens para el lenguaje de bigrafos
tokens = [
    # Identificadores y literales
    'IDENTIFIER', 'INTEGER', 'FLOAT', 'STRING',
    
    # Operadores de bigrafos
    'COMPOSE',      # |  (composición paralela)
    'TENSOR',       # *  (producto tensorial)
    'SEQUENCE',     # .  (composición secuencial)
    'MERGE',        # +  (merge de interfaces)
    'CLOSURE',      # /  (closure de nombres)
    
    # Operadores de lugar (place graph)
    'NEST',         # <<  (anidamiento)
    'UNNEST',       # >>  (des-anidamiento)
    'CONTAIN',      # <-  (containment)
    'RELEASE',      # ->  (release from container)
    
    # Operadores de enlace (link graph)
    'LINK',         # ~   (enlace/binding)
    'UNLINK',       # !   (desenlace)
    'SHARE',        # &   (compartir enlace)
    'BIND',         # @   (bind a nombre)
    'EQUALS',       # =   (igualdad)
    
    # Constructores de bigrafos
    'NODE',         # node
    'SITE',         # site
    'ROOT',         # root
    'HOLE',         # hole
    'PORT',         # port
    'EDGE',         # edge
    'IDLE',         # idle (bigrafo vacío)
    
    # Definiciones y control
    'ATOMIC',       # atomic
    'CONTROL',      # control
    'SIGNATURE',    # signature
    'REACTION',     # reaction
    'RULE',         # rule
    'BIGRAPH',      # bigraph
    'WHEN',         # when
    'THEN',         # then
    'WHERE',        # where
    'WITH',         # with
    'LINKS',        # links
    
    # Cuantificadores y modalidades
    'FORALL',       # forall
    'EXISTS',       # exists
    'LOCAL',        # local
    'GLOBAL',       # global
    'MOBILE',       # mobile
    'STATIC',       # static
    
    # Delimitadores
    'LPAREN', 'RPAREN',         # ( )
    'LBRACE', 'RBRACE',         # { }
    'LBRACKET', 'RBRACKET',     # [ ]
    'LANGLE', 'RANGLE',         # < >
    
    # Separadores
    'COMMA', 'SEMICOLON', 'COLON', 'DOT',
    'NEWLINE', 'ARROW', 'DARROW',
    
    # Comentarios y espacios en blanco (ignorados)
]

# Palabras reservadas
reserved = {
    'node': 'NODE',
    'site': 'SITE', 
    'root': 'ROOT',
    'hole': 'HOLE',
    'port': 'PORT',
    'edge': 'EDGE',
    'idle': 'IDLE',
    'atomic': 'ATOMIC',
    'control': 'CONTROL',
    'signature': 'SIGNATURE',
    'reaction': 'REACTION',
    'rule': 'RULE',
    'bigraph': 'BIGRAPH',
    'when': 'WHEN',
    'then': 'THEN',
    'where': 'WHERE',
    'forall': 'FORALL',
    'exists': 'EXISTS',
    'local': 'LOCAL',
    'global': 'GLOBAL',
    'mobile': 'MOBILE',
    'static': 'STATIC',
    'with': 'WITH',
    'links': 'LINKS'
}

# Ignorar espacios, tabs y retornos de carro
t_ignore = ' \t\r'

# Ignorar BOM en archivos UTF-8
def t_BOM(t):
    r'\ufeff'
    pass

# Operadores de bigrafos
t_COMPOSE = r'\|'
t_TENSOR = r'\*'
t_SEQUENCE = r'\.'
t_MERGE = r'\+'
t_CLOSURE = r'/'

# Operadores de lugar
t_NEST = r'<<'
t_UNNEST = r'>>'
t_CONTAIN = r'<-'
t_RELEASE = r'->'

# Operadores de enlace
t_LINK = r'~'
t_UNLINK = r'!'
t_SHARE = r'&'
t_BIND = r'@'
t_EQUALS = r'='

# Delimitadores
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LANGLE = r'<'
t_RANGLE = r'>'

# Separadores
t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_ARROW = r'=>'
t_DARROW = r'<=>'

# Números flotantes (antes que enteros)
def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

# Números enteros
def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Cadenas de texto
def t_STRING(t):
    r'"([^"\\]|\\.)*"'
    t.value = t.value[1:-1]  # Remover comillas
    return t

# Identificadores (debe ir después de las palabras reservadas)
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# Saltos de línea
def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# Manejo de errores
def t_error(t):
    print(f"Bigraph lexical error at line {t.lexer.lineno}: illegal character '{t.value[0]}'")
    t.lexer.skip(1)
class WrappedLexer:
    def __init__(self, ply_lexer):
        self.lexer = ply_lexer
        self.text = ''

    def input(self, text):
        self.text = text
        self.lexer.input(text)

    def token(self):
        ply_tok = self.lexer.token()
        if not ply_tok:
            return None
        col = find_column(self.text, ply_tok.lexpos)
        lines = self.text.split('\n')
        idx = ply_tok.lineno - 1
        text_line = lines[idx] if 0 <= idx < len(lines) else ''
        # construimos el Token propio
        return Token(
            type=ply_tok.type,
            value=ply_tok.value,
            lineno=ply_tok.lineno,
            column=col,
            lexpos=ply_tok.lexpos,
            text=text_line
        )

# Crear el lexer
_ply_lexer = lex.lex()
lexer = WrappedLexer(_ply_lexer)

# Función de utilidad para testing
def test_lexer(input_text):
    lexer.input(input_text)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok: break
        tokens.append(tok)
    return tokens

# Ejemplo de uso y testing
if __name__ == '__main__':
    # Ejemplo de código de bigrafos
    sample_code = '''
    // Definición de un control atómico
    atomic control Person : 2;
    atomic control Room : 1;
    
    // Definición de un bigrafo simple
    signature {
        Person : 2,
        Room : 1,
        Building : 0
    };
    
    // Regla de reacción: persona entra en habitación  
    rule enter_room:
        Person | Room -> Room(Person);
    
    // Bigrafo inicial
    bigraph house -> Building(Room(Person) | Room);
    '''
    
    print("=== Testing Bigraph Lexer ===")
    tokens = test_lexer(sample_code)
    
    for tok in tokens:
        print(f"Line {tok.lineno:2}: {tok.type:12} -> {tok.value}")
