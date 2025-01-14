// To run this program:
//
// <symcc_base_dir>/build/symcc -o test program3.c
// echo -ne "" > input.cmd
// ./test < input.cmd

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  uint8_t *buf = (uint8_t *)calloc(5,0);
  int n1 = read(STDIN_FILENO, buf, 5);

  if (buf[2] == 'a') printf("found\n");
  else printf("not found\n");

  return 0;
}
