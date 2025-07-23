from instrucciones import CPU, Memoria

def run_instructions(instrs, base=0x0):
    cpu = CPU()
    mem = Memoria()

    for i, instr in enumerate(instrs):
        mem.escribir(base + i, instr)

    pc = base
    cpu.pc = pc

    while True:
        instr = mem.leer(cpu.pc)
        if instr == "HALT":
            break
        cpu.ejecutar(instr, mem)
        cpu.pc += 1

    return cpu, mem
