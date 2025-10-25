#!/usr/bin/env python3

import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'../../'))

import jb.justbuffers
import jb.jscompare
import jb.randomspec

# This test consists of the following steps:
#
# 0. generate a randomized specification of buffers. This
#    spec includes a buffer that contains other buffers,
#    as well as multidimensional arrays
# 1. generate headers using the library
# 2. compile programs in C and C++ using the headers
# 3. Use the "C" program to generate a completely random file of the appropriate size
# 4. Use a "C++" program to load that file and write it back out as JSON
# 5. Use the library to also read that file and decode it
# 6. Check that the json written by the c++ program and that decoded by python are identical
#
# This is repeated several times.

def makeBufferator(spec):
  return jb.justbuffers.JustBufferator(
    spec, max_array_elements=2**20,
    max_struct_size=2**20,
    max_nesting_depth=2**8
  )

def compileExes(tdir, spec, top):
    j = makeBufferator(spec)
    with open(os.path.join(tdir, "test.h"), 'w') as ofh:
        ofh.write(j.generateCHeader())
    with open(os.path.join(tdir, "test.hpp"), 'w') as ofh:
        ofh.write(j.generateCPPHeader())
    with open(os.path.join(tdir, "ctest.c"), 'w') as ofh:
        ofh.write(
f'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "test.h"
int main(int argc, char *argv[]) {{
    {top} top;
    char *t = (char *)&top;
    for (size_t i=0; i<sizeof(top); i++) {{
        t[i] = rand() & 0xff;
    }}
    FILE *f = fopen("test.bin", "wb");
    fwrite(&top, 1, sizeof(top), f);
    fclose(f);
    return 0;
}}
'''
            )

    with open(os.path.join(tdir, "cxxtest.cpp"), 'w') as ofh:
        ofh.write(
f'''
#include "test.hpp"
#include <fstream>
#include <iterator>
#include <iostream>
#include <vector>
int main(int argc, char *argv[]) {{
    {top} top;
    std::ifstream is("test.bin", std::ios::binary);
    std::ofstream os("test.json");
    std::vector<char> d(
        (std::istreambuf_iterator<char>(is)),
        (std::istreambuf_iterator<char>())
    );
    is.close();
    memcpy(&top, d.data(), d.size());
    os << top.toJS().dump() << "\\n";
    os.close();
    return 0;
}}
'''
            )

    steps = {
        'cc':     ['gcc', '-g', '-Wall', '-Werror', 'ctest.c', '-o', 'ctest'],
        'c++':    ['g++', 'cxxtest.cpp', '-o', 'cpptest' ],
        'runc':   ['./ctest'],
        'runc++': ['./cpptest']
    }

    for name, step in steps.items():
        res = jb.util.get_shell_output(step, cwd=os.path.abspath(tdir), shell=False, env={'PATH':'/usr/bin'})
        if res[0] != 0:
            print(f'FAIL at step {name}')
            print(res[1])
            print(f"spec was: (top: {top})")
            print(json.dumps(spec,indent=2,sort_keys=True))
            return False
        print(f'{name} complete')
    return True

def compare(tdir, spec, top):
    with open(os.path.join(tdir, "test.bin"), "rb") as ifh:
        js_jb = makeBufferator(spec).decodeBuffer(top, ifh.read())
    with open(os.path.join(tdir, "test.json"), "r") as ifh:
        js_cpp = json.loads(ifh.read())

    with open(os.path.join(tdir,'a.json'), 'w') as ofh:
        ofh.write(json.dumps(js_jb, indent=2, sort_keys=True))
    with open(os.path.join(tdir,'b.json'), 'w') as ofh:
        ofh.write(json.dumps(js_cpp, indent=2, sort_keys=True))

    return jb.jscompare.compareSimple(js_cpp, js_jb)

if __name__ == '__main__':

    for i in range(5):
        print(f"Iter {i}")
        max_retries = 100
        for retry in range(max_retries):
            try:
                with tempfile.TemporaryDirectory() as tdir:
                    top, spec = jb.randomspec.makeSpecObject()
                    if not compileExes(tdir, spec, top):
                        print('Compilation / run failed')
                        sys.exit(-1)
                    if not compare(tdir, spec, top):
                        print('Check failed')
                        sys.exit(-1)
                break
            except (jb.justbuffers.ElaborationError, jb.justbuffers.SchemaValidationError) as e:
                if retry == max_retries - 1:
                    print(f'Failed after {max_retries} retries: {e}')
                    sys.exit(-1)
                continue
    sys.exit(0)

            

       
