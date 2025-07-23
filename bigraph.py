class Node:
    def __init__(self, name, ports=None):
        self.name = name
        self.ports = ports or []
        self.children = []
        self.parent = None

    def __repr__(self):
        return f"Node({self.name})"


class Link:
    def __init__(self, name):
        self.name = name
        self.connected_ports = []

    def __repr__(self):
        return f"Link({self.name})"


class Bigraph:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.instructions = []

    def add_node(self, node, parent=None):
        if parent:
            parent.children.append(node)
            node.parent = parent
        self.nodes.append(node)

    def add_instruction(self, line):
        if line and line.strip():  # ✨ Asegura que la instrucción no sea vacía
            self.instructions.append(line.strip())

    def add_link(self, link):
        self.links.append(link)

    def connect(self, node1, port1, node2, port2):
        link = Link(f"{node1.name}:{port1}-{node2.name}:{port2}")
        link.connected_ports.extend([(node1, port1), (node2, port2)])
        self.links.append(link)

    def __repr__(self):
        return f"Bigraph(Nodes={self.nodes}, Links={self.links})"


class BigraphCompiler:
    def __init__(self, bigraph):
        self.bigraph = bigraph
        self.assembly_lines = []

    def compile(self):
        for node in self.bigraph.nodes:
            self.compile_node(node)

        # ⚠️ Asegura que no haya líneas vacías antes de HALT
        self.assembly_lines = [l for l in self.assembly_lines if l.strip()]
        self.assembly_lines.append("HALT")
        return self.assembly_lines

    def compile_node(self, node):
        if not node.name.strip():
            return  # ⚠️ omitir nodos vacíos

        if node.name.startswith("decl_"):
            var = node.name[5:]
            self.assembly_lines.append(f"; declaración de {var}")
        elif node.name.startswith("assign_"):
            var = node.name[7:]
            self.assembly_lines.append(f"; asignación a {var}")
        elif node.name == "procers":
            self.compile_procers(node)
        elif node.name == "colectavgB":
            self.assembly_lines.append("NOP  ; colectavgB simulada")
        elif node.name == "while":
            self.assembly_lines.append("NOP  ; inicio while")
            for child in node.children:
                self.compile_node(child)
            self.assembly_lines.append("NOP  ; fin while")
        else:
            self.assembly_lines.append(f"; Nodo no reconocido: {node.name}")

    def compile_procers(self, node: Node):
        self.assembly_lines.append("NOP  ; inicio de bloque procers")
        for child in node.children:
            self.compile_node(child)
        self.assembly_lines.append("NOP  ; fin de bloque procers")
