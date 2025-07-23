#!/usr/bin/env python3
"""
Simple Assembler for the Simulated CPU
"""

import sys
import re

# Instruction metadata
INSTR = {
    'NOP':   {'code': 0x00, 'mode': None, 'imm_bits': 0},
    'HALT':  {'code': 0xFF, 'mode': None, 'imm_bits': 0},
    'MOV':   {'code': 0xC2, 'mode': 0,    'imm_bits': 0},
    'LOADK': {'code': 0xC2, 'mode': 1,    'imm_bits': 32},
    'LOADM': {'code': 0xC2, 'mode': 2,    'imm_bits': 32},
    'LOADI': {'code': 0xC2, 'mode': 3,    'imm_bits': 4},
    'STOREM':{'code': 0xC3, 'mode': 2,    'imm_bits': 32},
    'STOREI':{'code': 0xC3, 'mode': 3,    'imm_bits': 4},
    'ADD':   {'code': 0x81, 'mode': 0,    'imm_bits': 0},
    'SUB':   {'code': 0x82, 'mode': 0,    'imm_bits': 0},
    'MUL':   {'code': 0x83, 'mode': 0,    'imm_bits': 0},
    'DIV':   {'code': 0x84, 'mode': 0,    'imm_bits': 0},
    'ADDI':  {'code': 0x81, 'mode': 1,    'imm_bits': 32},
    'SUBI':  {'code': 0x82, 'mode': 1,    'imm_bits': 32},
    'MULI':  {'code': 0x83, 'mode': 1,    'imm_bits': 32},
    'DIVI':  {'code': 0x84, 'mode': 1,    'imm_bits': 32},
    'CMP':   {'code': 0x8A, 'mode': 0,    'imm_bits': 0},
    'CMPI':  {'code': 0x8A, 'mode': 1,    'imm_bits': 32},
    'AND':   {'code': 0x11, 'mode': 0,    'imm_bits': 0},
    'OR':    {'code': 0x13, 'mode': 0,    'imm_bits': 0},
    'XOR':   {'code': 0x12, 'mode': 0,    'imm_bits': 0},
    'NOT':   {'code': 0x10, 'mode': None, 'imm_bits': 0},
    'JMP':   {'code': 0xE0, 'mode': None, 'imm_bits': 32},
    'JZ':    {'code': 0xE1, 'mode': None, 'imm_bits': 32},
    'JNZ':   {'code': 0xEE, 'mode': None, 'imm_bits': 32},
    'JN':    {'code': 0xE2, 'mode': None, 'imm_bits': 32},
    'JNN':   {'code': 0xED, 'mode': None, 'imm_bits': 32},
    'CALL':  {'code': 0xD8, 'mode': None, 'imm_bits': 32},
    'RET':   {'code': 0xD9, 'mode': None, 'imm_bits': 0},
    'PUSH':  {'code': 0xD0, 'mode': 0,    'imm_bits': 0},
    'POP':   {'code': 0xD1, 'mode': 0,    'imm_bits': 0},
    'INT':   {'code': 0xF0, 'mode': None, 'imm_bits': 0},
    'IRET':  {'code': 0xF1, 'mode': None, 'imm_bits': 0},
}

def parse_register(tok: str) -> int:
    if not tok.upper().startswith('R'):
        raise ValueError(f"Invalid register '{tok}'")
    num = int(tok[1:], 0)
    if not (0 <= num < 16):
        raise ValueError(f"Register out of range: {tok}")
    return num

def preprocess_lines(lines):
    cleaned = []
    for line in lines:
        line = re.sub(r";.*", "", line).strip()
        if line:
            cleaned.append(line)
    return cleaned

def assemble_lines(lines):
    lines = preprocess_lines(lines)
    for idx, ln in enumerate(lines, start=1):
        print(f"💡 ensamblando línea: {ln}")

    # Primera pasada: etiquetas
    labels = {}
    addr = 0
    for ln in lines:
        m = re.match(r'^(\w+):$', ln)
        if m:
            labels[m.group(1)] = addr
        else:
            addr += 1

    # Segunda pasada: generación de binario
    output = []
    for idx, ln in enumerate(lines, start=1):
        if re.match(r'^(\w+):$', ln):
            continue
        try:
            parts = re.split(r'[ ,]+', ln)
            mnem = parts[0].upper()
            if mnem == 'INC':
                mnem = 'ADDI'
                parts = ['ADDI', parts[1], '1']
            elif mnem == 'DEC':
                mnem = 'SUBI'
                parts = ['SUBI', parts[1], '1']

            if mnem not in INSTR:
                raise ValueError(f"Unknown mnemonic '{mnem}'")
            info = INSTR[mnem]
            code, mode, imm_bits = info['code'], info['mode'], info['imm_bits']
            bits = format(code, '08b')
            if mode is not None:
                bits += format(mode, '02b')

            if mnem in ('NOP','HALT','INT','IRET','RET'):
                pass
            elif mnem in ('PUSH','POP','NOT'):
                r = parse_register(parts[1])
                if mode is None:
                    bits += '00'
                bits += format(r, '04b')
            elif mnem in ('MOV','ADD','SUB','MUL','DIV','CMP','AND','OR','XOR'):
                r1, r2 = parse_register(parts[1]), parse_register(parts[2])
                bits += format(r1, '04b') + format(r2, '04b')
            elif mnem in ('ADDI','SUBI','MULI','DIVI','CMPI','LOADK','LOADM','STOREM'):
                r = parse_register(parts[1])
                val = parts[2]
                imm = labels[val] if val in labels else int(val, 0)
                bits += format(r, '04b') + format(imm & ((1 << imm_bits) - 1), f'0{imm_bits}b')
            elif mnem in ('LOADI','STOREI'):
                r1, r2 = parse_register(parts[1]), parse_register(parts[2])
                bits += format(r1, '04b') + format(r2, '04b')
            elif mnem in ('JMP','JZ','JNZ','JN','JNN','CALL'):
                tgt = parts[1]
                addr = labels[tgt] if tgt in labels else int(tgt, 0)
                bits += format(addr & ((1 << imm_bits) - 1), f'0{imm_bits}b')
            else:
                raise ValueError(f"Unsupported operands for '{mnem}'")

            if len(bits) < 8:
                raise ValueError(f"Instrucción inválida: '{ln}' genera solo {len(bits)} bits")
            bin_instr = int(bits, 2)
            output.append(bin_instr)
        except Exception as e:
            raise ValueError(f"❌ Error en línea {idx}: \"{ln}\" -> {e}")

    print("🧪 Instrucciones binarias generadas:", [(i, instr, f"{instr:b}", f"{instr.bit_length()} bits") for i, instr in enumerate(output, start=1)])
    return output

def assemble_file(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    return assemble_lines(lines)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python assembler.py <archivo_fuente>")
        sys.exit(1)
    binary = assemble_file(sys.argv[1])
    for b in binary:
        print(b)
