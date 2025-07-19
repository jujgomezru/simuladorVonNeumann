from instrucciones import Instrucciones
from preprocessor import Preprocessor
from assembler import ensamblar     
from linker_loader import link_and_load
import ast

MEMORY_SIZE = 2**16

class Memoria:
    def __init__(self): self.mem=[0]*MEMORY_SIZE
    def leer(self,d): assert 0<=d<MEMORY_SIZE; return self.mem[d]
    def escribir(self,d,v): assert 0<=d<MEMORY_SIZE; self.mem[d]=v

class CPU:
    def __init__(self,mem):
        self.mem=mem; self.reg=[0]*16; self.PC=0; self.IR=0; self.IR_len=0
        self.FLAGS={'Z':0,'N':0,'C':0,'V':0}; self.running=True
        self.instrucciones=Instrucciones(self)
    def fetch(self):
        raw = self.mem.leer(self.PC)
        if isinstance(raw, tuple):
            self.IR, self.IR_len = raw
        else:
            self.IR = raw
            self.IR_len = self.IR.bit_length()
            if self.IR_len < 8:
                # Detener ejecución si se detecta instrucción basura
                print(f"[DEBUG] Instrucción inválida en {hex(self.PC)}: {self.IR}")
                self.running = False
                return
        self.PC += 1

    def decode_execute(self): self.instrucciones.ejecutar(self.IR,self.IR_len)
    def ejecutar(self, max_instrucciones=100):
        cuenta = 0
        while self.running and cuenta < max_instrucciones:
            self.fetch()
            print(f"[TRACE] Ejecutando en PC={hex(self.PC-1)}: IR={self.IR}, bits={self.IR_len}")
            self.decode_execute()
            cuenta += 1

class Cargador:
    @staticmethod
    def parse_binary(s: str):
        b = s.replace(' ', '').replace('\n', '')
        return int(b, 2), len(b)

    @staticmethod
    def cargar(memoria, instrs, base_addr=0):
        for i, word in enumerate(instrs):
            if isinstance(word, str):
                word = word.strip()
                if word.startswith("("):
                    try:
                        word = ast.literal_eval(word)
                        assert isinstance(word, tuple) and len(word) == 2
                    except Exception:
                        raise ValueError(f"Instrucción inválida como tupla: {word}")
                elif set(word).issubset({'0', '1'}):  # binario
                    word = Cargador.parse_binary(word)
                else:
                    raise ValueError(f"Formato de instrucción no reconocido: {word}")
            memoria.escribir(base_addr + i, word)
# utilidad para GUI
from preprocessor import Preprocessor
from assembler import ensamblar
from linker_loader import link_and_load

def run_assembly(src_file, base=0):
    source = Preprocessor().process_file(src_file)
    prog = ensamblar(source)
    mem  = link_and_load(prog, base)
    cpu  = CPU(mem)
    cpu.PC = base
    cpu.ejecutar(max_instrucciones=50)  # ← CAMBIO AQUÍ
    return cpu, mem


def run_instructions(instrs, base=0, regs_init=None):
    mem=Memoria(); cpu=CPU(mem)
    if regs_init:
        for r,v in regs_init.items(): cpu.reg[r]=v
    Cargador.cargar(mem,instrs,base); cpu.PC=base; cpu.ejecutar(); return cpu,mem