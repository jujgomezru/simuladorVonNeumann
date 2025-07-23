import ply.yacc as yacc
from lexer_1 import tokens
from bigraph import Bigraph, Node

# Globales
global_bigraph = Bigraph()
symbol_table = {}

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('nonassoc', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),
)

def p_program(p):
    'program : instruction_list'
    print("✔ Programa completo.")
    for instr in p[1]:
        if instr and isinstance(instr, str) and instr.strip() and not instr.strip().startswith(";"):
            global_bigraph.add_instruction(instr.strip())
    p[0] = global_bigraph

def p_instruction_list(p):
    '''instruction_list : instruction
                        | instruction instruction_list'''
    if len(p) == 2:
        p[0] = p[1] or []
    else:
        p[0] = (p[1] or []) + (p[2] or [])

def p_instruction(p):
    '''instruction : declaration
                   | assignment
                   | control_flow
                   | racha_process
                   | function_call
                   | comment'''
    p[0] = p[1] or []

def p_declaration(p):
    '''declaration : KEYWORD_STRE tipo IDENTIFIER EQUALS expression SEMICOLON
                   | KEYWORD_STRE tipo IDENTIFIER SEMICOLON'''
    var = p[3]
    if var not in symbol_table:
        reg_id = len(symbol_table)
        symbol_table[var] = reg_id
    else:
        reg_id = symbol_table[var]

    if len(p) == 7:
        print(f"📦 Declaración con valor: {var} = {p[5]}")
        node = Node(f"decl_{var}")
        global_bigraph.add_node(node)
        p[0] = [f"LOADK R{reg_id}, {p[5]}"]
    else:
        print(f"📦 Declaración sin valor: {var}")
        node = Node(f"decl_{var}")
        global_bigraph.add_node(node)
        p[0] = []

def p_tipo(p):
    '''tipo : KEYWORD_INT
            | KEYWORD_FLOAT
            | KEYWORD_BOOL
            | KEYWORD_CADENA
            | KEYWORD_COLECT
            | KEYWORD_MTIX'''
    p[0] = p[1]

def p_assignment(p):
    'assignment : IDENTIFIER EQUALS expression SEMICOLON'
    var = p[1]
    val = p[3]
    print(f"📝 Asignación: {var} = {val}")
    if var not in symbol_table:
        reg_id = len(symbol_table)
        symbol_table[var] = reg_id
    else:
        reg_id = symbol_table[var]
    node = Node(f"assign_{var}")
    global_bigraph.add_node(node)
    p[0] = [f"LOADK R{reg_id}, {val}"]

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MOD expression
                  | expression EQ expression
                  | expression NE expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression'''
    p[0] = f"({p[1]} {p[2]} {p[3]})"

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_value(p):
    '''expression : NUMBER
                  | FLOAT
                  | STRING
                  | BOOLEAN
                  | NULL
                  | IDENTIFIER'''
    p[0] = str(p[1])

def p_control_flow(p):
    'control_flow : KEYWORD_WHILE_STRE LPAREN expression RPAREN LBRACE instruction_list RBRACE'
    print("🔄 Estructura de control reconocida.")
    node = Node("while")
    global_bigraph.add_node(node)
    p[0] = []

def p_racha_process(p):
    '''racha_process : FUNC_PROCERS LPAREN IDENTIFIER RPAREN SEMICOLON
                     | FUNC_COLECTAVGB LPAREN IDENTIFIER RPAREN SEMICOLON'''
    print(f"⚙️ Proceso de racha: {p[1]}")
    node = Node(p[1])
    global_bigraph.add_node(node)
    p[0] = [f"; llamada a {p[1]} con {p[3]}"]

def p_function_call(p):
    'function_call : IDENTIFIER LPAREN RPAREN SEMICOLON'
    print(f"📞 Llamada a función: {p[1]}")
    p[0] = []

def p_comment(p):
    '''comment : LINE_COMMENT
               | BLOCK_COMMENT'''
    p[0] = []

def p_error(p):
    if p:
        print(f"❌ Error de sintaxis en '{p.value}' (línea {p.lineno})")
    else:
        print("❌ Error: fin inesperado del archivo.")

parser = yacc.yacc()
