#!/usr/bin/env python3

import sys
import os
import random
import json
import tempfile
import subprocess
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'../../'))

import jb.justbuffers

def get_shell_output(args, **runargs):
    runargs['stdout'] = subprocess.PIPE
    r = subprocess.run(args, **runargs)
    return (r.returncode, r.stdout.decode("utf-8", errors="ignore"))


def makeSpecObject():
    name_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    names_used = {
        'j': 1 # this is used in the c++ header
    }

    def makeName(maxl):
        while True:
            candidate = ''.join([random.choice(name_letters) for i in range(random.randint(1,maxl)) ])
            if candidate not in names_used:
                names_used[candidate] = 1
                return candidate


    def makeSimple(more_types=[]):
        ms = []
        s = {
           makeName(10): ms    
        }
        elem_count = random.randint(1, 15)
        for i in range(elem_count):
            elem_type = random.choice(list(jb.justbuffers.JustBufferator.typeinfo.keys()) + more_types)
            elem_dims = random.randint(0, 3)
            elem_sizes = [ random.randint(1,10) for i in range(elem_dims) ]
            if elem_dims > 0:
                ms.append({'type': elem_type, 'name': makeName(10), 'counts': elem_sizes})
            else:
                ms.append({'type': elem_type, 'name': makeName(10)})
        return s

    s = {}
    for i in range(0,4):
        s.update(makeSimple())

    top = makeSimple(list(s.keys()))
    s.update(top)
    return list(top.keys())[0], s


def compileExes(tdir, spec, top):
    j = jb.justbuffers.JustBufferator(spec)
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
        res = get_shell_output(step, cwd=os.path.abspath(tdir), shell=False, env={'PATH':'/usr/bin'})
        if res[0] != 0:
            print(f'FAIL at step {name}')
            print(res[1])
            return False
        print(f'{name} complete')
    return True

def compareSimple(a,b):
    if isinstance(a, dict) and isinstance(b, dict):
        return all([ (k in b) and compareSimple(v, b[k])  for k,v in a.items()  ])
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            print(f'mismatch len {len(a)} {len(b)}')
            return False 
        return all([ compareSimple(a[i], b[i]) for i in range(len(a))])
    else:
        if a != b:
            # we can treat none and nan as equivalent here
            a_nothing = a is None or math.isnan(a)
            b_nothing = b is None or math.isnan(b)
            if not a_nothing or not b_nothing:
                print(f'a {a} != b {b}')
                return False
        return True

            
def compare(tdir, spec, top):
    with open(os.path.join(tdir, "test.bin"), "rb") as ifh:
        js_jb = jb.justbuffers.JustBufferator(spec).decodeBuffer(top, ifh.read())
    with open(os.path.join(tdir, "test.json"), "r") as ifh:
        js_cpp = json.loads(ifh.read())

    with open('a.json', 'w') as ofh:
        ofh.write(json.dumps(js_jb, indent=2, sort_keys=True))
    with open('b.json', 'w') as ofh:
        ofh.write(json.dumps(js_cpp, indent=2, sort_keys=True))

    return compareSimple(js_cpp, js_jb)

if __name__ == '__main__':

    for i in range(5):
        print(f"Iter {i}")
        with tempfile.TemporaryDirectory() as tdir:
            top, spec = makeSpecObject()
            if not compileExes(tdir, spec, top):
                print('Compilation / run failed')
                sys.exit(-1)
            if not compare(tdir, spec, top):
                print('Check failed')
                sys.exit(-1)
    sys.exit(0)

            

       
