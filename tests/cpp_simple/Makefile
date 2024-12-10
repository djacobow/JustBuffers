
all: cpp_decoded.json py_decoded.json

cpp_decoded.json: cpp_decoder py_encoded.bin
	./cpp_decoder py_encoded.bin > cpp_decoded.json

cpp_decoder: cpp_decode.cpp types.hpp
	g++ --std=c++17 -o cpp_decoder cpp_decode.cpp

py_encoded.bin: types.json py_encoder.py
	./py_encoder.py types.json py_encoded.bin

py_decoded.json: py_decoder.py cpp_encoded.bin cpp_encoded.json types.json
	./py_decoder.py types.json cpp_encoded.bin cpp_encoded.json py_decoded.json

cpp_encoded.bin cpp_encoded.json: cpp_encoder
	./cpp_encoder cpp_encoded.bin > cpp_encoded.json

cpp_encoder: cpp_encode.cpp types.hpp
	g++ -std=c++17 -o cpp_encoder cpp_encode.cpp

types.h: types.json ../../command.py ../../jb/justbuffers.py
	../../command.py -c types.json --generate-cpp types.hpp

clean:
	rm -f types.h cpp_decoder cpp_encoder *.bin py_decoded.* cpp_decoded.* py_encoded.* cpp_encoded.*

