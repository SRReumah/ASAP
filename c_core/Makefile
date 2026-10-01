CC = gcc
CFLAGS = -Wall -O2
TARGET = net_crypto_core
SRC = net_crypto_core.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

clean:
	rm -f $(TARGET) net_crypto_core.exe