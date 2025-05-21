# %%writefile Instrucciones.py *Para correrlo en colab*
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
    def __init__(self, memoria,debug):
        self.mem = memoria
        self.reg = [0] * 16
        self.PC = 0
        self.IR = 0
        self.MAR = 0
        self.MDR = 0
        self.FLAGS = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.running = True
        self.debug = debug
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
            if self.debug:
                self.mostrar_estado()
            self.decode_execute()
            if self.debug:
                input("Presiona Enter para continuar...")

    def mostrar_estado(self):
        print("\n========================")
        print(f"PC:  0x{self.PC:04X}")
        print(f"IR:  0x{self.IR:016X}")
        print("Registros:")
        for i in range(0, 16, 4):
            print(" ".join([f"R{j}: {self.reg[j]:016X}" for j in range(i, i+4)]))
        print("FLAGS:", self.FLAGS)
        print("========================")

class Cargador:
    @staticmethod
    def cargar(memoria, instrucciones, base_addr):
        for i, palabra in enumerate(instrucciones):
            memoria.escribir(base_addr + i, palabra)

# Ejemplo de uso
if __name__ == '__main__':
    mem = Memoria()
    cpu = CPU(mem, debug=True)

    # Programa de prueba: Euclides MCD de 36 y 24 en R1 y R2
    euclides = [
        0x8A11200000000000,
        0xE1300000000000D0,
        0xE2300000000000CD,
        0x8211200000000000,
        0xE0300000000000C8,
        0x8212100000000000,
        0xE0300000000000C8,
        0x0000000000000000,
        0xFF00000000000000
    ]

    insertionSort = [
        0xC23100000A000000,
        0xC222000000000005,
        0xC203000000000002,
        0x8A13200000000000,
        0xE2300000000000CE,
        0xFF00000000000000,
        0xC23400000A000010,
        0xC215300000000002,
        0x8205000000000001,
        0xC23400000A000008,
        0x8A13000000000000,
        0xE2300000000000D6,
        0x8A16400000000000,
        0xE2300000000000D6,
        0x8105000000000001,
        0xC32600000A000010,
        0x8205000000000002,
        0xE2300000000000D1,
        0x8105000000000001,
        0xC32400000A000010,
        0xE2300000000000CB,
    ]

    Cargador.cargar(mem, euclides, 0xC8)
    cpu.PC = 0xC8
    cpu.reg[1] = 36
    cpu.reg[2] = 24
    print(f"Antes de ejecutar:")
    print(f"R1 = {cpu.reg[1]}")
    print(f"R2 = {cpu.reg[2]}")
    cpu.ejecutar()

    print(f"Resultado en R1: {cpu.reg[1]}")
