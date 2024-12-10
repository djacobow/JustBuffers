
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "types.h"

int main(int argc, char *argv[]) {
    t1 t = {};

    FILE *f = fopen(argv[1], "rb");
    fread(&t, 1, sizeof(t), f);
    fclose(f);

    for (size_t i=0; i<2; i++) {
        for (size_t j=0; j<2; j++) {
            assert(t.t0s[i][j].fee == (i + 2*j) * 0x02202202);
            assert(t.t0s[i][j].fi  == (i + 2*j) * 0x0202);
            assert(t.t0s[i][j].fo  == (i + 2*j) * 0x2200220022002200UL);
            const char *check_str = "Relax, they're Just Buffers";
            assert(!strcmp(check_str, t.t0s[i][j].fum));
        }
    }
    printf("PASS\n");
    return 0;
};
