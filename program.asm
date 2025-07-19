#define VAL 10
#include "lib.inc"

        LOAD R1, VAL
        LOAD R2, 20
        ADD  R1, R2
        STORE R1, 0x200
        HALT
