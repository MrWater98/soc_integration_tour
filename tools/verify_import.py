#!/usr/bin/env python3
"""Replay selected 19/20 checks from local RTL snapshots without a PDK checkout."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/progress/validation/replay')
    parser.add_argument('--timeout', type=float, default=300,
                        help='Maximum wall-clock seconds per compile or simulation')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").unlink(missing_ok=True)
    rtl = ROOT / 'results/19/rtl'
    chapter19 = ROOT / 'chapters/19-asic-rtl'
    chapter20 = ROOT / 'chapters/20-asic-verification'
    compiler = shutil.which('iverilog')
    simulator = shutil.which('vvp')
    if not compiler or not simulator:
        parser.error('Install Icarus Verilog (iverilog and vvp) first')
    results = []

    def command(arguments, name, expected=None, expect_failure=False):
        try:
            result = subprocess.run(list(map(str, arguments)), cwd=rtl, capture_output=True,
                                    text=True, timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            captured = (exc.stdout or b'') + (exc.stderr or b'')
            if isinstance(captured, bytes):
                captured = captured.decode(errors='replace')
            (output / f'{name}.log').write_text(captured + '\nWALL_CLOCK_TIMEOUT\n')
            raise RuntimeError(f'{name}: exceeded {args.timeout}s; inspect log before retrying') from exc
        text = result.stdout + result.stderr
        (output / f'{name}.log').write_text(text)
        if expected is None:
            passed = result.returncode == 0
        else:
            passed = expected in text and (result.returncode == 0 or expect_failure)
        if not expect_failure:
            passed = passed and 'FATAL:' not in text
        if not passed:
            raise RuntimeError(f'{name} failed: see {output / (name + ".log")}')
        return text

    with tempfile.TemporaryDirectory(prefix='tour-replay-') as temporary:
        temporary = Path(temporary)
        # Each netlist is a separate design with the same top module name.
        for name, sources in (
            ('rtl', ['elaborated.v']),
            ('generic', ['generic.v']),
            ('mapped', ['mapped.v', 'ics55_LLSC_H7CR.v']),
        ):
            executable = temporary / name
            command([compiler, '-g2012', '-Dfunctional', '-s', 'tb', '-o', executable,
                     *[rtl / file for file in sources], chapter19 / 'tb.sv'], f'19-{name}-compile')
            command([simulator, executable], f'19-{name}', 'PASS19')
            results.append({'case': f'19-{name}', 'status': 'PASS'})
        executable = temporary / '20'
        command([compiler, '-g2012', '-DRTL_FAULTS', '-s', 'tb', '-o', executable,
                 rtl / 'elaborated.v', chapter20 / 'tb.sv'], '20-compile')
        for name, options, expected, negative in (
            ('repeated-reset', ['+BOOTS=2'], 'PASS20', False),
            ('missing-ack', ['+FAULT=2'], 'WATCHDOG', True),
            ('wrong-gpio', ['+FAULT=4'], 'FIRMWARE_FAIL result=000000e5', True),
        ):
            command([simulator, executable, *options], f'20-{name}', expected, negative)
            results.append({'case': f'20-{name}', 'status': 'PASS expected failure detected' if negative else 'PASS'})
    summary = {'status': 'PASS selected imported RTL checks', 'cases': results,
               'scope': 'Replay existing snapshots; synthesis, full chapter20 regression and physical signoff not rerun'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
