.PHONY: test clean

test: py_decoded.json
	@echo "** PASS **"

types.h: types.json ../../jb.py ../../jb/justbuffers.py
	@echo "* generate the header from the spec"
	../../jb.py -c types.json --generate-c types.h

c_encoder: c_encode.c types.h
	@echo "* compile the c encoder program"
	gcc -o c_encoder c_encode.c

c_decoder: c_decode.c types.h
	@echo "* compile the c decoder program"
	gcc -o c_decoder c_decode.c

c_encoded.bin c_encoded.json: c_encoder
	@echo "* run the c encoder program to generate .bin and .json files"
	./c_encoder c_encoded.bin > c_encoded.json

py_encoded.bin: py_encoder.py types.json ../../jb/justbuffers.py
	@echo "* run the py_encoder program that also generates a .bin that"
	@echo "  should match the one from the c program"
	./py_encoder.py types.json py_encoded.bin

c_decoded.json: c_decoder py_encoded.bin
	@echo "* run a c decoder program which reads the python-generated"
	@echo "  .bin file and generates a decoded .json file"
	./c_decoder py_encoded.bin > c_decoded.json

py_decoded.json: py_decoder.py c_encoded.bin c_encoded.json c_decoded.json
	@echo "* run the python decoder with the c generated files and"
	@echo "  make a new python decoded .json file, compare the values"
	./py_decoder.py types.json c_encoded.bin c_encoded.json py_decoded.json

clean:
	@echo "* cleanup"
	rm -f types.h c_decoder c_encoder *.bin py_decoded.* c_decoded.* py_encoded.* c_encoded.*
