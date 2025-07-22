"""
Módulo Semántico para Bigrafos según Robin Milner
================================================

Este módulo implementa la semántica de bigrafos, incluyendo:
- Place Graph (Grafo de Lugar): modelar localidad y anidamiento
- Link Graph (Grafo de Enlace): modelar conectividad y comunicación
- Reglas de Reacción: transformaciones del sistema
- Matching y Aplicación de Reglas
"""

from typing import Dict, List, Set, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import namedtuple
import copy
from bigraph_parser import VarDecl, BiGraph, Reaction, Signature, Link

# ============================================================================
# ESTRUCTURAS BÁSICAS DE BIGRAFOS
# ============================================================================

class Environment:
    """
    Tabla de símbolos y almacenamiento de variables,
    con soporte para escalares y arreglos multidimensionales.
    """
    def __init__(self):
        # vars: nombre -> estructura de datos (int, float, str o lista anidada)
        self.vars = {}

    def declare(self, name, type_name, dimensions):
        if name in self.vars:
            raise SemanticError(f"Variable '{name}' ya declarada")
        # Construir estructura inicial: escalares o listas anidadas de tamaño fijo
        if not dimensions:
            self.vars[name] = None
        else:
            # crea una lista multidim de None
            def make_array(sizes):
                size, *rest = sizes
                arr = [None] * size
                return [make_array(rest) for _ in range(size)] if rest else arr
            self.vars[name] = make_array(dimensions)

    def assign(self, name, value, indices=None):
        if name not in self.vars:
            raise SemanticError(f"Variable '{name}' no declarada")
        target = self.vars[name]
        if indices:
            # navegar hasta la celda adecuada
            for idx in indices[:-1]:
                if idx < 0 or idx >= len(target):
                    raise SemanticError(f"Índice {idx} fuera de rango en '{name}'")
                target = target[idx]
            last = indices[-1]
            if last < 0 or last >= len(target):
                raise SemanticError(f"Índice {last} fuera de rango en '{name}'")
            target[last] = value
        else:
            self.vars[name] = value

    def get(self, name, indices=None):
        if name not in self.vars:
            raise SemanticError(f"Variable '{name}' no declarada")
        target = self.vars[name]
        if indices:
            for idx in indices:
                if idx < 0 or idx >= len(target):
                    raise SemanticError(f"Índice {idx} fuera de rango en '{name}'")
                target = target[idx]
        return target


class SemanticsProcessor:
    def __init__(self):
        self.env = Environment()
        # ... otras estructuras si tienes (e.g., para controladores, puertos)

    def process(self, ast_list: BiGraph):
        # Asumimos que ast_root.statements es la lista de Sentencias+VarDecl
        for stmt in ast_list:
            if isinstance(stmt, VarDecl):
                self._handle_vardecl(stmt)
            else:
                self._handle_statement(stmt)
        # luego devolvemos o construimos el bigraph semántico
        return self.env, ast_list  # o tu objeto final

    def _handle_vardecl(self, decl: VarDecl):
        # 1. registrar la declaración
        self.env.declare(decl.name, decl.type_name, decl.dimensions)
        # 2. si hay inicializador, evaluarlo y asignar
        if decl.value is not None:
            # Si fuese expresión compleja, aquí llamarías a un evaluador recursivo
            val = decl.value
            # Chequear tipo:
            if decl.dimensions:
                # inicializador escalar para todo el arreglo
                # podrías replicar o solo asignar a [0][...]
                self.env.assign(decl.name, val, indices=[0]*len(decl.dimensions))
            else:
                self.env.assign(decl.name, val)

    def _handle_statement(self, stmt):
        # tu lógica existente para rules, controls, bigraphs...
        pass

    # si más adelante añades expresiones/assignments, podrías definir:
    # def _eval_expression(self, expr): ...


# Clase de error semántico
class SemanticError(Exception):
    pass

@dataclass
class Port:
    """Puerto de un nodo - punto de conexión para enlaces"""
    node_id: str
    port_index: int
    
    def __str__(self):
        return f"{self.node_id}.{self.port_index}"

