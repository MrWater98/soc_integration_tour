"""Purchased board facts and adjustable tutorial settings."""
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Config:
    reference_clk_hz: int = 27_000_000
    sys_clk_hz: int = 54_000_000
    baud: int = 115200
    led_count: int = 1
    button_count: int = 1
    blink_hz: int = 1
    rom_size: int = 8192
    sram_size: int = 4096
    main_ram_size: int = 16384
    stack_size: int = 1024
    por_cycles: int = 65536
    def validate(self):
        if self.reference_clk_hz != 27_000_000: raise ValueError('board oscillator is 27 MHz')
        # Software experiment limit; PLL feasibility and timing are checked separately.
        if not 10_000_000 <= self.sys_clk_hz <= 120_000_000: raise ValueError('tutorial experiment range 10..120 MHz; PLL and timing still require checks')
        if self.led_count != 1 or self.button_count != 1: raise ValueError('this first board profile uses LED4 heartbeat, LED5 CPU output and button1; extend the verified pin profile to change IO count')
        if self.blink_hz <= 0 or self.sys_clk_hz % (2*self.blink_hz): raise ValueError('invalid heartbeat half-period')
        if not 1 <= self.baud <= self.sys_clk_hz//8: raise ValueError('invalid baud rate')
        if self.por_cycles < 16: raise ValueError('power-on reset must last at least 16 reference cycles in this example')
        for field in ('rom_size','sram_size','main_ram_size'):
            value=getattr(self,field)
            if value < 1024 or value & (value-1):raise ValueError(f'{field} must be a power of two >= 1024')
        if self.stack_size<256 or self.stack_size%16 or self.stack_size+1024>=self.main_ram_size:raise ValueError('invalid stack budget')
        return self
    @property
    def values(self):return asdict(self)
    @property
    def half_period(self):return self.sys_clk_hz//(2*self.blink_hz)
    @property
    def regions(self):return {'rom':(0,self.rom_size),'sram':(0x10000000,self.sram_size),'main_ram':(0x40000000,self.main_ram_size),'csr':(0xf0000000,65536)}
