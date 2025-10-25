#!/usr/bin/env python3

import argparse
import json
import random
import re
import struct
import os

from . import util
from . import generators

class SchemaValidationError(Exception):
    """Raised when JSON config schema is invalid"""
    pass

class ElaborationError(Exception):
    """Raised when struct elaboration fails"""
    pass

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

VALID_IDENTIFIER = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
DANGEROUS_PATH_PREFIXES = ['/etc/', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/', '/boot/', '/sys/', '/proc/']

C_CPP_KEYWORDS = {
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor', 'bool', 'break',
    'case', 'catch', 'char', 'char16_t', 'char32_t', 'char8_t', 'class', 'compl', 'concept',
    'const', 'const_cast', 'consteval', 'constexpr', 'constinit', 'continue', 'co_await',
    'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast',
    'else', 'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend', 'goto',
    'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq',
    'nullptr', 'operator', 'or', 'or_eq', 'private', 'protected', 'public', 'register',
    'reinterpret_cast', 'requires', 'return', 'short', 'signed', 'sizeof', 'static',
    'static_assert', 'static_cast', 'struct', 'switch', 'template', 'this', 'thread_local',
    'throw', 'true', 'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using',
    'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq',
    '_Alignas', '_Alignof', '_Atomic', '_Bool', '_Complex', '_Generic', '_Imaginary',
    '_Noreturn', '_Static_assert', '_Thread_local',
}

def validate_identifier(name, context, allow_base_types=False):
    if not isinstance(name, str):
        raise ElaborationError(f"Invalid identifier in {context}: expected string, got {type(name).__name__}")

    if not name:
        raise ElaborationError(f"Invalid identifier in {context}: empty string not allowed")

    if not VALID_IDENTIFIER.match(name):
        raise ElaborationError(
            f"Invalid identifier '{name}' in {context}. "
            f"Must start with letter or underscore, followed by letters, digits, or underscores. "
            f"Pattern: [a-zA-Z_][a-zA-Z0-9_]*"
        )

    if name in C_CPP_KEYWORDS:
        if allow_base_types and name in TYPEINFO:
            return
        raise ElaborationError(
            f"Invalid identifier '{name}' in {context}. "
            f"'{name}' is a reserved C/C++ keyword and cannot be used"
        )

def validate_output_path(path, purpose):
    if not isinstance(path, str):
        raise ValueError(f"Invalid path for {purpose}: expected string, got {type(path).__name__}")

    if not path:
        raise ValueError(f"Invalid path for {purpose}: empty string not allowed")

    abs_path = os.path.abspath(path)

    for prefix in DANGEROUS_PATH_PREFIXES:
        if abs_path.startswith(prefix):
            raise ValueError(
                f"Refusing to write to system directory: {abs_path}\n"
                f"Path {path} for {purpose} resolves to a protected location."
            )

    return abs_path

def validate_member_schema(type_name, idx, member):
    if not isinstance(member, dict):
        raise SchemaValidationError(
            f"Member {idx} in type '{type_name}' must be an object/dict, "
            f"got {type(member).__name__}"
        )

    if 'type' not in member:
        raise SchemaValidationError(
            f"Member {idx} in type '{type_name}' missing required field 'type'"
        )

    if 'name' not in member:
        raise SchemaValidationError(
            f"Member {idx} in type '{type_name}' missing required field 'name'"
        )

    if not isinstance(member['type'], str):
        raise SchemaValidationError(
            f"Member {idx} in type '{type_name}': 'type' must be a string, "
            f"got {type(member['type']).__name__}"
        )

    if not isinstance(member['name'], str):
        raise SchemaValidationError(
            f"Member {idx} in type '{type_name}': 'name' must be a string, "
            f"got {type(member['name']).__name__}"
        )

    if 'counts' in member:
        counts = member['counts']
        if isinstance(counts, int):
            if counts < 1:
                raise SchemaValidationError(
                    f"Member '{member['name']}' in type '{type_name}': "
                    f"'counts' must be positive, got {counts}"
                )
        elif isinstance(counts, list):
            if not counts:
                raise SchemaValidationError(
                    f"Member '{member['name']}' in type '{type_name}': "
                    f"'counts' list cannot be empty"
                )
            for i, c in enumerate(counts):
                if not isinstance(c, int):
                    raise SchemaValidationError(
                        f"Member '{member['name']}' in type '{type_name}': "
                        f"'counts[{i}]' must be an integer, got {type(c).__name__}"
                    )
                if c < 1:
                    raise SchemaValidationError(
                        f"Member '{member['name']}' in type '{type_name}': "
                        f"'counts[{i}]' must be positive, got {c}"
                    )
        else:
            raise SchemaValidationError(
                f"Member '{member['name']}' in type '{type_name}': "
                f"'counts' must be an integer or list of integers, "
                f"got {type(counts).__name__}"
            )

def validate_config_schema(configs):
    if not isinstance(configs, dict):
        raise SchemaValidationError(
            f"Config must be a JSON object/dict, got {type(configs).__name__}"
        )

    if not configs:
        raise SchemaValidationError("Config cannot be empty")

    for type_name, members in configs.items():
        if not isinstance(members, list):
            raise SchemaValidationError(
                f"Type '{type_name}' must have a list of members, "
                f"got {type(members).__name__}"
            )

        if not members:
            raise SchemaValidationError(f"Type '{type_name}' has no members")

        for idx, member in enumerate(members):
            validate_member_schema(type_name, idx, member)

class JustBufferator():
    typeinfo = TYPEINFO

    def __makePlaceholder(self, needed, index, offset):
        return {
            'name': f'__pad_{index}',
            'offset': offset,
            'type': 'u8',
            'counts': [needed],
            'align': 1,
            'size': needed,
        }

    def __elaborateConfigs(self):
        elaborated = {}
        messages = []

        # First, validate all type names and check that referenced types exist
        for t_name, t_info in self.configs.items():
            validate_identifier(t_name, 'type name')

            for m_info in t_info:
                m_name = m_info['name']
                m_t_name = m_info['type']

                validate_identifier(m_name, f'member name in type "{t_name}"')
                validate_identifier(m_t_name, f'member type in type "{t_name}", member "{m_name}"', allow_base_types=True)

                # Check that the type exists somewhere
                if m_t_name not in self.typeinfo and m_t_name not in self.configs:
                    raise ElaborationError(f"Unknown type '{m_t_name}' in type '{t_name}', member '{m_name}'")

        # Now elaborate in multiple passes to handle forward references
        max_passes = len(self.configs) + 1
        for pass_num in range(max_passes):
            progress_made = False

            for t_name, t_info in self.configs.items():
                if t_name in elaborated and 'size' in elaborated[t_name]:
                    continue  # Already fully elaborated

                can_complete = True
                offset = 0
                placeholder_count = 0
                temp_members = []

                for m_info in t_info:
                    m_name = m_info['name']
                    m_t_name = m_info['type']

                    m_elaborated = {
                        'type': m_t_name,
                        'name': m_name,
                    }

                    if m_t_name in self.typeinfo:
                        req_align = self.typeinfo[m_t_name]['align']
                        m_t_size = self.typeinfo[m_t_name]['size']
                    elif m_t_name in elaborated and 'size' in elaborated[m_t_name]:
                        req_align = elaborated[m_t_name]['align']
                        m_t_size = elaborated[m_t_name]['size']
                    else:
                        # Forward reference - can't complete this type yet
                        can_complete = False
                        break

                    if not self.packed:
                        misalignment = offset % req_align
                        if misalignment:
                            needed_alignment = req_align - misalignment
                            temp_members.append(self.__makePlaceholder(needed_alignment, placeholder_count, offset))
                            offset += needed_alignment
                            placeholder_count += 1
                            messages.append(('info',f'struct "{t_name}": alignment placeholder size {needed_alignment} inserted before "{m_name}"'))

                    m_elaborated['align'] = req_align
                    m_elaborated['offset'] = offset
                    temp_members.append(m_elaborated)
                    counts = m_info.get('counts',[1])
                    if isinstance(counts,int):
                        counts = [counts]
                    m_elaborated['counts'] = counts

                    total_count = util.total_array_count(m_elaborated)
                    if total_count > self.max_array_elements:
                        raise ElaborationError(
                            f"Array too large in type '{t_name}', member '{m_name}': "
                            f"{total_count} elements exceeds limit of {self.max_array_elements}"
                        )

                    total_size = m_t_size * total_count
                    m_elaborated['size'] = total_size
                    offset += total_size

                if not can_complete:
                    continue  # Skip this type for now, try again in next pass

                # Type can be completed
                elaborated[t_name] = {'members': temp_members}
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
                        elaborated[t_name]['members'].append(self.__makePlaceholder(needed_alignment, placeholder_count, offset))
                        offset += needed_alignment

                elaborated[t_name]['size'] = offset

                if offset > self.max_struct_size:
                    raise ElaborationError(
                        f"Struct '{t_name}' too large: {offset} bytes exceeds limit of {self.max_struct_size}"
                    )

                progress_made = True

            if not progress_made:
                # No progress in this pass - must be circular references
                break

        def validate_depth(t_name, depth=0):
            if t_name in self.typeinfo:
                return depth

            if depth > self.max_nesting_depth:
                raise ElaborationError(
                    f"Nesting depth {depth} in type '{t_name}' exceeds limit of {self.max_nesting_depth}"
                )

            max_depth = depth
            for m_info in elaborated[t_name]['members']:
                m_type = m_info['type']
                if m_type not in self.typeinfo:
                    d = validate_depth(m_type, depth + 1)
                    max_depth = max(max_depth, d)

            return max_depth

        for t_name in elaborated:
            validate_depth(t_name)

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

    def __init__(self, configs, big_endian=False, packed=False,
                 max_array_elements=65535, max_struct_size=65535,
                 max_nesting_depth=16):
        validate_config_schema(configs)
        self.elab_messages = None
        self.elaborated = None
        self.pack_endian = '>' if big_endian else '<'
        self.packed = packed
        self.configs = configs
        self.max_array_elements = max_array_elements
        self.max_struct_size = max_struct_size
        self.max_nesting_depth = max_nesting_depth
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
    ap.add_argument(
        '--max-array-elements',
        help='maximum elements in any array',
        type=int,
        default=65535,
    )
    ap.add_argument(
        '--max-struct-size',
        help='maximum struct size in bytes',
        type=int,
        default=65535,
    )
    ap.add_argument(
        '--max-nesting-depth',
        help='maximum nesting depth',
        type=int,
        default=16,
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
        packed=args.packed,
        max_array_elements=args.max_array_elements,
        max_struct_size=args.max_struct_size,
        max_nesting_depth=args.max_nesting_depth
    )
    showMessages('Elaboration Messages:', j.elab_messages)        

    if args.dump:
        print('Elaborated Struct Info')
        print('----------------------')
        print(json.dumps(j.elaborated, indent=2))

    if args.generate_c is not None:
        output_path = validate_output_path(args.generate_c[0], 'C header output')
        h = j.generateCHeader()
        with open(output_path, 'w') as ofh:
            ofh.write(h)

    if args.generate_cpp is not None:
        output_path = validate_output_path(args.generate_cpp[0], 'C++ header output')
        h = j.generateCPPHeader()
        with open(output_path, 'w') as ofh:
            ofh.write(h)

    if (args.decode or args.encode) and not args.type:
        print('If encoding or decoding, you need to specify the name of struct with --type')

    if args.decode:
        input_path = os.path.abspath(args.decode[0])
        output_path = validate_output_path(args.decode[1], 'decoded JSON output')
        with open(input_path, 'rb') as ifh:
            d = j.decodeBuffer(args.type, ifh.read())
        with open(output_path, 'w') as ofh:
            ofh.write(json.dumps(d, indent=2))
    elif args.encode:
        input_path = os.path.abspath(args.encode[0])
        output_path = validate_output_path(args.encode[1], 'encoded binary output')
        with open(input_path, 'r') as ifh:
            b = j.encodeBuffer(args.type, json.loads(ifh.read()))
        with open(output_path, 'wb') as ofh:
            ofh.write(b)
        
if __name__ == '__main__':
    main()
