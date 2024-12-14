#!/usr/bin/env -S bash -e


echo
echo "* cleanup from last run"
rm -f types.h c_decoder c_encoder *.bin py_decoded.* c_decoded.* py_encoded.* c_encoded.*

echo
echo "* generate the header from the spec"
../../jb.py -c types.json --generate-c types.h

echo
echo "* compile the c++ test programs"
gcc -o c_encoder c_encode.c
gcc -o c_decoder c_decode.c

echo
echo "* run the c++ encoded program to generate .bin and .json files"
./c_encoder c_encoded.bin > c_encoded.json

# run a python script that also generartes a bin file that should
# match the one from the c++ program
echo
echo "* run the py_encoder program that also generates a .bin that"
echo "  should match the one from the c++ program"
./py_encoder.py types.json py_encoded.bin

echo
echo "* run a c++ decoder program which reads the python-generated"
echo "  .bin file and generates a decoded .json file"
./c_decoder py_encoded.bin > c_decoded.json

echo
echo "* run the python decoder with the cpp generated files and"
echo "  make a new python decoded .json file, compare the values"
./py_decoder.py types.json c_encoded.bin c_encoded.json py_decoded.json

echo
echo "** PASS **"
