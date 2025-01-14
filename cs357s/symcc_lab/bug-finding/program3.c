
// To run this program:
//
// <symcc_base_dir>/build/symcc -o test program3.c
// echo -ne "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" > input.cmd
// ./test < input.cmd

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>

char cmp_values[] = {0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99};

int main(int argc, char *argv[]) {
  char buffer[10];

  printf("===== First read =====\n");
  // Read characters from stdin
  int n1 = read(STDIN_FILENO, buffer, 10);

  // Compare with cmp_values
  if (memcmp(buffer,cmp_values,10) == 0) {
    printf("yes\n");
  } else {
    printf("no\n");
  }

  printf("\n\n===== Second read =====\n");
  // Read more characters from stdin
  int n2 = read(STDIN_FILENO, buffer, 10);

  // Make sure everything in the buffer is 0.
  for (size_t i = 0; i < n2; i++) {
    assert (buffer[i] == 0);
  }

  // Compare with cmp_values
  if (memcmp(buffer,cmp_values,10) == 0) {
    printf("yes\n");
  } else {
    printf("no\n");
  }


  
  return 0;
}
