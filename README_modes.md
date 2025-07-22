# Simulador Von Neumann con Bigrafos - Información de Modos

## Modo Ensamblador (asm)
- Ejecuta código ensamblador estándar
- Soporta macros e includes
- Instrucciones: LOAD, STORE, ADD, SUB, MUL, DIV, etc.
- Ejemplo:
```asm
#include "math.inc"
LOAD R2, CONST
ADD R2, 10
HALT
```

## Modo Binario/Tuplas (bin)
- Ejecuta instrucciones binarias directamente
- Formato: cadenas binarias o tuplas (valor, bits)
- Útil para depuración a bajo nivel

## Modo Bigrafos (bigraph)
- Sistema de Reacción de Bigrafos según Robin Milner
- Modela sistemas concurrentes y móviles
- Place Graph: estructura jerárquica
- Link Graph: conectividad hipergráfica
- Reglas de reacción: transformaciones del sistema

### Elementos del lenguaje de Bigrafos:

**Controles:**
```
atomic control Person(name: string) : 1;
control Room : 2;
```

**Signaturas:**
```
signature {
    Person(name) : 1,
    Room : 2
}
```

**Reglas de Reacción:**
```
rule enter_room:
    Person("Alice") | Room
    =>
    Room << Person("Alice");
```

**Bigrafos:**
```
bigraph house = Building << (Room | Person("Bob"));
```

**Operadores:**
- `|` : Composición paralela
- `*` : Producto tensorial  
- `.` : Composición secuencial
- `<<` : Anidamiento (place graph)
- `~{}` : Enlaces (link graph)
