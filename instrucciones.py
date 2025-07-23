class Memoria:
    def __init__(self):
        self.data = {}

    def escribir(self, direccion, valor):
        self.data[direccion] = valor

    def leer(self, direccion):
        return self.data.get(direccion, 0)


class CPU:
    def __init__(self):
        self.reg = [0] * 16  # 16 registros
        self.mem = Memoria()  # memoria integrada
        self.FLAGS = {'Z': 0, 'N': 0}
        self.PC = 0
        self.running = True
        self.instrucciones = Instrucciones(self)

    def ejecutar(self, instruccion, memoria_externa=None):
        """
        Ejecuta una instrucción de 64 bits en binario (int).
        """
        # Si se provee una memoria externa (como en la simulación), se usa.
        if memoria_externa:
            self.mem = memoria_externa

        bit_length = instruccion.bit_length()
        self.instrucciones.ejecutar(instruccion, bit_length)

class Instrucciones:
    def __init__(self, cpu):
        self.cpu = cpu
        self.MASK56 = (1 << 56) - 1
        self.MASK46 = (1 << 46) - 1

    def to_signed(self, val: int, bits: int = 64) -> int:
        """Interpreta val como signed two’s-complement de ‘bits’ bits."""
        sign_bit = 1 << (bits - 1)
        return val - (1 << bits) if (val & sign_bit) else val

    def ejecutar(self, instr: int, bit_len: int):
        pos = bit_len
        if pos < 8:
            raise ValueError(f"Instrucción demasiado corta ({pos} bits)")

        # opcode: 8 bits más significativos
        opcode = instr >> (pos - 8)

        # NOP / HALT (simple-byte)
        if opcode == 0x00:
            return self.nop()
        if opcode == 0xFF:
            return self.halt()

        # Saltos / llamadas: opcode + inmediato
        if opcode in (0xE0, 0xE1, 0xEE, 0xE2, 0xED, 0xD8):
            offset = pos - 8
            dest = instr & ((1 << offset) - 1)
            return getattr(self, {
                0xE0: 'jmp', 0xE1: 'jz', 0xEE: 'jnz',
                0xE2: 'jn', 0xED: 'jnn', 0xD8: 'call'
            }[opcode])(dest)

        # Para C2/C3 extraigo modo
        if opcode in (0xC2, 0xC3):
            modo = (instr >> (pos - 8 - 2)) & 0x3

            # INDIRECTO (modo=3)
            if modo == 3:
                # 8 opcode +2 modo +4 r1 +4 r2 = 18 bits, resto = offset (pos-18)
                r1 = (instr >> (pos - 8 - 2 - 4)) & 0xF
                r2 = (instr >> (pos - 8 - 2 - 4 - 4)) & 0xF
                off = instr & ((1 << (pos - 18)) - 1)
                addr = self.cpu.reg[r2] + off
                if opcode == 0xC2:
                    return self.load_indirect(r1, addr)
                else:
                    return self.store_indirect(r1, addr)

        # Para STORE directo (modo=2 implícito para store)
        if opcode == 0xC3:
            # 8 opcode +4 r1 +4 zeros =16 bits, resto=addr
            r1 = (instr >> (pos - 8 - 4)) & 0xF
            addr = instr & ((1 << (pos - 16)) - 1)
            return self.store_direct(r1, addr)

        # INC/DEC formato corto (14 bits)
        if opcode in (0x48, 0x49):
            # Asegurémonos de tener al menos 14 bits
            if pos < 14:
                raise ValueError(f"Instrucción demasiado corta para INC/DEC ({pos} bits)")
            # Los 4 bits de r1 empiezan justo después del opcode:
            # bits: [opcode(8)] [r1(4)] [--(2)]
            r1 = instr & 0xF

            if opcode == 0x48:
                return self.inc(r1)
            else:  # opcode == 0x49
                return self.dec(r1)

        # Para LOAD directo o inmediato
        # requer al menos 18 bits: opcode+modo+ r1+ r2
        if pos < 18:
            raise ValueError(f"Instrucción demasiado corta para LOAD/ALU ({pos} bits)")
        shift = pos - 8
        modo = (instr >> (shift - 2)) & 0x3
        r1   = (instr >> (shift - 6)) & 0xF
        r2   = (instr >> (shift - 10)) & 0xF
        # campo inmediato sin signo
        imm  = instr & ((1 << (pos - 18)) - 1)

        # Sign-extension de inmediatos (dos complementos) si modo inmediato (modo==1)
        if modo == 1:
            width = pos - 18
            sign_bit = 1 << (width - 1)
            if imm & sign_bit:
                imm = imm - (1 << width)

        # LOAD r1, r2/const/mem
        if opcode == 0xC2:
            return self.load(r1, r2, imm, modo)        

        match opcode:
            case 0xC2:             self.load(r1, r2, imm, modo)
            case 0xC3:             self.store(r1, imm)
            # Aritmética / Comparación
            case 0x81:             self.add(r1, r2, imm, modo)
            case 0x82:             self.sub(r1, r2, imm, modo)
            case 0x83:             self.mul(r1, r2, imm, modo)
            case 0x84:             self.div(r1, r2, imm, modo)
            case 0x8A:             self.comp(r1, r2, imm, modo)

            # Lógica de bits
            case 0x11:  self.and_op(r1, r2, imm, modo)
            case 0x13:  self.or_op (r1, r2, imm, modo)
            case 0x12:  self.xor_op(r1, r2, imm, modo)
            case 0x10:  self.not_op(r1)
            case 0x21:  self.test(r1, r2)

            # E/S
            case 0x90:  self.input(r1)
            case 0x91:  self.output(r1)

            # Stack
            case 0xD0:  self.push(r1)
            case 0xD1:  self.pop(r1)
            case 0xD8:  self.call(dest)
            case 0xD9:  self.ret()
            case 0xD2:  self.load_sp(r1)
            case 0xD3:  self.store_sp(dest)

            # Corrimientos
            case 0x28:  self.shl(r1, r2, imm)
            case 0x29:  self.shr(r1, r2, imm)

            # Inc / Dec
            case 0x48:  self.inc(r1)
            case 0x49:  self.dec(r1)

            # Interrupciones
            case 0xF0:  self.interrupt()
            case 0xF1:  self.return_interrupt()

            case _:
                print(f"Instrucción no implementada: {hex(opcode)}")
                self.cpu.running = False

    def nop(self):
        pass

    def halt(self):
        self.cpu.running = False

    # Saltos
    def jmp(self, dest):        self.cpu.PC = dest
    def jz(self, dest):         self.cpu.PC = dest if self.cpu.FLAGS['Z']==1 else self.cpu.PC
    def jnz(self, dest):        self.cpu.PC = dest if self.cpu.FLAGS['Z']==0 else self.cpu.PC
    def jn(self, dest):         self.cpu.PC = dest if self.cpu.FLAGS['N']==1 else self.cpu.PC
    def jnn(self, dest):        self.cpu.PC = dest if self.cpu.FLAGS['N']==0 else self.cpu.PC

    # ALU
    def add(self, r1, r2, k, modo): res=(self.cpu.reg[r1] + (self.cpu.reg[r2] if modo==0 else k))&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def sub(self, r1, r2, k, modo): res=(self.cpu.reg[r1] - (self.cpu.reg[r2] if modo==0 else k))&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def mul(self, r1, r2, k, modo): res=(self.cpu.reg[r1] * (self.cpu.reg[r2] if modo==0 else k))&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def div(self, r1, r2, k, modo):
        val=(self.cpu.reg[r2] if modo==0 else k)
        if val==0: print("Error: División por cero"); self.cpu.running=False; return
        res=(self.cpu.reg[r1]//val)&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def comp(self, r1, r2, k, modo):
        # lee los valores “en crudo” de registro o inmediato
        v1 = self.cpu.reg[r1]
        v2 = (self.cpu.reg[r2] if modo == 0 else k)
        # conviértelos a signed de 64 bits:
        s1 = self.to_signed(v1)
        s2 = self.to_signed(v2)
        # ahora Z y N según signed
        self.cpu.FLAGS['Z'] = 1 if (s1 == s2) else 0
        self.cpu.FLAGS['N'] = 1 if (s1 <  s2) else 0

    # Lógica
    def and_op(self, r1, r2, k, modo): res=self.cpu.reg[r1]& (self.cpu.reg[r2] if modo==0 else k);self.cpu.reg[r1]=res;self.set_flags(res)
    def or_op (self, r1, r2, k, modo): res=self.cpu.reg[r1]| (self.cpu.reg[r2] if modo==0 else k);self.cpu.reg[r1]=res;self.set_flags(res)
    def xor_op(self, r1, r2, k, modo): res=self.cpu.reg[r1]^ (self.cpu.reg[r2] if modo==0 else k);self.cpu.reg[r1]=res;self.set_flags(res)
    def not_op(self, r1): res=(~self.cpu.reg[r1])&0xFFFFFFFFFFFFFFFF;self.cpu.reg[r1]=res;self.set_flags(res)
    def test(self, r1, r2): res=self.cpu.reg[r1]&self.cpu.reg[r2];self.set_flags(res)

    # E/S
    def input(self, r1): self.cpu.reg[r1]=int(input(f"Entrada R{r1}: "))&0xFFFFFFFFFFFFFFFF
    def output(self, r1): print(f"Salida R{r1}: {self.cpu.reg[r1]}")

    # Stack
    def push(self, r1): sp=15;self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF;self.cpu.mem.escribir(self.cpu.reg[sp],self.cpu.reg[r1])
    def pop(self, r1):  sp=15;self.cpu.reg[r1]=self.cpu.mem.leer(self.cpu.reg[sp]);self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF
    def call(self, dest):sp=15;self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF;self.cpu.mem.escribir(self.cpu.reg[sp],self.cpu.PC);self.cpu.PC=dest
    def ret(self):      sp=15;self.cpu.PC=self.cpu.mem.leer(self.cpu.reg[sp]);self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF

    # Corrimientos
    def shl(self, r1, r2, k): res=(self.cpu.reg[r2]<<k)&0xFFFFFFFFFFFFFFFF;self.cpu.reg[r1]=res;self.set_flags(res)
    def shr(self, r1, r2, k): res=(self.cpu.reg[r2]>>k)&0xFFFFFFFFFFFFFFFF;self.cpu.reg[r1]=res;self.set_flags(res)

    # Inc/Dec
    def inc(self, r1): self.cpu.reg[r1]=(self.cpu.reg[r1]+1)&0xFFFFFFFFFFFFFFFF
    def dec(self, r1): self.cpu.reg[r1]=(self.cpu.reg[r1]-1)&0xFFFFFFFFFFFFFFFF

    # SP
    def store_direct(self, r1, addr):
            val = self.cpu.reg[r1]
            print(f"DEBUG: store_direct R{r1} -> mem[{hex(addr)}] = {val}")
            self.cpu.mem.escribir(addr, val)
        # self.cpu.mem.escribir(addr, self.cpu.reg[r1])

    def load(self, r1, r2, k, modo):
        if modo == 0:
            self.cpu.reg[r1] = self.cpu.reg[r2]
        elif modo == 1:
            self.cpu.reg[r1] = k
        elif modo == 2:
            self.cpu.reg[r1] = self.cpu.mem.leer(k)
        else:
            raise ValueError(f"Modo LOAD inválido: {modo}")

    def store_indirect(self, r1, addr):
        # self.cpu.mem.escribir(addr, self.cpu.reg[r1])
        val = self.cpu.reg[r1]
        print(f"DEBUG: store_indirect R{r1} -> mem[{hex(addr)}] = {val}")
        self.cpu.mem.escribir(addr, val)

    def load_indirect(self, r1, addr):
        self.cpu.reg[r1] = self.cpu.mem.leer(addr)

    # Interrupciones
    def interrupt(self):sp=15;self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF;self.cpu.mem.escribir(self.cpu.reg[sp],self.cpu.PC);self.cpu.PC=0x1000
    def return_interrupt(self):sp=15;self.cpu.PC=self.cpu.mem.leer(self.cpu.reg[sp]);self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF

    def set_flags(self, result):
        self.cpu.FLAGS['Z'] = 1 if result == 0 else 0
        self.cpu.FLAGS['N'] = 1 if (result >> 63) & 1 else 0
