#!/usr/bin/env python3
"""
Simple Assembler for the Simulated CPU

Provides a library function to assemble pseudo-assembly into binary strings,
including INC/DEC pseudoinstructions, and a CLI entrypoint.

Usage as script:
  python assembler.py <source.txt>

API for integration:
  from assembler import assemble_lines
  bin_list = assemble_lines(source_lines)
"""
import sys
import re

# Instruction metadata
INSTR = {
    'NOP':   {'code':0x00, 'mode':None, 'imm_bits':0},
    'HALT':  {'code':0xFF, 'mode':None, 'imm_bits':0},
    'MOV':   {'code':0xC2, 'mode':0,    'imm_bits':0},
    'LOADK': {'code':0xC2, 'mode':1,    'imm_bits':32},
    'LOADM': {'code':0xC2, 'mode':2,    'imm_bits':32},
    'LOADI': {'code':0xC2, 'mode':3,    'imm_bits':4},
    'STOREM':{'code':0xC3, 'mode':2,    'imm_bits':32},
    'STOREI':{'code':0xC3, 'mode':3,    'imm_bits':4},
    'ADD':   {'code':0x81, 'mode':0,    'imm_bits':0},
    'SUB':   {'code':0x82, 'mode':0,    'imm_bits':0},
    'MUL':   {'code':0x83, 'mode':0,    'imm_bits':0},
    'DIV':   {'code':0x84, 'mode':0,    'imm_bits':0},
    'ADDI':  {'code':0x81, 'mode':1,    'imm_bits':32},
    'SUBI':  {'code':0x82, 'mode':1,    'imm_bits':32},
    'MULI':  {'code':0x83, 'mode':1,    'imm_bits':32},
    'DIVI':  {'code':0x84, 'mode':1,    'imm_bits':32},
    'CMP':   {'code':0x8A, 'mode':0,    'imm_bits':0},
    'CMPI':  {'code':0x8A, 'mode':1,    'imm_bits':32},
    'AND':   {'code':0x11, 'mode':0,    'imm_bits':0},
    'OR':    {'code':0x13, 'mode':0,    'imm_bits':0},
    'XOR':   {'code':0x12, 'mode':0,    'imm_bits':0},
    'NOT':   {'code':0x10, 'mode':None, 'imm_bits':0},
    'JMP':   {'code':0xE0, 'mode':None, 'imm_bits':32},
    'JZ':    {'code':0xE1, 'mode':None, 'imm_bits':32},
    'JNZ':   {'code':0xEE, 'mode':None, 'imm_bits':32},
    'JN':    {'code':0xE2, 'mode':None, 'imm_bits':32},
    'JNN':   {'code':0xED, 'mode':None, 'imm_bits':32},
    'CALL':  {'code':0xD8, 'mode':None, 'imm_bits':32},
    'RET':   {'code':0xD9, 'mode':None, 'imm_bits':0},
    'PUSH':  {'code':0xD0, 'mode':0,    'imm_bits':0},
    'POP':   {'code':0xD1, 'mode':0,    'imm_bits':0},
    'INT':   {'code':0xF0, 'mode':None, 'imm_bits':0},
    'IRET':  {'code':0xF1, 'mode':None, 'imm_bits':0},
}

# Helpers
def parse_register(tok: str) -> int:
    if not tok.upper().startswith('R'):
        raise ValueError(f"Invalid register '{tok}'")
    num = int(tok[1:], 0)
    if not (0 <= num < 16):
        raise ValueError(f"Register out of range: {tok}")
    return num


def preprocess_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for ln in lines:
        code = re.split(r'[;#]', ln, 1)[0].strip()
        if code:
            cleaned.append(code)
    return cleaned


def assemble_lines(raw_lines: list[str]) -> list[str]:
    """
    Given list of source lines (pseudo-assembly), return list of binary strings.
    Supports INC and DEC as pseudoinstructions.
    """
    lines = preprocess_lines(raw_lines)

    # First pass: resolve labels
    labels: dict[str,int] = {}
    addr = 0
    for ln in lines:
        m = re.match(r'^(\w+):$', ln)
        if m:
            labels[m.group(1)] = addr
        else:
            addr += 1

    # Second pass: emit binary
    output: list[str] = []
    for idx, ln in enumerate(lines, start=1):
        if re.match(r'^(\w+):$', ln):
            continue
        try:
            parts = re.split(r'[ ,]+', ln)
            mnem = parts[0].upper()
            # Handle pseudoinstructions
            if mnem == 'INC':
                mnem = 'ADDI'
                parts = ['ADDI', parts[1], '1']
            elif mnem == 'DEC':
                mnem = 'SUBI'
                parts = ['SUBI', parts[1], '1']

            if mnem not in INSTR:
                raise ValueError(f"Unknown mnemonic '{mnem}'")
            info = INSTR[mnem]
            code = info['code']; mode = info['mode']; imm_bits = info['imm_bits']

            bits = format(code, '08b')
            if mode is not None:
                bits += format(mode, '02b')

            # operand encoding
            if mnem in ('NOP','HALT','INT','IRET','RET'):
                pass
            elif mnem in ('PUSH','POP','NOT'):
                r = parse_register(parts[1])
                if mode is None: bits += '00'
                bits += format(r, '04b')
            elif mnem in ('MOV','ADD','SUB','MUL','DIV','CMP','AND','OR','XOR'):
                r1,r2 = parse_register(parts[1]), parse_register(parts[2])
                bits += format(r1,'04b')+format(r2,'04b')
            elif mnem in ('ADDI','SUBI','MULI','DIVI','CMPI','LOADK','LOADM','STOREM'):
                r = parse_register(parts[1])
                val = parts[2]
                imm = labels[val] if val in labels else int(val,0)
                bits += format(r,'04b') + format(imm & ((1<<imm_bits)-1), f'0{imm_bits}b')
            elif mnem in ('LOADI','STOREI'):
                r1,r2 = parse_register(parts[1]), parse_register(parts[2])
                bits += format(r1,'04b')+format(r2,'04b')
            elif mnem in ('JMP','JZ','JNZ','JN','JNN','CALL'):
                tgt = parts[1]
                addr = labels[tgt] if tgt in labels else int(tgt,0)
                bits += format(addr & ((1<<imm_bits)-1), f'0{imm_bits}b')
            else:
                raise ValueError(f"Unsupported operands for '{mnem}'")
            output.append(bits)
        except ValueError as e:
            raise ValueError(f"Error en línea {idx}: \"{ln}\" -> {e}")
    return output


def assemble_file(path: str) -> list[str]:
    with open(path,'r',encoding='utf-8') as f:
        raw = f.read().splitlines()
    return assemble_lines(raw)

if __name__ == '__main__':
    if len(sys.argv)!=2:
        print("Usage: python assembler.py <source.txt>")
        sys.exit(1)
    for b in assemble_file(sys.argv[1]):
        print(b)
