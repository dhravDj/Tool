#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct PacketHeader {
    int version;
    int payload_length;
};

void copy_buffer_unsafe(const char* input) {
    char dest[64];
    strcpy(dest, input); // Unsafe legacy function to trigger diagnostic
    printf("Copied buffer: %s\n", dest);
}

int calculate_checksum(const char* data, int length) {
    int sum = 0;
    for (int i = 0; i < length; i++) {
        sum += (unsigned char)data[i];
    }
    return sum;
}
