#!/usr/bin/env python3

import sys
import datetime
from .. import util

def generate(typeinfo, elaborated):
    os = [ f'''
#pragma once
/* 
   This file was generated by {sys.argv[0]} at {datetime.datetime.now().isoformat()}
   * DO NOT EDIT *
*/

#include <stdint.h>
#include <stdbool.h>
#ifndef STATIC_ASSERT
   #define STATIC_ASSERT(test) typedef char assertion_on_struct[(!!(test))*2-1]
#endif
    ''' ]

    for t_name, t_info in elaborated.items():
        os.append(f'typedef struct {t_name} {{')
        for m_info in t_info['members']:
            if util.is_scalar(m_info):
                a_str = '';
            else:
                a_str = '[' + ']['.join([str(x) for x in m_info['counts']]) + ']'
            name_str = ''.join([m_info['name'], a_str, ';'])
            c_type_name = typeinfo.get(m_info['type'], {'c_type': m_info['type'] })['c_type']
            os.append(f'  {c_type_name:20} {name_str:20} // offset 0x{m_info["offset"]:x}, align 0x{m_info["align"]:x}, size 0x{m_info["size"]:x}')
        os.append(
f'''}} {t_name};

STATIC_ASSERT(sizeof({t_name}) == 0x{t_info["size"]:x});
'''     )

    return '\n'.join(os)
