#!/usr/bin/env python3

import sys
import os
import random
#import json
import tempfile
import subprocess

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
    std::vector<char> d(
        (std::istreambuf_iterator<char>(is)),
        (std::istreambuf_iterator<char>())
    );
    is.close();
    memcpy(&top, d.data(), d.size());
    std::cout << top.toJS().dump() << "\\n";
    return 0;
}}
'''
            )

        steps = {
            'cc':  ['gcc', '-g', '-Wall', '-Werror', 'ctest.c', '-o', 'ctest'],
            'c++': ['g++', 'cxxtest.cpp' ],
        }

        for name, step in steps.items():
            res = get_shell_output(step, cwd=os.path.abspath(tdir), shell=False, env={'PATH':'/usr/bin'})
            print(res[1])
            if res[0] != 0:
                print(f'FAIL {name}')
                return None
            print(f'{name} complete')

    return { 'c': os.path.join(tdir,"ctest"), 'cpp': os.path.join('cpptest') }


def runExes(tdir, exes):
    pass

if __name__ == '__main__':

    for i in range(1):
        with tempfile.TemporaryDirectory() as tdir:
            tdir = 'boop'
            print(i)
            top, spec = makeSpecObject()
            exes = compileExes(tdir, spec, top)
            res = runExes(tdir, exes)
            if exes is None:
                sys.exit(-1)


       
