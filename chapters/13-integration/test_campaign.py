"""Check that the regression checker detects corruption, not just happy paths."""
import unittest
from campaign import memory_scoreboard
from run import workload_sequence


class CheckerTests(unittest.TestCase):
    def test_byte_selected_write_and_read(self):
        for lane in range(4):
            expected = (0x11223344 & ~(255 << (lane * 8))) | (0xaa << (lane * 8))
            log = ("MEMORY_TRANSACTION adr=0x04000000 we=1 sel=f write=0x11223344 read=0x00000000\n"
                   f"MEMORY_TRANSACTION adr=0x04000000 we=1 sel={1 << lane:x} write=0x{0xaa << (lane*8):08x} read=0x00000000\n"
                   f"MEMORY_TRANSACTION adr=0x04000000 we=0 sel=f write=0x00000000 read=0x{expected:08x}\n")
            self.assertEqual(memory_scoreboard(log), ({lane}, 1))
            corrupted = log.replace(f"read=0x{expected:08x}", "read=0xdeadbeef")
            with self.assertRaisesRegex(AssertionError, "SRAM scoreboard"):
                memory_scoreboard(corrupted)

    def test_read_before_known_write_does_not_claim_coverage(self):
        log = "MEMORY_TRANSACTION adr=0x04000000 we=0 sel=f write=0x00000000 read=0xdeadbeef\n"
        self.assertEqual(memory_scoreboard(log), (set(), 0))

    def test_prng_matches_published_xorshift32_vector(self):
        self.assertEqual(workload_sequence(1, 5), [270369, 67634689, 2647435461, 307599695, 2398689233])


if __name__ == "__main__": unittest.main()
