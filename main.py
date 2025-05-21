from instrucciones import Instrucciones

WORD_SIZE = 64  # bits
MEMORY_SIZE = 2 ** 16  # palabras de 64 bits

class Memoria:
    def __init__(self):
        self.mem = [0] * MEMORY_SIZE

    def leer(self, direccion):
        assert 0 <= direccion < MEMORY_SIZE, f"Dirección fuera de rango: {direccion}"
        return self.mem[direccion]

    def escribir(self, direccion, valor):
        assert 0 <= direccion < MEMORY_SIZE, f"Dirección fuera de rango: {direccion}"
        self.mem[direccion] = valor & 0xFFFFFFFFFFFFFFFF

class CPU:
    def __init__(self, memoria):
        self.mem = memoria
        self.reg = [0] * 16
        self.PC = 0
        self.IR = 0
        self.MAR = 0
        self.MDR = 0
        self.FLAGS = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.running = True
        self.instrucciones = Instrucciones(self)

    def fetch(self):
        self.MAR = self.PC
        self.IR = self.mem.leer(self.MAR)
        self.PC += 1

    def decode_execute(self):
        self.instrucciones.ejecutar(self.IR)

    def ejecutar(self):
        while self.running:
            self.fetch()
            self.decode_execute()

class Cargador:
    @staticmethod
    def cargar(memoria, instrucciones, base_addr):
        for i, palabra in enumerate(instrucciones):
            memoria.escribir(base_addr + i, palabra)

# Ejemplo de uso
if __name__ == '__main__':
    mem = Memoria()
    cpu = CPU(mem)

    # Programa de prueba: Euclides MCD de 36 y 24 en R1 y R2
    instrucciones = [
        0x8A11000000000000,
        0xE1300000000000D2,
        0xE2300000000000CD,
        0x8211200000000000,
        0xE0300000000000C8,
        0x8221400000000000,
        0xE0300000000000C8,
        0x0000000000000000,
        0xFF00000000000000
    ]

    Cargador.cargar(mem, instrucciones, 0xC8)
    cpu.PC = 0xC8
    cpu.reg[1] = 36
    cpu.reg[2] = 24
    cpu.ejecutar()

    print(f"Resultado en R1: {cpu.reg[1]}")