@dataclass
class Edge:
    """Arista que conecta puertos"""
    edge_id: str
    ports: Set[Port] = field(default_factory=set)
    
    def add_port(self, port: Port):
        self.ports.add(port)
    
    def remove_port(self, port: Port):
        self.ports.discard(port)
    
    def __str__(self):
        ports_str = ", ".join(str(p) for p in self.ports)
        return f"Edge({self.edge_id}: {ports_str})"

@dataclass
class Control:
    """Control de un nodo - define su tipo y aridad"""
    name: str
    arity: int  # número de puertos
    is_atomic: bool = False
    
    def __str__(self):
        atomic_str = "atomic " if self.is_atomic else ""
        return f"{atomic_str}{self.name}:{self.arity}"

# ============================================================================
# PLACE GRAPH (GRAFO DE LUGAR)
# ============================================================================

class PlaceGraph:
    """
    Grafo de Lugar - modela la estructura jerárquica y localidad de los nodos
    Implementa una estructura de árbol donde los nodos pueden contener otros nodos
    """
    
    def __init__(self):
        self.nodes: Dict[str, 'BiGraphNode'] = {}
        self.roots: Set[str] = set()  # nodos raíz
        self.sites: Set[str] = set()  # sitios (hoyos en el contexto)
        self.parent: Dict[str, str] = {}  # hijo -> padre
        self.children: Dict[str, Set[str]] = {}  # padre -> {hijos}
    
    def add_node(self, node_id: str, parent_id: Optional[str] = None):
        """Añadir un nodo al grafo de lugar"""
        if node_id not in self.children:
            self.children[node_id] = set()
        
        if parent_id is None:
            self.roots.add(node_id)
        else:
            self.parent[node_id] = parent_id
            self.children[parent_id].add(node_id)
            self.roots.discard(node_id)
    
    def nest(self, parent_id: str, child_id: str):
        """Anidar child_id dentro de parent_id"""
        if child_id in self.parent:
            old_parent = self.parent[child_id]
            self.children[old_parent].discard(child_id)
        
        self.parent[child_id] = parent_id
        self.children[parent_id].add(child_id)
        self.roots.discard(child_id)
    
    def unnest(self, node_id: str):
        """Sacar un nodo de su contenedor"""
        if node_id in self.parent:
            parent_id = self.parent[node_id]
            self.children[parent_id].discard(node_id)
            del self.parent[node_id]
            self.roots.add(node_id)
    
    def get_ancestors(self, node_id: str) -> List[str]:
        """Obtener todos los ancestros de un nodo"""
        ancestors = []
        current = node_id
        while current in self.parent:
            current = self.parent[current]
            ancestors.append(current)
        return ancestors
    
    def get_descendants(self, node_id: str) -> Set[str]:
        """Obtener todos los descendientes de un nodo"""
        descendants = set()
        stack = list(self.children.get(node_id, set()))
        
        while stack:
            child = stack.pop()
            descendants.add(child)
            stack.extend(self.children.get(child, set()))
        
        return descendants
    
    def is_ancestor(self, ancestor_id: str, node_id: str) -> bool:
        """Verificar si ancestor_id es ancestro de node_id"""
        return ancestor_id in self.get_ancestors(node_id)
    
    def __str__(self):
        def print_subtree(node_id: str, indent: int = 0) -> str:
            result = "  " * indent + f"{node_id}\n"
            for child in sorted(self.children.get(node_id, set())):
                result += print_subtree(child, indent + 1)
            return result
        
        result = "PlaceGraph:\n"
        for root in sorted(self.roots):
            result += print_subtree(root, 1)
        return result

# ============================================================================
# LINK GRAPH (GRAFO DE ENLACE)
# ============================================================================

