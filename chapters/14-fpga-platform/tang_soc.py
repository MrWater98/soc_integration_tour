"""Tang Primer 20K Dock target; on-chip RAM, real UART and two verified 3.3V LEDs."""
from migen import ClockDomain, If, Signal
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.gen import LiteXModule
from litex.soc.cores.clock.gowin_gw2a import GW2APLL
from litex.soc.integration.soc_core import SoCCore
from litex_boards.platforms import sipeed_tang_primer_20k
from io_cores import Heartbeat, ButtonInput, LEDOutput

class CRG(LiteXModule):
    def __init__(self,platform,cfg):
        self.cd_por=ClockDomain('por',reset_less=True)
        self.cd_sys=ClockDomain('sys')
        clk=platform.request('clk27')
        reset_n=platform.request('btn_n',0)
        self.comb += self.cd_por.clk.eq(clk)
        counter=Signal(max=cfg.por_cycles+1,reset=cfg.por_cycles)
        self.sync.por += If(~reset_n,counter.eq(cfg.por_cycles)).Elif(counter!=0,counter.eq(counter-1))
        self.pll=pll=GW2APLL(devicename=platform.devicename,device=platform.device)
        self.comb += pll.reset.eq((counter!=0)|~reset_n)
        pll.register_clkin(clk,cfg.reference_clk_hz)
        pll.create_clkout(self.cd_sys,cfg.sys_clk_hz,margin=0,with_reset=False)
        self.specials += AsyncResetSynchronizer(self.cd_sys,pll.reset|~pll.locked)

class BoardSoC(SoCCore):
    csr_map={'uart':0,'leds':1,'buttons':2,'identifier_mem':3}
    def __init__(self,cfg,rom_words):
        platform=sipeed_tang_primer_20k.Platform(dock='standard',toolchain='apicula')
        # Preserve JTAG and flash pins. LED4/5 reuse READY/DONE, so only those two become GPIO.
        for name in list(platform.toolchain.options):
            if name.startswith('use_'):platform.toolchain.options[name]=int(name in ('use_ready_as_gpio','use_done_as_gpio'))
        super().__init__(platform,clk_freq=cfg.sys_clk_hz,
            cpu_type='vexriscv',cpu_variant='standard',cpu_reset_address=0,
            integrated_rom_size=cfg.rom_size,integrated_rom_init=rom_words,
            integrated_sram_size=cfg.sram_size,integrated_main_ram_size=cfg.main_ram_size,
            with_uart=True,uart_name='serial',uart_baudrate=cfg.baud,
            with_timer=False,with_ctrl=False,ident='Tutorial Tang Primer 20K Dock')
        self.crg=CRG(platform,cfg)
        heartbeat=Signal()
        self.comb += platform.request('led',4).eq(~heartbeat)
        self.add_module('heartbeat',Heartbeat(heartbeat,cfg.half_period))
        led=Signal()
        self.comb += platform.request('led',5).eq(~led)
        self.add_module('leds',LEDOutput(led))
        self.add_module('buttons',ButtonInput(~platform.request('btn_n',1)))
