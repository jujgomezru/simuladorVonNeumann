class Instrucciones:
    def __init__(self, cpu):
        self.cpu = cpu
        self.MASK56 = (1 << 56) - 1
        self.MASK46 = (1 << 46) - 1

    def ejecutar(self, instr: int, bit_len: int):
        pos = bit_len
        if pos < 8:
            raise ValueError(f"Instrucción demasiado corta ({pos} bits)")

        # 1) Extraigo opcode (los 8 bits más significativos)
        opcode = instr >> (pos - 8)

        # 2) Single-byte ops: NOP y HALT
        if opcode in (0x00, 0xFF):
            if   opcode == 0x00:  return self.nop()
            elif opcode == 0xFF:  return self.halt()

        # 3) Saltos y llamadas: sólo opcode + campo inmediato
        JUMPS = {0xE0:'jmp', 0xE1:'jz', 0xEE:'jnz', 0xE2:'jn', 0xED:'jnn', 0xD8:'call'}
        if opcode in JUMPS:
            imm_size = pos - 8
            dest = instr & ((1 << imm_size) - 1)
            getattr(self, JUMPS[opcode])(dest)
            return

        if opcode == 0xC3:
        # pos = bit_len
        # extraigo r1 de los 4 bits que siguen al opcode
            r1   = (instr >> (pos - 8 - 4)) & 0xF
            # la dirección ocupa el resto: pos - (8+4+4) bits = pos - 16
            addr = instr & ((1 << (pos - 16)) - 1)
            return self.store(r1, addr)

        

        if opcode in (0x48, 0x49):
            if pos < 14:
                raise ValueError(f"INC/DEC demasiado corta ({pos} bits)")
            shift = pos - 8              # 6 bits: [modo2][r1-4]
            # modo = (instr >> (shift - 2)) & 0x3   # siempre 0
            r1   = (instr >> (shift - 2 - 4)) & 0xF
            if opcode == 0x48:
                return self.inc(r1)
            else:
                return self.dec(r1)

        # 4) Resto de instrucciones: necesitan modo (2b), r1(4b), r2(4b), y luego k = resto (inmediato)
        if pos < 18:
            raise ValueError(f"Instrucción demasiado corta para modo+regs ({pos} bits)")

        # 8 bits opcode  + 2 bits modo + 4 bits r1 + 4 bits r2 = 18 bits
        shift = pos - 8
        modo = (instr >> (shift - 2)) & 0x3
        r1   = (instr >> (shift - 2 - 4)) & 0xF
        r2   = (instr >> (shift - 2 - 4 - 4)) & 0xF

        imm_size = pos - 18
        k = instr & ((1 << imm_size) - 1)

        match opcode:
            case 0xC2:             self.load(r1, r2, k, modo)
            case 0xC3:             self.store(r1, k)
            # Aritmética / Comparación
            case 0x81:             self.add(r1, r2, k, modo)
            case 0x82:             self.sub(r1, r2, k, modo)
            case 0x83:             self.mul(r1, r2, k, modo)
            case 0x84:             self.div(r1, r2, k, modo)
            case 0x8A:             self.comp(r1, r2, k, modo)

            # Lógica de bits
            case 0x11:  self.and_op(r1, r2, k, modo)
            case 0x13:  self.or_op (r1, r2, k, modo)
            case 0x12:  self.xor_op(r1, r2, k, modo)
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
            case 0x28:  self.shl(r1, r2, k)
            case 0x29:  self.shr(r1, r2, k)

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

    # Carga/Almacena
    def load(self, r1, r2, k, modo):
        if modo==0:    self.cpu.reg[r1]=self.cpu.reg[r2]
        elif modo==1:  self.cpu.reg[r1]=k
        elif modo==2:  self.cpu.reg[r1]=self.cpu.mem.leer(k)
        else:         raise ValueError(f"Modo load inválido: {modo}")
    def store(self, r1, addr):  self.cpu.mem.escribir(addr,self.cpu.reg[r1])

    # ALU
    def add(self, r1, r2, k, modo): res=(self.cpu.reg[r1] + (self.cpu.reg[r2] if modo==0 else k))&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def sub(self, r1, r2, k, modo): res=(self.cpu.reg[r1] - (self.cpu.reg[r2] if modo==0 else k))&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def mul(self, r1, r2, k, modo): res=(self.cpu.reg[r1] * (self.cpu.reg[r2] if modo==0 else k))&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def div(self, r1, r2, k, modo):
        val=(self.cpu.reg[r2] if modo==0 else k)
        if val==0: print("Error: División por cero"); self.cpu.running=False; return
        res=(self.cpu.reg[r1]//val)&0xFFFFFFFFFFFFFFFF; self.cpu.reg[r1]=res; self.set_flags(res)
    def comp(self, r1, r2, k, modo):
        v1=self.cpu.reg[r1];v2=(self.cpu.reg[r2] if modo==0 else k)
        self.cpu.FLAGS['Z']=1 if v1==v2 else 0; self.cpu.FLAGS['N']=1 if v1<v2 else 0

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
    def load_sp(self, r1):self.cpu.reg[r1]=self.cpu.reg[15]
    def store_sp(self, addr):self.cpu.mem.escribir(addr,self.cpu.reg[15])

    # Interrupciones
    def interrupt(self):sp=15;self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF;self.cpu.mem.escribir(self.cpu.reg[sp],self.cpu.PC);self.cpu.PC=0x1000
    def return_interrupt(self):sp=15;self.cpu.PC=self.cpu.mem.leer(self.cpu.reg[sp]);self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF

    def set_flags(self, result):
        self.cpu.FLAGS['Z'] = 1 if result == 0 else 0
        self.cpu.FLAGS['N'] = 1 if (result >> 63) & 1 else 0