class LinkGraph:
    """
    Grafo de Enlace - modela las conexiones entre puertos de los nodos
    Implementa un grafo hipergráfico donde las aristas pueden conectar múltiples puertos
    """
    
    def __init__(self):
        self.edges: Dict[str, Edge] = {}
        self.ports: Dict[Port, str] = {}  # port -> edge_id
        self.outer_names: Set[str] = set()  # nombres externos
        self.inner_names: Set[str] = set()  # nombres internos
    
    def add_edge(self, edge_id: str) -> Edge:
        """Crear una nueva arista"""
        edge = Edge(edge_id)
        self.edges[edge_id] = edge
        return edge
    
    def link_ports(self, edge_id: str, ports: List[Port]):
        """Conectar puertos a través de una arista"""
        if edge_id not in self.edges:
            self.add_edge(edge_id)
        
        edge = self.edges[edge_id]
        for port in ports:
            # Desconectar puerto de arista anterior si existe
            if port in self.ports:
                old_edge_id = self.ports[port]
                self.edges[old_edge_id].remove_port(port)
            
            # Conectar a nueva arista
            edge.add_port(port)
            self.ports[port] = edge_id
    
    def unlink_port(self, port: Port):
        """Desconectar un puerto"""
        if port in self.ports:
            edge_id = self.ports[port]
            self.edges[edge_id].remove_port(port)
            del self.ports[port]
    
    def merge_edges(self, edge1_id: str, edge2_id: str, new_edge_id: str):
        """Fusionar dos aristas en una nueva"""
        if edge1_id not in self.edges or edge2_id not in self.edges:
            return
        
        new_edge = self.add_edge(new_edge_id)
        
        # Mover todos los puertos a la nueva arista
        all_ports = (self.edges[edge1_id].ports | 
                    self.edges[edge2_id].ports)
        
        for port in all_ports:
            new_edge.add_port(port)
            self.ports[port] = new_edge_id
        
        # Eliminar aristas antiguas
        del self.edges[edge1_id]
        del self.edges[edge2_id]
    
    def closure(self, names: Set[str]):
        """Aplicar clausura sobre un conjunto de nombres"""
        self.inner_names.update(names)
        self.outer_names -= names
    
    def get_connected_ports(self, port: Port) -> Set[Port]:
        """Obtener todos los puertos conectados a un puerto dado"""
        if port in self.ports:
            edge_id = self.ports[port]
            return self.edges[edge_id].ports.copy()
        return set()
    
    def __str__(self):
        result = "LinkGraph:\n"
        for edge_id, edge in self.edges.items():
            result += f"  {edge}\n"
        if self.outer_names:
            result += f"  Outer names: {self.outer_names}\n"
        if self.inner_names:
            result += f"  Inner names: {self.inner_names}\n"
        return result

# ============================================================================
# NODO DE BIGRAFO
# ============================================================================

@dataclass
class BiGraphNode:
    """Nodo en un bigrafo con control y puertos"""
    node_id: str
    control: Control
    ports: List[Port] = field(default_factory=list)
    
    def __post_init__(self):
        # Crear puertos según la aridad del control
        if not self.ports:
            self.ports = [Port(self.node_id, i) for i in range(self.control.arity)]
    
    def get_port(self, index: int) -> Optional[Port]:
        """Obtener puerto por índice"""
        if 0 <= index < len(self.ports):
            return self.ports[index]
        return None
    
    def __str__(self):
        return f"{self.control.name}({self.node_id})"

# ============================================================================
# BIGRAFO PRINCIPAL
# ============================================================================

