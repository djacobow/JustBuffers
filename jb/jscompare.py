#!/usr/bin/env python3

import argparse
import json
import math
import re
import sys
import yaml

# this simple utility lets you compare two json files to check if they are
# the same. It can also do yaml or yaml/json

def compareSimple(a,b):
    if isinstance(a, dict) and isinstance(b, dict):
        return all([ (k in b) and compareSimple(v, b[k])  for k,v in a.items()  ])
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            print(f'mismatch len {len(a)} {len(b)}')
            print('a',a,'b',b)
            return False 
        return all([ compareSimple(a[i], b[i]) for i in range(len(a))])
    else:
        if a != b:
            # we can treat none and nan as equivalent here
            a_nothing = a is None or math.isnan(a) or math.isinf(a)
            b_nothing = b is None or math.isnan(b) or math.isinf(b)
            if not a_nothing or not b_nothing:
                print(f'a {a} != b {b}')
                return False
        return True


def getArgs():
    ap = argparse.ArgumentParser(description="tool to compare two files of json or yaml")
    ap.add_argument(
        '-a', '--file-a',
        type=str,
        required=True
    )
    ap.add_argument(
        '-b', '--file-b',
        type=str,
        required=True
    )
    return ap.parse_args()

def main(args):
    d = {
        'a': {
            'name': args.file_a,
        },
        'b': {
            'name': args.file_b,
        },
    }
    
    for k,v in d.items():
        with open(v['name'],'r') as ifh:
            v['raw'] = ifh.read()
        if re.search(r'.json$',v['name'],re.IGNORECASE):
            v['data'] = json.loads(v['raw'])
        if re.search(r'.ya?ml$',v['name'],re.IGNORECASE):
            v['data']= yaml.load(v['raw'])
        
    match =  compareSimple(*[ v['data'] for v in d.values() ])
    if match:
       print('Files match!')
       sys.exit(0)
    print('ERROR MISMATCH')
    sys.exit(-1)


if __name__ == '__main__':
    args = getArgs()
    main(args)


