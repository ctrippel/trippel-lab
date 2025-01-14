// To run this program:
//
// <symcc_base_dir>/build/symcc -o test program2.c
// echo -ne "helloworld" > input.cmd
// ./test < input.cmd

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  char string1[6];
  int n1 = read(STDIN_FILENO, string1, 5);
  string1[n1] = '\0';

  char string2[6];
  int n2 = read(STDIN_FILENO, string2, 5);
  string2[n2] = '\0';

  if (strncmp(string1,string2,6) == 0) printf("Strings are the same\n");
  else printf("Strings are different\n");

  return 0;
}
