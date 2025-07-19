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
