.PHONY: test clean

test: verify_compare
	@echo "** PASS **"

types.hpp: types.json ../../jb.py ../../jb/justbuffers.py
	@echo "* generate the header from the spec"
	../../jb.py -c types.json --generate-cpp types.hpp

cpp_encoder: cpp_encode.cpp types.hpp
	@echo "* compile the cpp encoder program"
	g++ --std=c++17 -o cpp_encoder cpp_encode.cpp

cpp_decoder: cpp_decode.cpp types.hpp
	@echo "* compile the cpp decoder program"
	g++ --std=c++17 -o cpp_decoder cpp_decode.cpp

cpp_encoded.bin cpp_encoded.json: cpp_encoder
	@echo "* run the cpp encoder program to generate .bin and .json files"
	./cpp_encoder cpp_encoded.bin > cpp_encoded.json

py_encoded.bin: py_encoder.py types.json ../../jb/justbuffers.py
	@echo "* run the py_encoder program that also generates a .bin that"
	@echo "  should match the one from the cpp program"
	./py_encoder.py types.json py_encoded.bin

cpp_decoded.json: cpp_decoder py_encoded.bin
	@echo "* run a cpp decoder program which reads the python-generated"
	@echo "  .bin file and generates a decoded .json file"
	./cpp_decoder py_encoded.bin > cpp_decoded.json

py_decoded.json: py_decoder.py cpp_encoded.bin cpp_encoded.json cpp_decoded.json
	@echo "* run the python decoder with the cpp generated files and"
	@echo "  make a new python decoded .json file, compare the values"
	./py_decoder.py types.json cpp_encoded.bin cpp_encoded.json py_decoded.json

verify_compare: py_decoded.json cpp_encoded.json
	@echo "* finally bulk check that the json files are identical"
	../../jb/jscompare.py -a py_decoded.json -b cpp_encoded.json

clean:
	@echo "* cleanup"
	rm -f types.hpp cpp_decoder cpp_encoder *.bin py_decoded.* cpp_decoded.* py_encoded.* cpp_encoded.*
