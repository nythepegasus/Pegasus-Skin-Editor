CC ?= gcc
CFLAGS = -O2 $$(pkg-config --cflags raylib)
LIBS = $$(pkg-config --libs raylib)

.PHONY: clean

main: src/main.c
	$(CC) -o $@ $(CFLAGS) $(LIBS) $?

clean:
	rm -fr main
