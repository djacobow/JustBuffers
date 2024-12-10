#!/usr/bin/env python3

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'../../'))

import jb.justbuffers

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as ifh:
        typespec = json.loads(ifh.read())

    data = { 't0s': [[{},{}],[{},{}]], }
    for i in range(2):
        for j in range(2):
            t0 = data['t0s'][i][j]
            t0['fee'] = (i + 2*j) * 0x02202202
            t0['fi']  = (i + 2*j) * 0x0202
            t0['fo']  = (i + 2*j) * 0x2200220022002200
            fum_str = 'Relax, they\'re Just Buffers'
            fum_bytes = fum_str.encode('ascii') + bytes(128 - len(fum_str))
            t0['fum'] = list(fum_bytes)

    j = jb.justbuffers.JustBufferator(typespec)
    with open(sys.argv[2], 'wb') as ofh:
        ofh.write(j.encodeBuffer('t1', data))

