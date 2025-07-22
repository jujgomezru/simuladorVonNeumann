import ply.yacc as yacc
from bigraph_lexer import tokens, lexer

# AST Node classes simplificadas
class BiGraphNode:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []
    
    def add_child(self, node):
        self.children.append(node)
    
    def __repr__(self):
        if self.children:
            return f"{self.name}: [{', '.join(map(str, self.children))}]"
        return self.name

class Control(BiGraphNode):
    def __init__(self, name, arity=0, is_atomic=False):
        super().__init__(name=name)
        self.arity = arity
        self.is_atomic = is_atomic
    def __repr__(self):
        atomic_str = "atomic " if self.is_atomic else ""
        return f"{atomic_str}control {self.name} : {self.arity}"

class BiGraph(BiGraphNode):
    def __init__(self, name, place_graph, links=None):
        super().__init__(name=name)
        self.place_graph = place_graph
        self.links       = links or []
    def __repr__(self):
        return f"Bigraph {self.name}: places={self.place_graph}, links={self.links}"


class Reaction(BiGraphNode):
    def __init__(self, name, lhs, rhs):
        super().__init__(name=name)
        self.name = name
        self.lhs = lhs
        self.rhs = rhs
    
    def __repr__(self):
        return f"rule {self.name}: {self.lhs} => {self.rhs}"

class Signature(BiGraphNode):
    def __init__(self, controls):
        super().__init__(name="signature")
        self.controls = controls
    
    def __repr__(self):
        controls_str = ', '.join(map(str, self.controls))
        return f"signature {{ {controls_str} }}"
    
class Link:
    def __init__(self, name, source, targets):
        self.name = name
        self.source = source
        self.targets = targets
    
    def __repr__(self):
        return f"{self.name}: {self.source}->{self.targets}"

# Gramática mínima
def p_program(p):
    '''program : statements'''
    p[0] = [s for s in p[1] if s is not None]

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
    '''bigraph_statement : BIGRAPH IDENTIFIER EQUALS place_graph link_options SEMICOLON'''
    name = p[2]
    place = p[4]
    links = p[5]           # puede ser [] o una lista de Link
    p[0] = BiGraph(name, place, links)

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

def p_place_graph(p):
    '''place_graph : ROOT COLON node_structure
                   | node_structure'''
    p[0] = p[3] if len(p)==4 else [p[1]]

def p_node_structure(p):
    '''node_structure : LBRACKET node_list_inner RBRACKET
                      | IDENTIFIER child_opt'''
    if p[1] == '[':
        p[0] = p[2]
    else:
        p[0] = BiGraphNode(p[1], p[2])

def p_node_list_inner(p):
    '''node_list_inner : node_structure
                       | node_list_inner COMPOSE node_structure'''
    # construir árbol compuesto de nodos
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_child_opt(p):
    '''child_opt : COLON node_structure
                 | empty'''
    p[0] = [p[2]] if len(p)==3 else []

def p_link_list(p):
    '''link_list : link_def
                 | link_list COMMA link_def'''
    if len(p) == 2:
        # un solo enlace
        p[0] = [p[1]]
    else:
        # lista previa + nuevo enlace
        p[0] = p[1] + [p[3]]

def p_link_def(p):
    '''link_def : IDENTIFIER COLON IDENTIFIER ARROW target_list'''
    # p[1] = nombre del enlace
    # p[3] = fuente
    # p[5] = lista de destinos
    p[0] = Link(name=p[1], source=p[3], targets=p[5])

def p_link_options(p):
    '''link_options : WITH LINKS COLON link_list
                    | empty'''
    if len(p) == 5:
        # WITH LINKS: link_list
        p[0] = p[3] if False else p[4]  # p[4] es la lista retornada por link_list
    else:
        # vacío
        p[0] = []

def p_target_list(p):
    '''target_list : IDENTIFIER
                   | LBRACKET target_list_inner RBRACKET'''
    if len(p) == 2:
        # destino único
        p[0] = [p[1]]
    else:
        # lista dentro de [ … ]
        p[0] = p[2]

def p_target_list_inner(p):
    '''target_list_inner : IDENTIFIER
                         | target_list_inner COMMA IDENTIFIER'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_empty(p):
    'empty :'
    p[0] = None

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
        Room   : 2
    }

    rule move: Person => Room;
    bigraph house = Building with links: link1: Person => Building;
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
