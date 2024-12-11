# Just Buffers

You've tried the rest, now try the best!

## What are Just Buffers?

Just Buffers are just ... buffers. Or, more precisely, they are "C"
structs. These are the same structs that you might write yourself
to hold hour data, except that they are generated for you from a
specification. This allows for a few good things to happen:

* you get automatic Python support for encoding and decoding
* you get clear indications where alignment rules have created gaps
* you only have to specify them in one file, and everything comes
  from.

The philosophy of Just Buffers is simple: the C struct is kept
simple and straighforward, so that from C using them is basically
frictionnless and without overhead. At the same time, Python has
easy access to blobs of data in Just Buffers form.

## What about protobuf / nanopb / CapnProto / JSON ...

All of those are wonderful tools, but I created Just Buffers because
I found those tools to be fussier than I needed or wanted for most
applications. They solved more problems (like validation) than I
needed, and they came at a cost: special compilers, and compilation
steps, etc.

On the other hand, Just Buffers is implemented in simple Python
with NO dependencies whatsoever. This means that no matter your
system and configuration and whatever else you've got going on,
if you have Python running at all, you can use Just Buffers.

## How does it work?

The Just Buffers python module reads a simple specification,
usually as JSON, and can immediately be used to encode and decode
buffers. If you want to generate a header file for C or C++,
you can call appropriate functions to do that.

There is also a command-line version of Just Buffers here, called
`command.py`

For example, let's say we have the following specification in a file called `spec.json`:

```json
{
    "t0_t": [
        { "type": "u32", "name": "fee" },
        { "type": "u16", "name": "fi" },
        { "type": "u64", "name": "fo" },
        { "type": "u8",  "name": "fum", "counts": 128 }
    ],
    "t1_t": [
        { "type": "t0_t", "name": "t0s", "counts": [2,2] },
        { "type": "u16", "name": "blee" }
    ]
}
```

You could run:

```sh
$ ./command.py -c spec.json --generate-c structs.h
```

That would create a file like this one:
```c
#pragma once
/* 
   This file was generated by ./command.py at 2024-12-11T03:02:03.701712
   * DO NOT EDIT *
*/

#include <stdint.h>
#include <stdbool.h>
#ifndef STATIC_ASSERT
   #define STATIC_ASSERT(test) typedef char assertion_on_struct[(!!(test))*2-1]
#endif
    
typedef struct  t0_t {
  uint32_t             fee;                 // offset 0x0, align 0x4, size 0x4
  uint16_t             fi;                  // offset 0x4, align 0x2, size 0x2
  uint8_t              __pad_0[2];          // offset 0x6, align 0x1, size 0x2
  uint64_t             fo;                  // offset 0x8, align 0x8, size 0x8
  uint8_t              fum[128];            // offset 0x10, align 0x1, size 0x80
} t0;

STATIC_ASSERT(sizeof(t0) == 0x90);

typedef struct  t1_t {
  t0_t                 t0s[2][2];           // offset 0x0, align 0x8, size 0x240
  uint16_t             blee;                // offset 0x240, align 0x2, size 0x2
  uint8_t              __pad_0[6];          // offset 0x242, align 0x1, size 0x6
} t1;

STATIC_ASSERT(sizeof(t1) == 0x248);
```

That asserts in this header are there as a check that the C compiler and
Just Buffers agree about the layout. If they fail, it means there is a 
bug in Just Buffers.

Anyway, you can use this header and its structs in your program and you could,
save them to a file or write them to a socket or whatever. Perhaps, something
like this:

```c
#include <stdio.h>
#include <stlib.h>
#include "struct.h"

int main(int argc, char *argv[]) {
    t1_t t = {};

    // do whatever with t
    FILE *f = fopen("bloop.bin", "wb");
    fwrite(&t, 1, sizeof(t), f);
    fclose(f);
    return 0;
}
```

Later on, in python you could do:
```python

import jb.justbuffers as jb
class JustBufferator():

j = jb.JustBufferator(json.loads(open('types.json','r').read()))
decoded = j.decodeBuffer('t1_t', open('bloop.bin','rb').read())
```

Anyway, that's pretty much the gist.

## Portability

### endianness

Just Buffers do not encode their endianness. By default, they are 
little-endian, but you can also specify big-endian. This only affects
the python decoder and encoder functions. The C struct is left alone,
so the data will be LE or BE depending on the platform you compile it
on.

If you need to maintain endianness, then you will have to use `ntoa`-
and `aton`-like functions on each member access.

However, there aren't many BE machines out there these days, so this
may not be a common problem.

### sizes

All the member types have explicit sizes using stdint.h, so there is
never any doubt as to their size.

### strings

Strings as such are not supported, the same as in C. You can, of course,
make a fixed size `int8_t` array and put text data in it.

### alignment

Just Buffers does respect and follow the C alignment rules, so there
should never be any issues with that. If you insist on packed structs,
you can pass a `packed` flag to the JustBufferator constructor and 
you'll get packed behavior.

### C++

The normal header files from `.generateCHeader()` should be compatible
with c++. However, there is also a function called `.generateCPPHeader()`.
This will create a file that include `nlohmann::json` and code so that
the structs have the ability to be converted to or from JSON. If this is
something you need, by all means use it.

## Tests

There are some tests in the `tests/` directory. They can be run by
running `make`. 

