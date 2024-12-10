#!/usr/bin/env python3

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'../../'))

import jb.justbuffers

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as ifh:
        typespec = json.loads(ifh.read())
    j = jb.justbuffers.JustBufferator(typespec)

    with open(sys.argv[2], 'rb') as ifh:
        bindata = ifh.read()
    data = j.decodeBuffer('t1', bindata)

    with open(sys.argv[3], 'w') as ofh:
        ofh.write(json.dumps(data,indent=2))

    for i in range(2):
        for j in range(2):
            t0 = data['t0s'][i][j]
            assert(t0['fee'] == (i*2 +j) * 0x11011011)
            assert(t0['fi']  == (i*2 +j) * 0x1010)
            assert(t0['fo']  == (i*2 +j) * 0x1110111011101110)
            fum_bytes = bytes(t0['fum']).split(b'\0')[0]
            fum_str   = fum_bytes.decode('ascii', errors='ignore').strip()
            ts = 'Just Buffers are chill'
            assert(fum_str == ts)

