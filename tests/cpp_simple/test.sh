#!/usr/bin/env -S bash -e


echo
echo "* cleanup from last run"
rm -f types.h cpp_decoder cpp_encoder *.bin py_decoded.* cpp_decoded.* py_encoded.* cpp_encoded.*

echo
echo "* generate the header from the spec"
../../jb.py -c types.json --generate-cpp types.hpp

echo
echo "* compile the c++ test programs"
g++ --std=c++17 -o cpp_encoder cpp_encode.cpp
g++ --std=c++17 -o cpp_decoder cpp_decode.cpp

echo
echo "* run the c++ encoded program to generate .bin and .json files"
./cpp_encoder cpp_encoded.bin > cpp_encoded.json

# run a python script that also generartes a bin file that should
# match the one from the c++ program
echo
echo "* run the py_encoder program that also generates a .bin that"
echo "  should match the one from the c++ program"
./py_encoder.py types.json py_encoded.bin

echo
echo "* run a c++ decoder program which reads the python-generated"
echo "  .bin file and generates a decoded .json file"
./cpp_decoder py_encoded.bin > cpp_decoded.json

echo
echo "* run the python decoder with the cpp generated files and"
echo "  make a new python decoded .json file, compare the values"
./py_decoder.py types.json cpp_encoded.bin cpp_encoded.json py_decoded.json

echo
echo "* finally bulk check that athe json files are identical"
../../jb/jscompare.py -a py_decoded.json -b cpp_encoded.json

echo
echo "** PASS **"
