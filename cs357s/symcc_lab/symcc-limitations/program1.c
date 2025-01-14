// To run this program:
//
// <symcc_base_dir>/build/symcc -o test program1.c
// echo -ne '\x00\x00\x00\x00' > input.cmd
// ./test < input.cmd


#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>

int find(int i) {
    int arr[10] = {0,1,2,3,4,5,6,7,8,9};

    if (i < 0 || i > 9) {
        return 2;
    } else if (arr[i] == 5) {
        return 1;
    } else {
        return 0;
    }

}

int main(int argc, char* argv[]) {
    int x;
    if (read(STDIN_FILENO, &x, sizeof(x)) != sizeof(x)) {
        printf("Failed to read x\n");
        return -1;
    }

    find(x);
    
    return 0;
}
