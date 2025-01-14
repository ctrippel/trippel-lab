
// To run this program:
//
// <symcc_base_dir>/build/symcc -o test program2.c
// echo -ne "\x00\x00\x00\x00\x00\x00\x00\x00" > input.cmd
// ./test < input.cmd

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  int x;
  if (read(STDIN_FILENO, &x, sizeof(x)) != sizeof(x)) {
    fprintf(stderr, "Failed to read x\n");
    return -1;
  }

  int y;
  if (read(STDIN_FILENO, &y, sizeof(y)) != sizeof(y)) {
    fprintf(stderr, "Failed to read x\n");
    return -1;
  }

  int z = y * x;
  z = z * z;

  if ( z < 0 ) {
    printf("yes\n");
  } else {
    printf("no\n");
  }
  
  return 0;
}