class BiGraph:
    """
    Bigrafo - combina Place Graph y Link Graph
    Representa la estructura completa de un sistema según el modelo de Milner
    """
    
    def __init__(self, name: str = ""):
        self.name = name
        self.place: PlaceGraph = PlaceGraph()
        self.link: LinkGraph = LinkGraph()
        self.nodes: Dict[str, BiGraphNode] = {}
        self.controls: Dict[str, Control] = {}
    
    def add_control(self, control: Control):
        """Registrar un control en el sistema"""
        self.controls[control.name] = control
    
    def add_node(self, node_id: str, control_name: str, parent_id: Optional[str] = None) -> BiGraphNode:
        """Añadir un nodo al bigrafo"""
        if control_name not in self.controls:
            raise ValueError(f"Control '{control_name}' not defined")
        
        control = self.controls[control_name]
        node = BiGraphNode(node_id, control)
        
        self.nodes[node_id] = node
        self.place.nodes[node_id] = node
        self.place.add_node(node_id, parent_id)
        
        return node
    
    def nest(self, parent_id: str, child_id: str):
        """Anidar un nodo dentro de otro"""
        self.place.nest(parent_id, child_id)
    
    def link(self, edge_id: str, port_specs: List[Tuple[str, int]]):
        """Crear enlace entre puertos especificados como (node_id, port_index)"""
        ports = []
        for node_id, port_index in port_specs:
            if node_id in self.nodes:
                port = self.nodes[node_id].get_port(port_index)
                if port:
                    ports.append(port)
        
        if ports:
            self.link.link_ports(edge_id, ports)
    
    def compose_parallel(self, other: 'BiGraph') -> 'BiGraph':
        """Composición paralela (|) con otro bigrafo"""
        result = BiGraph(f"({self.name} | {other.name})")
        
        # Copiar controles
        result.controls.update(self.controls)
        result.controls.update(other.controls)
        
        # Copiar nodos de ambos bigrafos
        for node_id, node in self.nodes.items():
            new_node = BiGraphNode(f"L_{node_id}", node.control)
            result.nodes[new_node.node_id] = new_node
            result.place.nodes[new_node.node_id] = new_node
            result.place.add_node(new_node.node_id)
        
        for node_id, node in other.nodes.items():
            new_node = BiGraphNode(f"R_{node_id}", node.control)
            result.nodes[new_node.node_id] = new_node
            result.place.nodes[new_node.node_id] = new_node
            result.place.add_node(new_node.node_id)
        
        return result
    
    def compose_sequential(self, other: 'BiGraph') -> 'BiGraph':
        """Composición secuencial (.) con otro bigrafo"""
        result = BiGraph(f"({self.name} . {other.name})")
        # Implementación simplificada - en la práctica requiere matching de interfaces
        return result
    
    def tensor_product(self, other: 'BiGraph') -> 'BiGraph':
        """Producto tensorial (*) con otro bigrafo"""
        result = BiGraph(f"({self.name} * {other.name})")
        # Implementación del producto tensorial
        return result
    
    def get_interface(self) -> Tuple[Set[str], Set[str]]:
        """Obtener interfaz del bigrafo (inner_names, outer_names)"""
        return (self.link.inner_names.copy(), self.link.outer_names.copy())
    
    def __str__(self):
        result = f"BiGraph '{self.name}':\n"
        result += str(self.place)
        result += str(self.link)
        result += "Nodes:\n"
        for node_id, node in self.nodes.items():
            result += f"  {node}\n"
        return result

# ============================================================================
# REGLAS DE REACCIÓN
# ============================================================================

@dataclass
class ReactionRule:
    """Regla de reacción: L -> R (con posible condición)"""
    name: str
    left_hand_side: BiGraph  # Patrón a buscar
    right_hand_side: BiGraph  # Reemplazo
    condition: Optional[callable] = None
    
    def can_apply(self, bigraph: BiGraph) -> List[Dict[str, str]]:
        """
        Verificar si la regla se puede aplicar al bigrafo
        Retorna lista de matchings posibles (mapeo de variables)
        """
        matchings = []
        # Implementación simplificada del matching de patrones
        # En la implementación completa, esto sería un algoritmo complejo
        # que busca subgrafos isomórficos
        
        if self._simple_match(bigraph):
            matchings.append({})  # matching vacío para simplicidad
        
        return matchings
    
    def _simple_match(self, bigraph: BiGraph) -> bool:
        """Matching simplificado para demostración"""
        # Verificar si existen nodos con los controles requeridos
        lhs_controls = [node.control.name for node in self.left_hand_side.nodes.values()]
        bg_controls = [node.control.name for node in bigraph.nodes.values()]
        
        for required_control in lhs_controls:
            if required_control not in bg_controls:
                return False
        return True
    
    def apply(self, bigraph: BiGraph, matching: Dict[str, str]) -> BiGraph:
        """
        Aplicar la regla al bigrafo con el matching dado
        """
        result = copy.deepcopy(bigraph)
        
        # Implementación simplificada
        # En la práctica, esto requiere:
        # 1. Encontrar el contexto donde aplicar la regla
        # 2. Remover el patrón del lado izquierdo
        # 3. Insertar el patrón del lado derecho
        # 4. Reconectar enlaces según sea necesario
        
        print(f"Aplicando regla '{self.name}' a bigrafo '{bigraph.name}'")
        return result

# ============================================================================
# SISTEMA DE REACCIÓN DE BIGRAFOS
# ============================================================================

