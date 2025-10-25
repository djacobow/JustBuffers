#!/usr/bin/env python3

import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'../../'))

import jb.justbuffers
import jb.jscompare
import jb.randomspec
import jb.util

def randomizeBufferFromSpec(spec, top):

    def makeOne(mi):
        if mi['type'] in jb.justbuffers.get_base_types():
            return jb.justbuffers.get_base_types()[mi['type']]['rand']()
        else:
            return randomizeBufferFromSpec(spec, mi['type'])

    def randomizeMember(mi):
        count = jb.util.total_array_count(mi)
        vals = [ makeOne(mi) for i in range(count) ]
        return jb.util.unflattenArray(vals, mi['counts'])

    ov = {}
    for mi in spec[top]['members']:
        ov[mi['name']] = randomizeMember(mi)
    return ov


def buildAndRunExe(tdir):
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
    std::ifstream is("encoded.bin", std::ios::binary);
    std::ofstream os("decoded.json");
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
        'c++':    ['g++', 'cxxtest.cpp', '-o', 'cpptest' ],
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


if __name__ == '__main__':

    for i in range(10):
        print(f"Iter {i}")
        max_retries = 100
        for retry in range(max_retries):
            try:
                top, spec = jb.randomspec.makeSpecObject()
                j = jb.justbuffers.JustBufferator(
                  spec,
                  max_struct_size=2**22,
                  max_nesting_depth=2**8,
                  max_array_elements=2**20
                )
                tb = randomizeBufferFromSpec(j.elaborated, top)
                with tempfile.TemporaryDirectory() as tdir:
                    with open(os.path.join(tdir, "test.hpp"), 'w') as ofh:
                        ofh.write(j.generateCPPHeader())
                    with open(os.path.join(tdir, "encoded.bin"), "wb") as ofh:
                        ofh.write(j.encodeBuffer(top, tb))

                    if not buildAndRunExe(tdir):
                        print("Build FAILED")
                        sys.exit(-1)

                    with open(os.path.join(tdir, "decoded.json"), "r") as ifh:
                        tb_dec = json.loads(ifh.read())

                    if not jb.jscompare.compareSimple(tb, tb_dec):
                        print("Compare FAILED")
                        sys.exit(-1)
                break
            except (jb.justbuffers.ElaborationError, jb.justbuffers.SchemaValidationError) as e:
                if retry == max_retries - 1:
                    print(f'Failed after {max_retries} retries: {e}')
                    sys.exit(-1)
                continue

    sys.exit(0)

            

       
