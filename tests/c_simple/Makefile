
all: c_decoded.txt py_decoded.json

c_decoded.txt: c_decoder py_encoded.bin
	./c_decoder py_encoded.bin > c_decoded.txt

c_decoder: c_decode.c types.h
	gcc -o c_decoder c_decode.c

py_encoded.bin: types.json py_encoder.py
	./py_encoder.py types.json py_encoded.bin

py_decoded.json: py_decoder.py c_encoded.bin types.json
	./py_decoder.py types.json c_encoded.bin py_decoded.json

c_encoded.bin: c_encoder
	./c_encoder c_encoded.bin

c_encoder: c_encode.c types.h
	gcc -o c_encoder c_encode.c

types.h: types.json
	../../command.py -c types.json --generate-c types.h

clean:
	rm -f types.h c_decoder c_encoder *.bin py_decoded.* c_decoded.* py_encoded.* c_encoded.*

