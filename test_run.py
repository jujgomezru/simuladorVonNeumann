from main import run_assembly
from preprocessor import Preprocessor
from assembler import ensamblar
from linker_loader import link_and_load
from main import Memoria, CPU

# --- Cargar manualmente, sin ejecutar ---
source = Preprocessor().process_file('program.asm')
program = ensamblar(source)
mem = link_and_load(program, base=0x100)

# Mostrar contenido real de la memoria ANTES de ejecutar
print("\n[Memoria cargada]")
for i in range(0x100, 0x106):
    palabra = mem.leer(i)
    print(f"Mem[{hex(i)}] =", palabra)

# Ejecutar por separado
cpu = CPU(mem)
cpu.PC = 0x100
cpu.ejecutar(max_instrucciones=50)

# Mostrar resultados
print("\n[Registros finales]")
print("R1 =", cpu.reg[1])
print("R2 =", cpu.reg[2])
print("Mem[0x200] =", mem.leer(0x200))