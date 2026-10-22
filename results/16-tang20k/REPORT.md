# Tang Primer 20K：VexRiscv SoC 实物首次运行

PASS：WSL USB 枚举、JTAG 识别 Gowin GW2A(R)-18(C)、配置 SRAM 下载、实际 UART 捕获。

UART 115200 8N1，使用 if01，实际收到 `14 HELLO: CPU reached main; LEDs are mapped`、初始 `BUTTONS=0x00000000` 与持续 `14 ALIVE`。

用户已确认：心跳 LED 闪烁、S1 按下/松开时 UART 值与 LED 一致、S0 复位后重新出现 HELLO 并继续 ALIVE。

基本 CPU/UART/GPIO/复位实物检查通过。断电重下载待验证；DDR3 和其余 SoC 功能尚未完成实物验证。
