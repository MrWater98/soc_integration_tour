# 13A TAP 验证

PASS：10 个场景；状态转移 32/32；IR 4 位；示例 IDCODE 0x12345679。

- idcode: PASS
- capture-ir: PASS
- user-register: PASS
- bypass: PASS
- wrong-ir: PASS WRONG_IR_READBACK
- short-scan: PASS SHORT_SCAN
- wrong-bit-order: PASS WRONG_BIT_ORDER
- reset-during-scan: PASS RESET_INTERRUPTED_SCAN
- pause-resume: PASS
- all-state-edges: PASS
