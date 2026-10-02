#include <stdint.h>

volatile uint32_t initialized_data = 0x11223344u; /* 留在 .data：上电后需从 ROM 拷入 RAM */
volatile uint32_t zero_initialized;              /* 留在 .bss：启动代码需清零 */
volatile uint32_t scratch[4];                   /* RAM 测试专用，避免覆盖 .data 变量 */

__attribute__((noinline)) static uint32_t use_stack(uint32_t input) {
    volatile uint32_t local[4] = {input, input + 1, input + 2, input + 3};
    return local[0] + local[3];
}

__attribute__((noinline)) static uint32_t stack_roundtrip(uint32_t input) {
    volatile uint32_t marker = 0x55aau;
    uint32_t result = use_stack(input);
    return result + (marker == 0x55aau ? 0u : 1u);
}

int main(void) {
    uint32_t ok = (initialized_data == 0x11223344u) &&
                  (zero_initialized == 0u) && (scratch[0] == 0u);
    scratch[0] = 0x76543210u;
    ok &= scratch[0] == 0x76543210u;
    ok &= stack_roundtrip(10u) == 23u;
    *(volatile uint32_t *)0x80000ffcu = ok ? 0x5au : 0xe1u;
    for (;;) {}
}
