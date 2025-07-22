import ply.yacc as yacc
from bigraph_lexer import tokens, lexer

# AST Node classes simplificadas
class BiGraphNode:
    pass

class Control(BiGraphNode):
    def __init__(self, name, arity=0, is_atomic=False):
        self.name = name
        self.arity = arity
        self.is_atomic = is_atomic
    
    def __str__(self):
        atomic_str = "atomic " if self.is_atomic else ""
        return f"{atomic_str}control {self.name} : {self.arity}"

class BiGraph(BiGraphNode):
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
    
    def __str__(self):
        return f"bigraph {self.name} = {self.expression}"

class Reaction(BiGraphNode):
    def __init__(self, name, lhs, rhs):
        self.name = name
        self.lhs = lhs
        self.rhs = rhs
    
    def __str__(self):
        return f"rule {self.name}: {self.lhs} => {self.rhs}"

class Signature(BiGraphNode):
    def __init__(self, controls):
        self.controls = controls
    
    def __str__(self):
        controls_str = ', '.join(map(str, self.controls))
        return f"signature {{ {controls_str} }}"

# Gramática mínima
def p_program(p):
    '''program : statements'''
    p[0] = [s for s in p[1] if s]

def p_statements(p):
    '''statements : statement
                  | statements statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement(p):
    '''statement : control_statement
                | bigraph_statement  
                | signature_statement
                | rule_statement'''
    p[0] = p[1]

def p_control_statement(p):
    '''control_statement : ATOMIC CONTROL IDENTIFIER COLON INTEGER SEMICOLON
                        | CONTROL IDENTIFIER COLON INTEGER SEMICOLON'''
    if len(p) == 7:  # atomic
        p[0] = Control(p[3], int(p[5]), True)
    else:  # normal
        p[0] = Control(p[2], int(p[4]), False)

def p_bigraph_statement(p):
    '''bigraph_statement : BIGRAPH IDENTIFIER ARROW IDENTIFIER SEMICOLON'''
    # "bigraph name => expression;"
    p[0] = BiGraph(p[2], p[4])

def p_signature_statement(p):
    '''signature_statement : SIGNATURE LBRACE signature_items RBRACE'''
    p[0] = Signature(p[3])

def p_signature_items(p):
    '''signature_items : signature_item
                      | signature_items COMMA signature_item'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_signature_item(p):
    '''signature_item : IDENTIFIER COLON INTEGER'''
    p[0] = Control(p[1], int(p[3]))

def p_rule_statement(p):
    '''rule_statement : RULE IDENTIFIER COLON IDENTIFIER ARROW IDENTIFIER SEMICOLON'''
    p[0] = Reaction(p[2], p[4], p[6])

def p_error(p):
    if p:
        print(f"Error de sintaxis en token '{p.value}' ({p.type}) línea {p.lineno}")
    else:
        print("Error: fin de archivo inesperado")

# Crear parser
parser = yacc.yacc(debug=False, write_tables=False)

def parse_bigraph(input_text):
    """Parser principal"""
    try:
        # Preprocesar: eliminar comentarios y líneas vacías
        lines = []
        for line in input_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('//'):
                lines.append(line)
        
        clean_text = ' '.join(lines)
        if not clean_text:
            return []
            
        result = parser.parse(clean_text, lexer=lexer, debug=False)
        return result if result else []
    except Exception as e:
        print(f"Error de parsing: {e}")
        return []

def test_parser():
    """Test del parser mínimo"""
    test_code = '''
    atomic control Person : 1;
    control Room : 2;
    
    signature {
        Person : 1,
        Room : 2
    }
    
    rule move: Person => Room;
    bigraph house => Building;
    '''
    
    print("=== Testing Minimal Bigraph Parser ===")
    ast = parse_bigraph(test_code)
    
    if ast:
        print(f"✓ Parse exitoso! {len(ast)} elementos:")
        for i, node in enumerate(ast):
            print(f"  {i+1}. {node}")
    else:
        print("❌ Parse falló!")

if __name__ == '__main__':
    test_parser()
