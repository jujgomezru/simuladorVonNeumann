from lexer_1 import lexer
from parser_2 import parser, global_bigraph
from bigraph import BigraphCompiler
from assembler import preprocess_lines


def compile_high_level_code(source_code: str) -> list[str]:
    try:
        print("🔍 Paso 1: Compilando lenguaje de alto nivel a ensamblador...")

        parser.parse(source_code, lexer=lexer, tracking=True)

        if global_bigraph.instructions:
            print("\n📄 Ensamblador generado (desde parser):")
            for line in global_bigraph.instructions:
                print(f"    {line}")
        else:
            print("⚠️ No se generaron instrucciones desde el parser.")

        compiler = BigraphCompiler(global_bigraph)
        assembly_code = compiler.compile()

        print("\n📄 Ensamblador generado (desde bigrafo):")
        for line in assembly_code:
            print(f"    {line}")

        # 🧹 Filtrado estricto
        combined_code = global_bigraph.instructions + assembly_code
        cleaned_code = [line.strip() for line in combined_code if line.strip() and not line.strip().startswith(";")]

        print("📋 Instrucciones compiladas antes del ensamblado:")
        for i, line in enumerate(cleaned_code):
            print(f"{i+1:02}: '{line}' ({len(line)} chars)")

        return cleaned_code

    except Exception as e:
        print(f"❌ Error durante compilación: {e}")
        return []
