import random

# this file is used by tests to generate randomized Just Buffers specifications

from . import justbuffers

def makeSpecObject():
    name_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    cant_use = {
        # avoid c++ keywords
        'alignas': 1, 'alignof': 1, 'and': 1, 'and_eq': 1, 'asm': 1, 'atomic_cancel': 1,
        'atomic_commit': 1, 'atomic_noexcept': 1, 'auto': 1, 'bitand': 1, 'bitor': 1, 'bool': 1,
        'break': 1, 'case': 1, 'catch': 1, 'char': 1, 'char16_t': 1, 'char32_t': 1, 'char8_t': 1,
        'class': 1, 'co_await': 1, 'compl': 1, 'concept': 1, 'const': 1, 'const_cast': 1,
        'consteval': 1, 'constexpr': 1, 'constinit': 1, 'continue': 1, 'co_return': 1, 'co_yield': 1,
        'decltype': 1, 'default': 1, 'delete': 1, 'do': 1, 'double': 1, 'dynamic_cast': 1,
        'else': 1, 'enum': 1, 'explicit': 1, 'export': 1, 'extern': 1, 'false': 1,
        'float': 1, 'for': 1, 'friend': 1, 'goto': 1, 'if': 1, 'inline': 1, 'int': 1,
        'long': 1, 'mutable': 1, 'namespace': 1, 'new': 1, 'noexcept': 1, 'not': 1, 'not_eq': 1,
        'nullptr': 1, 'operator': 1, 'or': 1, 'or_eq': 1, 'private': 1, 'protected': 1, 'public': 1,
        'reflexpr': 1, 'register': 1, 'reinterpret_cast': 1, 'requires': 1, 'return': 1, 'short': 1,
        'signed': 1, 'sizeof': 1, 'static': 1, 'static_assert': 1, 'static_cast': 1, 'struct': 1,
        'switch': 1, 'synchronized': 1, 'template': 1, 'this': 1, 'thread_local': 1, 'throw': 1,
        'true': 1, 'try': 1, 'typedef': 1, 'typeid': 1, 'typename': 1, 'union': 1, 'unsigned': 1,
        'using': 1, 'virtual': 1, 'void': 1, 'volatile': 1, 'wchar_t': 1, 'while': 1,
        'xor': 1, 'xor_eq': 1,
        'j': 1, # this is used in the c++ header
        'yn': 1, # defined in math.h, which something in stl pulls in
    }

    def makeName(maxl):
        while True:
            candidate = ''.join([random.choice(name_letters) for i in range(random.randint(1,maxl)) ])
            if candidate not in cant_use:
                cant_use[candidate] = 1
                return candidate


    # generates a spec that includes members of the base types only,
    # plus any types specified as an argument
    def makeSimple(more_types=[]):
        ms = []
        s = {
           makeName(10): ms    
        }
        elem_count = random.randint(1, 15)
        for i in range(elem_count):
            elem_type = random.choice(list(justbuffers.get_base_types().keys()) + more_types)
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

    # the top-level call makes a struct that can use some of the
    # earlier structs defined
    top = makeSimple(list(s.keys()))
    s.update(top)
    return list(top.keys())[0], s
