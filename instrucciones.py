class Instrucciones:
    def __init__(self, cpu):
        self.cpu = cpu

    def to_signed(self, val: int, bits: int) -> int:
        sign_bit = 1 << (bits - 1)
        return val - (1 << bits) if (val & sign_bit) else val

    def ejecutar(self, instr: int, bit_len: int):
        if bit_len == 8:
            opcode = instr & 0xFF
            if opcode == 0x00:
                return self.nop()
            if opcode == 0xFF:
                return self.halt()
            raise ValueError(f"Opcode de 8 bits inválido: {hex(opcode)}")

        # 64‑bits
        opcode = (instr >> 56) & 0xFF
        mode   = (instr >> 54) & 0x3
        r1     = (instr >> 50) & 0xF
        r2     = (instr >> 46) & 0xF
        imm    = instr & ((1 << 46) - 1)
        if mode == 1:
            imm = self.to_signed(imm, 46)

        # Dispatch
        if opcode == 0xC2:        return self.load(r1, r2, imm, mode)
        if opcode == 0xC3:        return self.store_direct(r1, imm)
        if opcode == 0x81:        return self.add(r1, r2, imm, mode)
        if opcode == 0x82:        return self.sub(r1, r2, imm, mode)
        if opcode == 0x83:        return self.mul(r1, r2, imm, mode)
        if opcode == 0x84:        return self.div(r1, r2, imm, mode)
        if opcode == 0x8A:        return self.comp(r1, r2, imm, mode)
        if opcode == 0x48:        return self.inc(r1)
        if opcode == 0x49:        return self.dec(r1)
        if opcode == 0x90:        return self.input(r1)
        if opcode == 0x91:        return self.output(r1)
        if opcode in (0xE0,0xE1,0xEE,0xE2,0xED):
            return {
                0xE0: self.jmp, 0xE1: self.jz, 0xEE: self.jnz,
                0xE2: self.jn, 0xED: self.jnn
            }[opcode](imm)
        if opcode == 0xD8:        return self.call(imm)
        if opcode == 0xD9:        return self.ret()
        if opcode == 0xD0:        return self.push(r1)
        if opcode == 0xD1:        return self.pop(r1)
        if opcode == 0x28:        return self.shl(r1, r2, imm)
        if opcode == 0x29:        return self.shr(r1, r2, imm)
        if opcode == 0xF0:        return self.interrupt()
        if opcode == 0xF1:        return self.return_interrupt()

        print(f"Opcode no implementado: {hex(opcode)}")
        self.cpu.running = False

    def nop(self): pass
    def halt(self): self.cpu.running = False

    # LOAD
    def load(self, r1, r2, k, mode):
        if mode == 0:
            val = self.cpu.reg[r2]
        elif mode == 1:
            val = k
        else:
            val = self.cpu.mem.leer(k)
        self.cpu.reg[r1] = val
        print(f"[LOAD] R{r1} <- {val}")

    # STORE
    def store_direct(self, r1, addr):
        val = self.cpu.reg[r1]
        self.cpu.mem.escribir(addr, val)
        print(f"[STORE] Mem[{hex(addr)}] <- {val}")

    # ALU
    def add(self, r1, r2, k, mode):
        op2 = self.cpu.reg[r2] if mode==0 else k
        res = (self.cpu.reg[r1] + op2) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        print(f"[ADD] R{r1} <- {res}")
        self.set_flags(res)

    def sub(self, r1, r2, k, mode):
        op2 = self.cpu.reg[r2] if mode==0 else k
        res = (self.cpu.reg[r1] - op2) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        print(f"[SUB] R{r1} <- {res}")
        self.set_flags(res)

    def mul(self, r1, r2, k, mode):
        op2 = self.cpu.reg[r2] if mode==0 else k
        res = (self.cpu.reg[r1] * op2) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        print(f"[MUL] R{r1} <- {res}")
        self.set_flags(res)

    def div(self, r1, r2, k, mode):
        op2 = self.cpu.reg[r2] if mode==0 else k
        if op2==0:
            print("Error: División por cero"); self.cpu.running=False; return
        res = (self.cpu.reg[r1] // op2) & 0xFFFFFFFFFFFFFFFF
        self.cpu.reg[r1] = res
        print(f"[DIV] R{r1} <- {res}")
        self.set_flags(res)

    def comp(self, r1, r2, k, mode):
        v1=self.cpu.reg[r1]; v2=self.cpu.reg[r2] if mode==0 else k
        s1=self.to_signed(v1,64); s2=self.to_signed(v2,64)
        self.cpu.FLAGS['Z']=int(s1==s2); self.cpu.FLAGS['N']=int(s1<s2)
        print(f"[COMP] Z={self.cpu.FLAGS['Z']} N={self.cpu.FLAGS['N']}")

    # Inc/Dec, I/O, etc...
    def inc(self, r1): self.cpu.reg[r1]=(self.cpu.reg[r1]+1)&0xFFFFFFFFFFFFFFFF
    def dec(self, r1): self.cpu.reg[r1]=(self.cpu.reg[r1]-1)&0xFFFFFFFFFFFFFFFF
    def input(self, r1): self.cpu.reg[r1]=int(input(f"Entrada R{r1}: "))&0xFFFFFFFFFFFFFFFF
    def output(self, r1): print(f"Salida R{r1}: {self.cpu.reg[r1]}")
    def push(self, r1):
        sp=15; self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF
        self.cpu.mem.escribir(self.cpu.reg[sp], self.cpu.reg[r1])
    def pop(self, r1):
        sp=15; self.cpu.reg[r1]=self.cpu.mem.leer(self.cpu.reg[sp])
        self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF
    def jmp(self,d): self.cpu.PC=d
    def jz(self,d):  self.cpu.PC=d if self.cpu.FLAGS['Z'] else self.cpu.PC
    def jnz(self,d): self.cpu.PC=d if not self.cpu.FLAGS['Z'] else self.cpu.PC
    def jn(self,d):  self.cpu.PC=d if self.cpu.FLAGS['N'] else self.cpu.PC
    def jnn(self,d): self.cpu.PC=d if not self.cpu.FLAGS['N'] else self.cpu.PC
    def call(self, d):
        sp=15; self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF
        self.cpu.mem.escribir(self.cpu.reg[sp], self.cpu.PC); self.cpu.PC=d
    def ret(self):
        sp=15; self.cpu.PC=self.cpu.mem.leer(self.cpu.reg[sp])
        self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF
    def shl(self,r1,r2,k):
        res=(self.cpu.reg[r2]<<k)&0xFFFFFFFFFFFFFFFF;self.cpu.reg[r1]=res;self.set_flags(res)
    def shr(self,r1,r2,k):
        res=(self.cpu.reg[r2]>>k)&0xFFFFFFFFFFFFFFFF;self.cpu.reg[r1]=res;self.set_flags(res)
    def interrupt(self):
        sp=15; self.cpu.reg[sp]=(self.cpu.reg[sp]-1)&0xFFFFFFFFFFFFFFFF
        self.cpu.mem.escribir(self.cpu.reg[sp], self.cpu.PC); self.cpu.PC=0x1000
    def return_interrupt(self):
        sp=15; self.cpu.PC=self.cpu.mem.leer(self.cpu.reg[sp])
        self.cpu.reg[sp]=(self.cpu.reg[sp]+1)&0xFFFFFFFFFFFFFFFF

    def set_flags(self, result):
        self.cpu.FLAGS['Z'] = int(result == 0)
        self.cpu.FLAGS['N'] = (result >> 63) & 1
