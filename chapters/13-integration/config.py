"""Chapter 13's single source of hardware parameters and test limits."""
from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class Config:
    sys_clk_hz: int = 1_000_000
    baud: int = 100_000
    gpio_width: int = 4
    rom_size: int = 16 * 1024
    sram_size: int = 4 * 1024
    main_ram_size: int = 16 * 1024
    stack_size: int = 2048
    stack_guard: int = 16
    uart_fifo_depth: int = 4
    response_wait: int = 8
    timer_period: int = 8000
    stress_bytes: int = 128
    minimum_irqs: int = 3
    poll_limit: int = 20000
    max_cycles: int = 2_000_000
    completion_base: int = 0x80000000
    completion_size: int = 4096
    spi_command: int = 0x9f
    spi_reply: int = 0xa5
    i2c_address: int = 0x42

    def validate(self):
        if not 1 <= self.gpio_width <= 32:
            raise ValueError("gpio_width must be in 1..32")
        if self.sys_clk_hz <= 0 or self.baud <= 0 or self.sys_clk_hz % self.baud:
            raise ValueError("this serial monitor requires an integral sys_clk_hz/baud")
        if self.bit_cycles < 8:
            raise ValueError("serial monitor requires at least 8 clocks per bit")
        for name in ("rom_size", "sram_size", "main_ram_size", "completion_size"):
            size = getattr(self, name)
            if size < 256 or size & (size - 1):
                raise ValueError(f"{name} must be a power of two >= 256 bytes")
        if self.completion_base % self.completion_size:
            raise ValueError("completion region must align to its size")
        if self.stack_size < 256 or self.stack_size % 16 or self.stack_guard < 16 or self.stack_guard % 16:
            raise ValueError("stack budget/guard must meet this RV32 ABI's 16-byte alignment")
        if self.stack_size + self.stack_guard + 1024 >= self.main_ram_size:
            raise ValueError("main RAM must also accommodate data, scratch, and stack")
        if not 4 <= self.response_wait <= 255:
            raise ValueError("response_wait must be in 4..255 for the bus-reset experiment")
        if not 1 <= self.uart_fifo_depth <= 256:
            raise ValueError("uart_fifo_depth must be in 1..256")
        if not 0x08 <= self.i2c_address < 0x78:
            raise ValueError("use an unreserved 7-bit I2C address")
        if not 0 <= self.spi_command <= 255 or not 0 <= self.spi_reply <= 255:
            raise ValueError("SPI model command and reply are bytes")
        if self.timer_period < 1000 or self.timer_period >= 2**32:
            raise ValueError("timer_period must fit 32 bits and leave time for this ISR")
        if min(self.stress_bytes, self.minimum_irqs, self.poll_limit, self.max_cycles) <= 0:
            raise ValueError("test counts and timeouts must be positive")
        return self

    @property
    def bit_cycles(self):
        return self.sys_clk_hz // self.baud

    @property
    def values(self):
        return asdict(self)

    @property
    def digest(self):
        return hashlib.sha256(json.dumps(self.values, sort_keys=True).encode()).hexdigest()

    @property
    def tag(self):
        return int(self.digest[:8], 16)

    @property
    def regions(self):
        return {"rom": (0, self.rom_size), "sram": (0x10000000, self.sram_size),
                "main_ram": (0x40000000, self.main_ram_size),
                "completion": (self.completion_base, self.completion_size),
                "csr": (0xf0000000, 65536)}

    def write_firmware_inputs(self, out):
        """C macros and linker layout follow the selected hardware configuration."""
        constants = {
            "CONFIG_TAG": self.tag, "ROM_BYTES": self.rom_size,
            "SRAM_BASE": self.regions["sram"][0], "SRAM_BYTES": self.sram_size,
            "MAIN_RAM_BASE": self.regions["main_ram"][0], "MAIN_RAM_BYTES": self.main_ram_size,
            "COMPLETION_BASE": self.completion_base,
            "DONE_ADDRESS": self.completion_base + self.completion_size - 4,
            "GPIO_MASK": (1 << self.gpio_width) - 1,
            "GPIO_PATTERN": (1 << self.gpio_width) - 1,
            "GPIO_INPUT_PATTERN": 0x55555555 & ((1 << self.gpio_width) - 1),
            "TIMER_PERIOD": self.timer_period, "STRESS_BYTES": self.stress_bytes,
            "MINIMUM_IRQS": self.minimum_irqs, "POLL_LIMIT": self.poll_limit,
            "SPI_COMMAND": self.spi_command, "SPI_REPLY": self.spi_reply,
            "I2C_ADDRESS": self.i2c_address,
        }
        (out / "test_config.h").write_text("#pragma once\n" + "".join(
            f"#define {key} 0x{value:x}u\n" for key, value in constants.items()))
        linker = f"""OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY {{
    rom (rx) : ORIGIN = 0, LENGTH = {self.rom_size - 16}
    main_ram (rwx) : ORIGIN = 0x40000000, LENGTH = {self.main_ram_size}
}}
SECTIONS {{
    .text : {{ KEEP(*(.text.init)) *(.text .text.*) *(.rodata .rodata.*) }} > rom
    .data : ALIGN(4) {{ __data_start = .; *(.data .data.* .sdata .sdata.*) . = ALIGN(4); __data_end = .; }} > main_ram AT > rom
    __data_load_start = LOADADDR(.data);
    .bss (NOLOAD) : ALIGN(4) {{ __bss_start = .; *(.bss .bss.* .sbss .sbss.* COMMON) . = ALIGN(4); __bss_end = .; }} > main_ram
    __stack_top = ORIGIN(main_ram) + LENGTH(main_ram) - {self.stack_guard};
    __stack_bottom = __stack_top - {self.stack_size};
    ASSERT(__bss_end <= __stack_bottom, "sections overlap the configured stack budget")
    /DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
"""
        (out / "linker.ld").write_text(linker)
