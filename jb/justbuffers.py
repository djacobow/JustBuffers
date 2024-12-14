#!/usr/bin/env python3

import argparse
import json
import random
import struct

from . import util
from . import generators

# These are all the basic types that Just Buffers supprts.
# The rand member is a function used by tests to generate test
# data.
TYPEINFO = {
    'bool':   { 'size': 1, 'align': 1, 'pack': 'B', 'c_type': 'bool',
                'rand': lambda: random.choice([True,False])
    },
    'u8':     { 'size': 1, 'align': 1, 'pack': 'B', 'c_type': 'uint8_t',
                'rand': lambda: random.randint(0,255)
    },
    'i8':     { 'size': 1, 'align': 1, 'pack': 'b', 'c_type': 'int8_t',
                'rand': lambda: random.randint(-128,127)
    },
    'u16':    { 'size': 2, 'align': 2, 'pack': 'H', 'c_type': 'uint16_t',
                'rand': lambda: random.randint(0,65535)
    },
    'i16':    { 'size': 2, 'align': 2, 'pack': 'h', 'c_type': 'int16_t',
                'rand': lambda: random.randint(-32768,32767)
    },
    'u32':    { 'size': 4, 'align': 4, 'pack': 'L', 'c_type': 'uint32_t',
                'rand': lambda: random.randint(0,4294967295)
    },
    'i32':    { 'size': 4, 'align': 4, 'pack': 'l', 'c_type': 'int32_t',
                'rand': lambda: random.randint(-2147483648, 2147483647)
    },
    'u64':    { 'size': 8, 'align': 8, 'pack': 'Q', 'c_type': 'uint64_t',
                'rand': lambda: random.randint(0,0xffffffff_ffffffff)
    },
    'i64':    { 'size': 8, 'align': 8, 'pack': 'q', 'c_type': 'int64_t',
                'rand': lambda: random.randint(0,0xffffffff_ffffffff) - 0x7fffffff_ffffffff
    },
    'float':  { 'size': 4, 'align': 4, 'pack': 'f', 'c_type': 'float',
                'rand': lambda: struct.unpack('<f', struct.pack('<f', random.uniform(-3.4e38,3.4e38)))[0]
    },
    'double': { 'size': 8, 'align': 8, 'pack': 'd', 'c_type': 'double',
                'rand': lambda: random.uniform(-1.79e308, 1.79e308)
    },
}

def get_base_types():
    return TYPEINFO

class JustBufferator():
    typeinfo = TYPEINFO

    def __addPlaceHolders(self, needed, elaborated, index, offset, name_pat = '__pad_{}'):
        placeholder = {
                    'name': name_pat.format(index),
                    'offset': offset,
                    'type': 'u8',
                    'counts': [needed],
                    'align': 1,
                    'size': needed,
        }
        elaborated['members'].append(placeholder)

    def __elaborateConfigs(self):
        elaborated = {}

        messages = []

        for t_name, t_info in self.configs.items():
            elaborated[t_name] = {
                'members': [],
            }
            offset = 0
            placeholder_count = 0
            for m_info in t_info:
                m_name = m_info['name']
                m_elaborated = {
                    'type': m_info['type'],
                    'name': m_name,
                }
                m_t_name = m_info['type']
                if m_t_name in self.typeinfo:
                    req_align = self.typeinfo[m_t_name]['align']
                    m_t_size = self.typeinfo[m_t_name]['size']
                elif m_t_name in elaborated and 'align' in elaborated[m_t_name]:
                    req_align = elaborated[m_t_name]['align']
                    m_t_size = elaborated[m_t_name]['size']
                else:
                    messages.append(('error', f'no known type {m_t_name}'))
                if not self.packed:
                    misalignment = offset % req_align 
                    if misalignment:
                        needed_alignment = req_align - misalignment
                        self.__addPlaceHolders(needed_alignment, elaborated[t_name], placeholder_count, offset)
                        offset += needed_alignment
                        placeholder_count += 1
                        messages.append(('info',f'struct "{t_name}": alignment placeholder size {needed_alignment} inserted before "{m_name}"'))

                m_elaborated['align'] = req_align
                m_elaborated['offset'] = offset
                elaborated[t_name]['members'].append(m_elaborated)
                counts = m_info.get('counts',[1])
                if isinstance(counts,int):
                    counts = [counts]
                m_elaborated['counts'] = counts 
                total_size = m_t_size * util.total_array_count(m_elaborated)
                m_elaborated['size'] = total_size
                offset += total_size

            elaborated[t_name]['size'] = offset 
            total_req_align = util.powerOfTwoEqualOrMoreThan(offset)
            if total_req_align > 8:
                total_req_align = 8
            elaborated[t_name]['align'] = total_req_align

            if not self.packed:
                misalignment = offset % total_req_align
                if misalignment:
                    needed_alignment = total_req_align - misalignment
                    messages.append(('info',f'struct "{t_name}": padding placeholder size {needed_alignment} appended'))
                    self.__addPlaceHolders(needed_alignment, elaborated[t_name], placeholder_count, offset)
                    offset += needed_alignment
                    placeholder_count += 1

            elaborated[t_name]['size'] = offset
            
        self.elab_messages = messages
        self.elaborated = elaborated
                    

    def encodeBuffer(self, t_name, data):
        enc_messages = [] 
        def encodeMember(m_info, values):
            m_type = m_info['type']
            m_t_info = self.typeinfo.get(m_type, None)
            flat_values = util.flattenArrays(values)
            total_count = util.total_array_count(m_info)

            if m_t_info is not None:
                fmt = m_t_info['pack']
                if len(flat_values) < total_count:
                    enc_messages.append(('warning', f'input for {m_info["name"]} too short'))
                    flat_values += [0] * (total_count - len(flat_values))
                obytes = struct.pack(f'{self.pack_endian}{total_count}{fmt}', *flat_values)     
            else:
                m_t_info = self.elaborated[m_type]
                if len(flat_values) < total_count:
                    flat_values += [{}] * (total_count - len(flat_values))
                obytes = b''.join([ self.encodeBuffer(m_type, v) for v in flat_values])
                
            return obytes

        t_info = self.elaborated[t_name]
        odata = []
        for m_info in t_info['members']:
            m_name = m_info['name']
            values = data.get(m_name)
            if values is None:
                odata.append(bytes(m_info['size']))
            else:
                odata.append(encodeMember(m_info, values))
        self.enc_messages = enc_messages

        return b''.join(odata)
         
    def decodeBuffer(self, t_name, data):

        def decodeMember(m_info, data):
            m_type = m_info['type']
            m_t_info = self.typeinfo.get(m_type, None)
            total_count = util.total_array_count(m_info)
            d_ary = []
            if m_t_info is not None:
                total_size = total_count * m_t_info['size']
                fmt = m_t_info['pack']
                d_ary = list(struct.unpack(f'{self.pack_endian}{total_count}{fmt}', data[:total_size]))
                if m_type == 'bool':
                    d_ary = [ bool(x) for x in d_ary ]
                # print(m_info['name'], m_info['type'], d_ary)
            else:
                m_t_info = self.elaborated[m_type]
                total_size = total_count * m_t_info['size']
                d_ary = []
                for i in range(total_count):
                    subdata = data[i*m_t_info['size']:(i+1)*m_t_info['size']]
                    # print('i', i, subdata.hex())
                    d_ary.append(self.decodeBuffer(m_info['type'], subdata))
            return d_ary
                
        t_info = self.elaborated[t_name]
        rv = {}
        offset = 0
        for m_info in t_info['members']:
            raw_array = decodeMember(m_info, data[offset:offset+m_info['size']])
            rv[m_info['name']] = util.unflattenArray(raw_array, m_info['counts'])
            offset += m_info['size']
        return rv


    def generateCPPHeader(self):
        return generators.cpp.generate(self.typeinfo, self.elaborated, self.packed)


    def generateCHeader(self):
        return generators.c.generate(self.typeinfo, self.elaborated, self.packed)

    def __init__(self, configs, big_endian=False, packed=False):
        self.elab_messages = None
        self.elaborated = None
        self.pack_endian = '>' if big_endian else '<'
        self.packed = packed
        self.configs = configs
        self.__elaborateConfigs()



