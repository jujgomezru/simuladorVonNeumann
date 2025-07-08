# main.py
from instrucciones_test import Instrucciones

MEMORY_SIZE = 2**16

class Memoria:
    def __init__(self):
        self.mem = [0] * MEMORY_SIZE

    def leer(self, direccion):
        assert 0 <= direccion < MEMORY_SIZE, f"Dirección fuera de rango: {direccion}"
        return self.mem[direccion]

    def escribir(self, direccion, valor):
        # valor puede ser int o (int, bit_len)
        assert 0 <= direccion < MEMORY_SIZE, f"Dirección fuera de rango: {direccion}"
        self.mem[direccion] = valor


class CPU:
    def __init__(self, memoria, debug):
        self.mem        = memoria
        self.reg        = [0] * 16
        self.PC         = 0
        self.IR         = 0
        self.MAR        = 0
        self.MDR        = 0
        self.FLAGS      = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.running    = True
        self.debug      = debug
        self.instrucciones = Instrucciones(self)

    def fetch(self):
        raw = self.mem.leer(self.PC)
        if isinstance(raw, tuple):
            self.IR, self.IR_len = raw
        else:
            self.IR      = raw
            # para datos o valores sin longitud, inferimos la longitud mínima
            self.IR_len  = self.IR.bit_length() or 1
        self.PC += 1

    def decode_execute(self):
        # ahora el descodificador puede usar self.IR_len
        self.instrucciones.ejecutar(self.IR, self.IR_len)

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
            print(" ".join(f"R{j}: {self.reg[j]:016X}" for j in range(i, i+4)))
        print("FLAGS:", self.FLAGS)
        print("========================")

class Cargador:
    @staticmethod
    def parse_binary(instr_str: str):
        bits = instr_str.replace(" ", "").replace("\n", "")
        # ahora **no** rellenamos ni limitamos a 64 bits
        if len(bits) == 0 or any(c not in "01" for c in bits):
            raise ValueError("Cadena inválida: debe contener sólo '0' y '1'")
        return int(bits, 2), len(bits)

    @staticmethod
    def cargar(memoria, instrucciones, base_addr):
        for offset, palabra in enumerate(instrucciones):
            if isinstance(palabra, str):
                valor, bit_len = Cargador.parse_binary(palabra)
                memoria.escribir(base_addr + offset, (valor, bit_len))
            else:
                # datos inmediatos, etc.
                memoria.escribir(base_addr + offset, palabra)

