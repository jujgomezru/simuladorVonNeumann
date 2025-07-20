<<<<<<< HEAD
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
=======
import re

OPTAB = {
    'ADD':   0x81,
    'SUB':   0x82,
    'MUL':   0x83,
    'DIV':   0x84,
    'LOAD':  0xC2,
    'STORE': 0xC3,
    'COMP':  0x8A,
    'JMP':   0xE0,
    'JZ':    0xE1,
    'JNZ':   0xEE,
    'JN':    0xE2,
    'JNN':   0xED,
    'CALL':  0xD8,
    'HALT':  0xFF
}

def ensamblar(source: str):
    output = []
    locctr = 0

    for raw in source.splitlines():
        line = raw.split(';',1)[0].strip()
        if not line:
            continue

        parts = [tok for tok in re.split(r'[\s,]+', line) if tok]
        mnem = parts[0].upper()

        if mnem == 'HALT':
            output.append((0xFF, 8, False))
            locctr += 1
            continue

        if mnem in ('LOAD','STORE','ADD','SUB','MUL','DIV','COMP'):
            r1_tok = parts[1]
            op2_tok = parts[2]

            # registro destino
            if not r1_tok.upper().startswith('R'):
                raise SyntaxError(f"Operando 1 no es registro: {r1_tok}")
            r1 = int(r1_tok[1:])

            # caso reg, reg
            if op2_tok.upper().startswith('R'):
                r2 = int(op2_tok[1:])
                mode = 0
                imm = 0

            else:
                # inmediato o dirección
                if op2_tok.lower().startswith('0x'):
                    num = int(op2_tok, 16)
                else:
                    num = int(op2_tok)
                imm = num & ((1<<46)-1)
                mode = 2 if mnem == 'STORE' else 1
                r2 = 0

            opcode = OPTAB[mnem]
            word = (
                (opcode << 56) |
                (mode   << 54) |
                (r1     << 50) |
                (r2     << 46) |
                imm
            )
            bits = 64

            # debug
            r1_e = (word >> 50) & 0xF
            r2_e = (word >> 46) & 0xF
            mode_e = (word >> 54) & 0x3
            print(f"[ASM] {mnem} R{r1},{op2_tok} → mode={mode_e}, r1={r1_e}, r2={r2_e}")

            output.append((word, bits, False))
            locctr += 1
            continue

        if mnem in ('JMP', 'JZ', 'JNZ', 'JN', 'JNN', 'CALL'):
            target = parts[1]
            dest = int(target, 16) if target.startswith("0x") else int(target)
            opcode = OPTAB[mnem]
            word = (opcode << 56) | (dest & ((1 << 56) - 1))
            output.append((word, 64, False))
            locctr += 1
            continue

        raise SyntaxError(f"Instrucción no reconocida: {mnem}")

    return output
>>>>>>> a3a9be74e16a941174d6cd646f00136567cfc639