def getArgs():
    ap = argparse.ArgumentParser(description="tool to generate C structs and python reader/writers for them")
    ap.add_argument(
        '-c', '--config',
        help='JSON-formatted configuration file',
        required = True,
        type=argparse.FileType('r')
    )
    ap.add_argument(
        '-gc', '--generate-c',
        help='generate a c header. Provide the name of the file to write',
        nargs=1,
        type=str,
        default=None,
    )
    ap.add_argument(
        '-gcpp', '--generate-cpp',
        help='generate a cpp header. Provide the name of the file to write',
        nargs=1,
        type=str,
        default=None,
    )
    ap.add_argument(
        '--dump',
        help='show the detailed struct info after elaboration; useful for debug',
        action='store_true',
    )
    ap.add_argument(
        '-b' ,'--big-endian',
        help='tell the python code to use big-endian encodings. Does not affect the headers!',
        action='store_true',
    )
    ap.add_argument(
        '-p' ,'--packed',
        help='make the struct packed',
        action='store_true',
    )
    meg = ap.add_mutually_exclusive_group()
    meg.add_argument(
        '-d', '--decode',
        help='convert a binary file to json',
        metavar = ('INPUT_bin', 'OUTPUT_json'),
        nargs=2,
    )
    meg.add_argument(
        '-e', '--encode',
        help='convert a json file to binary',
        metavar = ('INPUT_json', 'OUTPUT_bin'),
        nargs=2,
    )
    ap.add_argument(
        '-t', '--type',
        help='name of type in spec file to use for encode or decode',
        type=str
    )
    return ap.parse_args()


def showMessages(name, messages):
    print(name)
    print('------- ----------------------------------------------------------')
    for m in messages:
        print(f'{m[0]:6} {m[1]}')


def main(args):
    j = JustBufferator(
        json.loads(args.config.read()),
        big_endian=args.big_endian,
        packed=args.packed
    )
    showMessages('Elaboration Messages:', j.elab_messages)        

    if args.dump:
        print('Elaborated Struct Info')
        print('----------------------')
        print(json.dumps(j.elaborated, indent=2))

    if args.generate_c is not None:
        h = j.generateCHeader()
        with open(args.generate_c[0], 'w') as ofh:
            ofh.write(h)

    if args.generate_cpp is not None:
        h = j.generateCPPHeader()
        with open(args.generate_cpp[0], 'w') as ofh:
            ofh.write(h)

    if (args.decode or args.encode) and not args.type:
        print('If encoding or decoding, you need to specify the name of struct with --type')

    if args.decode:
        with open(args.decode[0], 'rb') as ifh:
            d = j.decodeBuffer(args.type, ifh.read())
        with open(args.decode[1], 'w') as ofh:
            ofh.write(json.dumps(d, indent=2))
    elif args.encode:
        with open(args.encode[0], 'r') as ifh:
            b = j.encodeBuffer(args.type, json.loads(ifh.read()))
        with open(args.encode[1], 'wb') as ofh:
            ofh.write(b)
        
if __name__ == '__main__':
    main()
