from instrucciones import Instrucciones

MEMORY_SIZE = 2**16

class Memoria:
    def __init__(self):
        self.mem = [0] * MEMORY_SIZE

    def leer(self, direccion):
        assert 0 <= direccion < MEMORY_SIZE, f"Dirección fuera de rango: {direccion}"
        return self.mem[direccion]

    def escribir(self, direccion, valor):
        assert 0 <= direccion < MEMORY_SIZE, f"Dirección fuera de rango: {direccion}"
        self.mem[direccion] = valor

class CPU:
    def __init__(self, memoria):
        self.mem = memoria
        self.reg = [0] * 16
        self.PC = 0
        self.IR = 0
        self.IR_len = 0
        self.FLAGS = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.running = True
        self.instrucciones = Instrucciones(self)

    def fetch(self):
        raw = self.mem.leer(self.PC)
        if isinstance(raw, tuple):
            self.IR, self.IR_len = raw
        else:
            self.IR = raw
            self.IR_len = self.IR.bit_length() or 1
        self.PC += 1

    def decode_execute(self):
        self.instrucciones.ejecutar(self.IR, self.IR_len)

    def ejecutar(self):
        # Ejecución sin debug paso a paso
        while self.running:
            self.fetch()
            self.decode_execute()

class Cargador:
    @staticmethod
    def parse_binary(instr_str: str):
        bits = instr_str.replace(" ", "").replace("\n", "")
        if len(bits) == 0 or any(c not in "01" for c in bits):
            raise ValueError("Cadena inválida: debe contener sólo '0' y '1'")
        return int(bits, 2), len(bits)

    @staticmethod
    def cargar(memoria, instrucciones, base_addr=0):
        for offset, palabra in enumerate(instrucciones):
            if isinstance(palabra, str):
                valor, bit_len = Cargador.parse_binary(palabra)
                memoria.escribir(base_addr + offset, (valor, bit_len))
            else:
                memoria.escribir(base_addr + offset, palabra)

# Función de utilidad para la GUI
def run_instructions(instrs, base=0, regs_init=None):
    """
    Carga y ejecuta una lista de instrucciones binarias o tuplas,
    devuelve la instancia de CPU y Memoria tras la ejecución.
    regs_init: dict {registro: valor}
    """
    mem = Memoria()
    cpu = CPU(mem)
    if regs_init:
        for r, v in regs_init.items():
            cpu.reg[r] = v
    Cargador.cargar(mem, instrs, base_addr=base)
    cpu.PC = base
    cpu.ejecutar()
    return cpu, mem
