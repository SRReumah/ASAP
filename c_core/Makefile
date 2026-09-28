CC = gcc
CFLAGS = -Wall -Wextra -O2
LIBS = -lcrypto

TARGET = net_crypto_core
SRC = net_crypto_core.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LIBS)

clean:
	rm -f $(TARGET)
