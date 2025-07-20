from assembler import ensamblar

def link_and_load(programa, base):

    from main import Memoria

    mem = Memoria()
    pos = base
    for word, bits, reloc in programa:
        # Si ya es una tupla (word,bits), lo dejamos; si no, lo empaquetamos
        if isinstance(word, tuple) and isinstance(word[0], int):
            mem.escribir(pos, word)
        else:
            mem.escribir(pos, (word, bits))
        pos += 1
    return mem



if __name__ == '__main__':
    import sys
    from preprocessor import Preprocessor
    from assembler import ensamblar 
    src, base = sys.argv[1], int(sys.argv[2], 0)
    source = Preprocessor().process_file(src)
    program = ensamblar(source)
    mem = link_and_load(program, base)
    print(f"Cargado desde {hex(base)}")