if __name__ == '__main__':
    mem = Memoria()
    cpu = CPU(mem, debug=True)

    # Ejemplo: Euclides MCD de 36 y 24 en R1, R2
    # Las cadenas deben comenzar con los bits MSB de la instrucción,
    # tal como en la tabla. El resto (menos significativo) se rellena a 0.
    euclides = [
    # comp R1,R2   → opcode=0x8A (10001010), modo=00, R1=0001, R2=0010  (18 bits)
    "100010100000010010",
    # jz 0xD0      → opcode=0xE1 (11100001), dest=0xD0 (208) in 32-bit little-endian field  (40 bits)
    "11100001" "00000000000000000000000011010000",
    # jn 0xCD      → opcode=0xE2 (11100010), dest=0xCD (205) in 32-bit field  (40 bits)
    "11100010" "00000000000000000000000011001101",
    # sub R1,R2    → opcode=0x82 (10000010), modo=00, R1=0001, R2=0010  (18 bits)
    "100000100000010010",
    # jmp 0xC8     → opcode=0xE0 (11100000), dest=0xC8 (200) in 32-bit field  (40 bits)
    "11100000" "00000000000000000000000011001000",
    # sub R2,R1    → opcode=0x82 (10000010), modo=00, R1=0010, R2=0001  (18 bits)
    "100000100000100001",
    # jmp 0xC8     → mismo que antes  (40 bits)
    "11100000" "00000000000000000000000011001000",
    # nop          → opcode=0x00  (8 bits)
    "00000000",
    # halt         → opcode=0xFF  (8 bits)
    "11111111",
]
    
    division = [
    # 1) Cargar A, a   (const a → memoria A)
    #    └─ Store R0 → A
    "11000011 0001 0000 00000000 00000000 10101010 10101010",
        #    └─ Load immediate → R0
    "11000010 01 0001 00000000 00000000 00000000 00000000",

    # 2) Cargar B, v   (const v → memoria B)
    "11000011 0010 0000 00000000 00000000 10111011 10111011",
    "11000010 01 0010 00000000 00000000 00000000 00000000",

    # 3) Cargar R3, 0  (inicia cociente R3 = 0)
    "11000010 01 0011 00000000000000000000000000000000",

    # 4) Copiar A, R1  (mem[A] → R1)
    "11000010 10 0001 00000000 00000000 10101010 10101010",

    # 5) Copiar B, R2  (mem[B] → R2)
    "11000010 10 0010 00000000 00000000 10111011 10111011",

    # ----- bucle “inicio” -----
    # 6) inicio:
    # 7) Comparar R1, R2
    "10001010 00 0001 0010",

    # 8) JN fin       (si N=1 saltar a etiqueta fin)
    "11100010 00000000000000000000000011010100",

    # 9) Restar R1, R2
    "10000010 00 0001 0010",

    # 10) Incrementar R3
    "01001000 00 0011",

    # 11) JMP inicio
    "11100000 00000000000000000000000011001111",

    # ----- etiqueta “fin” -----
    # 12) fin:
    # 13) Almacenar R3 → Q   (cociente final en memoria Q)
    "11000011 0011 0000 00000000 00000000 10000000 00000000",

    # 14) Almacenar R1 → X   (resto final en memoria X)
    "11000011 0001 0000 00000000 00000000 11111111 00000000",

    # 15) HALT
    "11111111",
]

    insertionSort = [
    # -------------------------------
    # 1) Inicializar memoria A[]
    # -------------------------------
    # Cargar el valor 5 en R4
    "11000010 01 0100 00000000000000000000000000000101",
    # Almacenar R4 → [0x0000AAAA + 0]
    "11000011 0100 0000 00000000000000001010101010101010",

    # Cargar el valor 1 en R4
    "11000010 01 0100 00000000000000000000000000000001",
    # Almacenar R4 → [0x0000AAAA + 1]
    "11000011 0100 0000 00000000000000001010101010101011",

    # Cargar el valor 7 en R4
    "11000010 01 0100 00000000000000000000000000000111",
    # Almacenar R4 → [0x0000AAAA + 2]
    "11000011 0100 0000 00000000000000001010101010101100",

    # Cargar el valor 6 en R4
    "11000010 01 0100 00000000000000000000000000000110",
    # Almacenar R4 → [0x0000AAAA + 3]
    "11000011 0100 0000 00000000000000001010101010101101",

    # Cargar el valor 4 en R4
    "11000010 01 0100 00000000000000000000000000000100",
    # Almacenar R4 → [0x0000AAAA + 4]
    "11000011 0100 0000 00000000000000001010101010101110",

    # Cargar el valor 0 en R4
    "11000010 01 0100 00000000000000000000000000000000",
    # Almacenar R4 → [0x0000AAAA + 5]
    "11000011 0100 0000 00000000000000001010101010101111",

    # -------------------------------
    # 2) insertionSort(A, n=6)
    # -------------------------------
    # Cargar R1 ← base A (0x0000AAAA)
    "11000010 01 0001 00000000000000001010101010101010",
    # Cargar R2 ← n−1 = 5
    "11000010 01 0010 00000000000000000000000000000101",
    # Cargar R3 ← 1
    "11000010 01 0011 00000000000000000000000000000001",

    # -- etiqueta FOR: --
    # COMP R3,R2
    "10001010 00 0011 0010",
    # JN THEN   (dest = dirección de la instrucción THEN)
    "11100010 00000000 00000000 00000000 11011010",
    # HALT      (si R3 ≥ R2)
    "11111111",

    # -- etiqueta THEN: --
    # Copiar puntero R7 ← R1
    "11000010 00 0111 0001",
    # Sumar R7 ← R7 + R3
    "10000001 00 0111 0011",
    # Cargar R4 ← [R7]
    "11000010 11 0100 0111 00000000000000000000000000000000",

    # Cargar R5 ← R3
    "11000010 00 0101 0011",
    # Restar R5 ← R5 − 1
    "10000010 01 0101 00000000000000000000000000000001",

    # -- etiqueta WHILE: --
    # COMP R5, 0
    "10001010 01 0101 00000000000000000000000000000000",
    # JN END1
    "11100010 00000000 00000000 00000000 11101100",

    # Copiar puntero R7 ← R1 E2
    "11000010 00 0111 0001",
    # Sumar R7 ← R7 + R5 E3
    "10000001 00 0111 0101",
    # Cargar R6 ← [R7] E4
    "11000010 11 0110 0111 00000000000000000000000000000000",

    # COMP R6,R4 E5
    "10001010 00 0110 0100",
    # JN END1 E6
    "11100010 00000000 00000000 00000000 11101100",

    # Sumar R5 ← R5 + 1 E7
    "10000001 01 0101 00000000000000000000000000000001",
    # Copiar puntero R7 ← R1 E8
    "11000010 00 0111 0001",
    # Sumar R7 ← R7 + R5 E9
    "10000001 00 0111 0101",
    # Almacenar [R7] ← R6 EA
    "11000011 11 0110 0111 00000000000000000000000000000000",

    # Restar R5 ← R5 − 2 EB
    "10000010 01 0101 00000000000000000000000000000010",
    # JMP WHILE (DF) EC
    "11100000 00000000 00000000 00000000 11011111",

    # -- etiqueta END1: --
    # Sumar R5 ← R5 + 1 ED
    "10000001 01 0101 00000000000000000000000000000001",
    # Copiar puntero R7 ← R1
    "11000010 00 0111 0001",
    # Sumar R7 ← R7 + R5
    "10000001 00 0111 0101",
    # Almacenar [R7] ← R4
    "11000011 11 0100 0111 00000000000000000000000000000000",

    # Sumar R3 ← R3 + 1
    "10000001 01 0011 00000000000000000000000000000001",
    # JMP FOR (D7)
    "11100000 00000000 00000000 00000000 11010111",
]

    # Carga y arranque
    Cargador.cargar(mem, insertionSort, base_addr=0xC8)
    cpu.PC     = 0xC8
    cpu.reg[1] = 36
    cpu.reg[2] = 24

    print(f"Antes de ejecutar: R1={cpu.reg[1]}, R2={cpu.reg[2]}")
    cpu.ejecutar()
    print(f"Resultado en R1: {cpu.reg[1]}")
