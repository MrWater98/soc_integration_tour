#!/usr/bin/env python3
"""Compare nextpnr algorithms on a frozen chapter-14 netlist."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import time

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parents[1]
PROFILES = {
    'heap-default': [],
    'heap-router1': ['--router', 'router1'],
    'heap-router2': ['--router', 'router2'],
    'heap-weight20': ['--timingweight', '20'],
    'heap-crit3': ['--critexp', '3'],
    'heap-router2-ripup': ['--router', 'router2', '--tmg-ripup'],
    'heap-router2-alt': ['--router', 'router2', '--router2-alt-weights'],
    'static-router2': ['--placer', 'static', '--router', 'router2'],
    'sa-router2': ['--placer', 'sa', '--router', 'router2'],
    'heap-weight30': ['--timingweight', '30'],
    'heap-weight40': ['--timingweight', '40'],
    'heap-weight20-beta80': ['--timingweight', '20', '--beta', '0.8'],
    'heap-weight20-crit3': ['--timingweight', '20', '--critexp', '3'],
}


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/14e-algorithms')
    parser.add_argument('--profiles', default=','.join(list(PROFILES)[:9]))
    parser.add_argument('--analyze-existing', action='store_true', help='reclassify saved cases and rebuild aggregate without rerunning PNR')
    parser.add_argument('--seeds', default='2,5,8')
    parser.add_argument('--timeout', type=float, default=600)
    args = parser.parse_args()
    names = args.profiles.split(',')
    if len(set(names)) != len(names) or any(n not in PROFILES for n in names):
        parser.error('profiles must be distinct names from ' + ','.join(PROFILES))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prior_summary = json.loads((out/'summary.json').read_text()) if args.analyze_existing and (out/'summary.json').exists() else None
    started = time.monotonic()
    configuration = {'profiles': {n: PROFILES[n] for n in names}, 'seeds': args.seeds,
                     'target_mhz': 150, 'parallel_profiles': 2, 'jobs_per_profile': 2,
                     'per_case_timeout_seconds': args.timeout, 'hardware': 'NOT_RUN',
                     'input_reference': 'results/15-tang20k-150mhz/netlist.json'}
    write(out/'config.json', configuration)

    def profile(name):
        directory = out/name
        directory.mkdir(exist_ok=True)
        command = [sys.executable, str(CHAPTER/'run.py'), '--output', str(directory),
                   '--seeds', args.seeds, '--timeout', str(args.timeout), '--jobs', '2'] + PROFILES[name]
        if args.analyze_existing:
            command += ['--analyze-existing', '--replay']
        write(directory/('analysis-command.json' if args.analyze_existing else 'profile-command.json'), command)
        print('START ' + name, flush=True)
        with (directory/('analysis.log' if args.analyze_existing else 'driver.log')).open('w') as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        path = directory/'summary.json'
        if not path.exists():
            result = {'profile': name, 'status': 'DRIVER_ERROR', 'exit_code': process.returncode}
        else:
            summary = json.loads(path.read_text())
            result = {'profile': name, 'exit_code': process.returncode, 'status': summary['status'],
                      'best': summary['best'], 'valid_runs': summary['valid_runs'],
                      'target_passes': summary['target_passes'],
                      'median_mhz': summary['median_limiting_fmax_mhz'],
                      'results': summary['results'], 'configuration': summary['configuration']}
        best = result.get('best')
        print(f"DONE {name}: best={best['limiting_fmax_mhz'] if best else 'N/A'} MHz", flush=True)
        return result

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = [pool.submit(profile, name) for name in names]
        for future in concurrent.futures.as_completed(pending):
            results.append(future.result())
            write(out/'progress.json', results)
    results.sort(key=lambda r: names.index(r['profile']))
    valid = [r for r in results if r.get('best')]
    best = max(valid, key=lambda r: r['best']['limiting_fmax_mhz']) if valid else None
    summary = {'configuration': configuration, 'profiles': results, 'best_profile': best,
               'wall_seconds': time.monotonic()-started,
               'target_passes': sum(r.get('target_passes', 0) for r in results),
               'total_cases': sum(len(r.get('results', [])) for r in results),
               'valid_runs': sum(r.get('valid_runs', 0) for r in results),
               'hardware': 'NOT_RUN', 'bitstream': 'NOT_PACKED'}
    if prior_summary:
        summary['analysis_wall_seconds'] = summary['wall_seconds']
        summary['wall_seconds'] = prior_summary['wall_seconds']
    write(out/'summary.json', summary)
    report = ['# 14E：布局布线算法实验', '',
              '固定原来的 16 KiB main RAM 网表、CST、器件与 150 MHz 目标。每组使用相同 seed 集合。', '',
              '| 配置 | 有效结果 | 最佳 MHz | 中位数 MHz | 150 MHz 通过 |',
              '| --- | ---: | ---: | ---: | ---: |']
    for row in results:
        if row.get('best'):
            report.append(f"| {row['profile']} | {row['valid_runs']} | {row['best']['limiting_fmax_mhz']:.2f} | {row['median_mhz']:.2f} | {row['target_passes']} |")
        else:
            report.append(f"| {row['profile']} | 0 | 无完整时序结果 | — | 0 |")
    report += ['', '每项状态和日志保存在对应配置目录。超时或工具错误不参与 Fmax 排名。',
               '这是有限配置/seed 样本的静态时序结果，没有上板验证。']
    (out/'REPORT.md').write_text('\n'.join(report) + '\n')
    print('COMPLETE', summary['target_passes'], 'passing cases', flush=True)


if __name__ == '__main__':
    main()