class BiGraphReactionSystem:
    """
    Sistema de Reacción de Bigrafos (BRS)
    Maneja la evolución de bigrafos mediante reglas de reacción
    """
    
    def __init__(self):
        self.signature: Dict[str, Control] = {}
        self.rules: List[ReactionRule] = []
        self.current_state: Optional[BiGraph] = None
        self.history: List[BiGraph] = []
    
    def add_control(self, control: Control):
        """Añadir control a la signatura"""
        self.signature[control.name] = control
    
    def add_rule(self, rule: ReactionRule):
        """Añadir regla de reacción"""
        self.rules.append(rule)
    
    def set_initial_state(self, bigraph: BiGraph):
        """Establecer estado inicial del sistema"""
        self.current_state = bigraph
        self.history = [copy.deepcopy(bigraph)]
    
    def step(self) -> bool:
        """
        Ejecutar un paso de reacción
        Retorna True si se aplicó alguna regla, False si no hay reglas aplicables
        """
        if not self.current_state:
            return False
        
        for rule in self.rules:
            matchings = rule.can_apply(self.current_state)
            if matchings:
                # Aplicar la primera regla que coincida con el primer matching
                new_state = rule.apply(self.current_state, matchings[0])
                self.current_state = new_state
                self.history.append(copy.deepcopy(new_state))
                print(f"Regla '{rule.name}' aplicada")
                return True
        
        print("No hay reglas aplicables")
        return False
    
    def run(self, max_steps: int = 100):
        """Ejecutar el sistema hasta que no haya reglas aplicables"""
        step_count = 0
        while step_count < max_steps and self.step():
            step_count += 1
        
        print(f"Sistema terminado después de {step_count} pasos")
    
    def get_current_state(self) -> Optional[BiGraph]:
        """Obtener estado actual del sistema"""
        return self.current_state
    
    def get_history(self) -> List[BiGraph]:
        """Obtener historial de estados"""
        return self.history.copy()

# ============================================================================
# FUNCIONES DE UTILIDAD Y CONSTRUCCIÓN
# ============================================================================

def create_simple_bigraph_example():
    """Crear un ejemplo simple de bigrafo para demostración"""
    
    # Crear sistema
    system = BiGraphReactionSystem()
    
    # Definir controles
    person_control = Control("Person", 1, is_atomic=True)
    room_control = Control("Room", 2)
    building_control = Control("Building", 0)
    
    system.add_control(person_control)
    system.add_control(room_control)
    system.add_control(building_control)
    
    # Crear bigrafo inicial
    initial = BiGraph("initial_state")
    initial.add_control(person_control)
    initial.add_control(room_control)
    initial.add_control(building_control)
    
    # Añadir nodos
    building = initial.add_node("building1", "Building")
    room1 = initial.add_node("room1", "Room", "building1")
    room2 = initial.add_node("room2", "Room", "building1")
    person = initial.add_node("alice", "Person")
    
    # Crear regla: persona entra en habitación
    lhs = BiGraph("person_outside")
    lhs.add_control(person_control)
    lhs.add_control(room_control)
    lhs.add_node("person", "Person")
    lhs.add_node("room", "Room")
    
    rhs = BiGraph("person_inside")
    rhs.add_control(person_control)
    rhs.add_control(room_control)
    room_node = rhs.add_node("room", "Room")
    person_node = rhs.add_node("person", "Person", "room")
    
    enter_rule = ReactionRule("enter_room", lhs, rhs)
    system.add_rule(enter_rule)
    
    return system, initial

# ============================================================================
# FUNCIÓN DE TESTING
# ============================================================================

def test_bigraph_semantics():
    """Función de prueba para el módulo semántico"""
    print("=== Testing Bigraph Semantics ===\n")
    
    # Crear ejemplo
    system, initial = create_simple_bigraph_example()
    
    print("Estado inicial:")
    print(initial)
    print()
    
    # Establecer estado inicial
    system.set_initial_state(initial)
    
    # Ejecutar sistema
    print("Ejecutando sistema de reacción...")
    system.run(max_steps=5)
    
    print("\nEstado final:")
    if system.get_current_state():
        print(system.get_current_state())
    
    print(f"\nHistorial: {len(system.get_history())} estados")

if __name__ == '__main__':
    test_bigraph_semantics()
