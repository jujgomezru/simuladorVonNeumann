class Instrucciones:
    def __init__(self, cpu):
        self.cpu = cpu

    def ejecutar(self, instruccion):
        opcode = instruccion & 0xFF
        modo = (instruccion >> 8) & 0xF
        r1 = (instruccion >> 12) & 0xF
        r2 = (instruccion >> 16) & 0xF
        constante = (instruccion >> 32) & 0xFFFFFFFF

        match opcode:
            case 0x00: self.nop()
            case 0x81: self.add(r1, r2, constante, modo)
            case 0x82: self.sub(r1, r2, constante, modo)
            case 0x83: self.mul(r1, r2, constante, modo)
            case 0x84: self.div(r1, r2, constante, modo)
            case 0x8A: self.comp(r1, r2, constante, modo)
            case 0xC2: self.load(r1, r2, constante, modo)
            case 0xC3: self.store(r1, r2, constante, modo)
            case 0xE0: self.jmp(constante)
            case 0xE1: self.jz(constante)
            case 0xE2: self.jn(constante)
            case 0xED: self.jnn(constante)
            case 0xEE: self.jnz(constante)
            case 0xFF: self.halt()
            case _: print(f"Instrucción no implementada: {hex(opcode)}"); self.cpu.running = False

    def nop(self):
        pass

    def halt(self):
        self.cpu.running = False

    def add(self, r1, r2, k, modo):
        val = k if modo == 0 else self.cpu.reg[r2]
        res = (self.cpu.reg[r1] + val) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        self.set_flags(res)

    def sub(self, r1, r2, k, modo):
        val = k if modo == 0 else self.cpu.reg[r2]
        res = (self.cpu.reg[r1] - val) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        self.set_flags(res)

    def mul(self, r1, r2, k, modo):
        val = k if modo == 0 else self.cpu.reg[r2]
        res = (self.cpu.reg[r1] * val) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        self.set_flags(res)

    def div(self, r1, r2, k, modo):
        val = k if modo == 0 else self.cpu.reg[r2]
        if val == 0:
            print("Error: División por cero")
            self.cpu.running = False
            return
        res = (self.cpu.reg[r1] // val) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        self.set_flags(res)

    def comp(self, r1, r2, k, modo):
        val = k if modo == 0 else self.cpu.reg[r2]
        res = (self.cpu.reg[r1] - val) & 0xFFFFFFFFFFFFFFFF
        self.set_flags(res)

    def load(self, r1, r2, k, modo):
        match modo:
            case 0: self.cpu.reg[r1] = k
            case 1: self.cpu.reg[r1] = self.cpu.reg[r2]
            case 2: self.cpu.reg[r1] = self.cpu.mem.leer(k)
            case 3: self.cpu.reg[r1] = self.cpu.mem.leer(k + self.cpu.reg[r2])

    def store(self, r1, r2, k, modo):
        match modo:
            case 2: self.cpu.mem.escribir(k, self.cpu.reg[r1])
            case 3: self.cpu.mem.escribir(k + self.cpu.reg[r2], self.cpu.reg[r1])

    def jmp(self, dest):
        self.cpu.PC = dest

    def jz(self, dest):
        if self.cpu.FLAGS['Z'] == 1:
            self.cpu.PC = dest

    def jnz(self, dest):
        if self.cpu.FLAGS['Z'] == 0:
            self.cpu.PC = dest

    def jn(self, dest):
        if self.cpu.FLAGS['N'] == 1:
            self.cpu.PC = dest

    def jnn(self, dest):
        if self.cpu.FLAGS['N'] == 0:
            self.cpu.PC = dest

    def set_flags(self, result):
        self.cpu.FLAGS['Z'] = 1 if result == 0 else 0
        self.cpu.FLAGS['N'] = 1 if (result >> 63) & 1 else 0
        # Simples, se puede extender para C y V según se necesite