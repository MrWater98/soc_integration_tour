#!/usr/bin/env python3
"""A small, executable request/response picture; not VexRiscv RTL."""


WAIT_CYCLES = 1
memory = {0x00: 0x04000093, 0x40: 0}


def transfer(name, address, write=False, value=0):
    # The master holds the request and address until the slave asserts ready.
    for cycle in range(WAIT_CYCLES + 1):
        req = 1
        ready = int(cycle == WAIT_CYCLES)  # The endpoint waits before completing the request.
        read_data = memory.get(address, 0) if ready and not write else 0
        print(f"{name:>5} {cycle:>5} {req:>3} 0x{address:02x}  {int(write):>2} "
              f"0x{value:08x} {ready:>5} 0x{read_data:08x}")
        if ready:
            if write:
                memory[address] = value
            print(f"{name:>5} {cycle + 1:>5}   0 0x{address:02x}  {int(write):>2} "
                  f"0x{value:08x}     0 0x00000000")
            return read_data


print("operation cycle req addr  we      wdata ready      rdata")
instruction = transfer("fetch", 0x00)
transfer("write", 0x40, write=True, value=0x40)
stored = transfer("readback", 0x40)
assert instruction == 0x04000093 and stored == 0x40
print("PASS TINY-BUS: fetch, write and readback")
