#include <stdio.h>
__attribute__((noinline)) int fact(int n) {
    if (n <= 1) return 1;
    int child = fact(n - 1);
    return n * child;
}
int main(void) {
    int answer = fact(3);
    printf("fact(3)=%d\n", answer);
    return answer == 6 ? 0 : 1;
}
