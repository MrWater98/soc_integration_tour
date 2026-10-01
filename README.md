# SoC Integration Tour

A reproducible, step-wise hardware integration project built around LiteX and a single-core VexiiRiscv. The first seven stages bring up the toolchain, verify Wishbone behavior, boot firmware from ROM, add writable SRAM and address decoding, then move the design into LiteX `SoCCore` and `Builder`.

Each stage has a standalone implementation and run command. Generated logs, firmware images, maps, and waveforms are written under `results/` and are excluded from Git.

## Project stages

| Stage | Integration result | Run |
| --- | --- | --- |
| 00 Environment | Pinned LiteX/VexiiRiscv toolchain and host simulator checks | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU bring-up | Native VexiiRiscv reset, ROM fetch, store, and missing-ACK behavior | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | Standalone slave transaction and response fault checks | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | Compiled firmware image, reset mapping, execution completion | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | Writable memory, byte lanes, stack use, and out-of-range fault | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 Memory map | ROM/SRAM/register decode, map overlap and unmapped-access checks | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`/`Builder` integration and generated-map verification | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |

Stage 00 documents the supported Linux setup and pinned source versions. Each chapter also provides `README_zh.md` with the same stage contract in Chinese; `README.md` is the primary project reference.

## Engineering gates

1. Do not integrate a new block until the preceding run command passes from a clean `results/` directory.
2. A generated address map is checked against the firmware contract before simulation.
3. A simulation gate requires an explicit completion marker; a successful Python build alone is insufficient.
4. Negative tests must report the expected fault and must not emit the normal completion marker.
5. Keep each stage runnable from the repository root without importing code from another stage.

See [PLAN.md](PLAN.md) for scope, interface decisions, and later integration stages.
