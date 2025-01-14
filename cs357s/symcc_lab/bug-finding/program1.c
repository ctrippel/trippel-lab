
// To run this program:
//
// <symcc_base_dir>/build/symcc -o test program1.c
// echo -ne "\x00\x00\x00\x00\x00\x00\x00\x00" > input.cmd
// ./test < input.cmd

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <stdbool.h>

bool foo(size_t x) {

  return x < 0;

}

int main(int argc, char *argv[]) {
  int x;
  if (read(STDIN_FILENO, &x, sizeof(x)) != sizeof(x)) {
    fprintf(stderr, "Failed to read x\n");
    return -1;
  }

  fprintf(stdout,"Result is %s\n.", (foo(x)) ? "true" : "false");
  
  return 0;
}
