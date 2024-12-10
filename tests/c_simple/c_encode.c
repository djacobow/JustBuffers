
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "types.h"

int main(int argc, char *argv[]) {
    t1 t = {};

    for (size_t i=0;i<2;i++) {
        for (size_t j=0;j<2;j++) {
            t.t0s[i][j] = (t0){
                .fee = (i*2 + j) * 0x11011011,
                .fi  = (i*2 + j) * 0x1010,
                .fo  = (i*2 + j) * 0x1110111011101110UL,
            };
            strncpy(t.t0s[i][j].fum, "Just Buffers are chill", 127);
        }
    }

    FILE *f = fopen(argv[1], "wb");
    fwrite(&t, 1, sizeof(t), f);
    fclose(f);
    return 0;
};
