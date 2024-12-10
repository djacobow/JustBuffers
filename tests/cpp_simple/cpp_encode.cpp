
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "types.hpp"

int main(int argc, char *argv[]) {
    t1 t = {};
    t.blee = 0xcafe;

    for (size_t i=0;i<2;i++) {
        for (size_t j=0;j<2;j++) {
            t0 temp = {};
            temp.fee = (i*2 + j) * 0x11011011,
            temp.fi  = (i*2 + j) * 0x1010,
            temp.fo  = (i*2 + j) * 0x1110111011101110UL,
            strncpy(reinterpret_cast<char *>(temp.fum), "Just Buffers are chill", 127);
            t.t0s[i][j] = temp;
        }
    }

    FILE *f = fopen(argv[1], "wb");
    fwrite(&t, 1, sizeof(t), f);
    fclose(f);
    printf("%s", t.toJS().dump().c_str());
    return 0;
};
