#!/usr/bin/env python3
"""Join the algorithm campaign and expanded seed trial without rerunning tools."""
import argparse
import json
from pathlib import Path
import shutil
import statistics

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'results/14e-algorithms')
    args = parser.parse_args()
    out = args.input.resolve()
    initial = load(out/'summary.json')
    followup = load(out/'followup/summary.json')
    extra = load(out/'weight20-extra-seeds/summary.json')
    baseline = load(ROOT/'results/14e/summary.json')
    profiles = initial['profiles'] + followup['profiles']
    identity = baseline['configuration']['netlist_sha256']
    constraint = baseline['configuration']['constraints_sha256']
    cases = []
    for group in profiles:
        config = group['configuration']
        assert config['netlist_sha256'] == identity
        assert config['constraints_sha256'] == constraint
        prefix = group['profile'] if group in initial['profiles'] else 'followup/' + group['profile']
        for row in group['results']:
            cases.append(dict(row, profile=group['profile'], directory=prefix))
    assert extra['configuration']['netlist_sha256'] == identity
    assert extra['configuration']['constraints_sha256'] == constraint
    cases += [dict(row, profile='heap-weight20', directory='weight20-extra-seeds') for row in extra['results']]
    valid = [row for row in cases if row['status'] in ('PASS', 'TIMING_FAIL')]
    best = max(valid, key=lambda row: row['limiting_fmax_mhz'])
    expanded = sorted([row for row in cases if row['profile'] == 'heap-weight20'], key=lambda row: row['seed'])
    assert [row['seed'] for row in expanded] == list(range(1, 13))
    expanded_valid = [row for row in expanded if row['status'] in ('PASS', 'TIMING_FAIL')]
    summary = {'profiles': profiles, 'expanded_weight20': {'results': expanded,
               'best': max(expanded_valid, key=lambda row: row['limiting_fmax_mhz']),
               'median_mhz': statistics.median(row['limiting_fmax_mhz'] for row in expanded_valid)},
               'baseline_12_seeds': baseline, 'best': best, 'total_cases': len(cases),
               'valid_runs': len(valid), 'target_passes': sum(row['status'] == 'PASS' for row in cases),
               'tool_errors': sum(row['status'] == 'TOOL_ERROR' for row in cases),
               'timeouts': sum(row['status'] == 'TIMEOUT' for row in cases),
               'phase_wall_seconds': {'initial': initial['wall_seconds'], 'followup': followup['wall_seconds'],
                                      'expanded_seeds': extra['wall_seconds']},
               'netlist_sha256': identity, 'constraints_sha256': constraint,
               'hardware': 'NOT_RUN', 'bitstream': 'NOT_PACKED'}
    (out/'campaign-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    bestout = out/'best'
    bestout.mkdir(exist_ok=True)
    for name in ('routed.json.gz', 'pnr-report.json', 'summary.json'):
        shutil.copyfile(out/best['directory']/'best'/name, bestout/name)
    path = best['critical_path']
    delays = path['delay_ns_by_type']
    report = ['# 14E：布局布线算法与参数实验', '',
              '使用同一份 16 KiB main RAM / 150 MHz 网表。先比较算法，再围绕有效参数扩大 seed 范围。', '',
              f"实际 {len(cases)} 次尝试，{len(valid)} 个完整时序结果，{summary['tool_errors']} 个工具错误，{summary['timeouts']} 次超时。",
              f"150 MHz 通过 {summary['target_passes']} 次；没有使用 timing-allow-fail，没有上板或打包 bitstream。", '',
              '## 1. 共同 seed 2、5、8 的配置比较', '',
              '| 配置 | 有效结果 | 最佳 MHz | 中位数 MHz | 150 MHz 通过 |',
              '| --- | ---: | ---: | ---: | ---: |']
    for group in profiles:
        if group['best']:
            report.append(f"| {group['profile']} | {group['valid_runs']}/3 | {group['best']['limiting_fmax_mhz']:.2f} | {group['median_mhz']:.2f} | {group['target_passes']} |")
        else:
            report.append(f"| {group['profile']} | 0/3 | 无完整时序结果 | — | 0 |")
    report += ['', '![相同 seed 的算法比较](algorithm-fmax.png)', '',
               '## 2. 权重 20 扩展到 seed 1–12', '',
               '前三个样本中权重 20 有改善，因此新增另外 9 个 seed。已有的 2、5、8 不重复计数。', '',
               '| 指标 | 默认权重 10，seed 1–12 | 权重 20，seed 1–12 |',
               '| --- | ---: | ---: |',
               f"| 最佳 MHz | {baseline['best']['limiting_fmax_mhz']:.2f} | {summary['expanded_weight20']['best']['limiting_fmax_mhz']:.2f} |",
               f"| 中位数 MHz | {baseline['median_limiting_fmax_mhz']:.2f} | {summary['expanded_weight20']['median_mhz']:.2f} |",
               f"| 150 MHz 通过 | {baseline['target_passes']}/12 | {sum(r['status']=='PASS' for r in expanded)}/12 |", '',
               '![相同 12 个 seed 的权重对照](weight20-seeds.png)', '',
               '| seed | 权重 20 Fmax MHz | 状态 |', '| --- | ---: | --- |']
    for row in expanded:
        report.append(f"| {row['seed']} | {row.get('limiting_fmax_mhz', 0):.2f} | {row['status']} |")
    report += ['', '## 3. 本轮最佳实现的关键路径', '',
               f"最佳配置 **{best['profile']}，seed {best['seed']}，Fmax {best['limiting_fmax_mhz']:.2f} MHz**。",
               f"起点 `{path['start']['cell']}.{path['start']['port']}`，终点 `{path['end']['cell']}.{path['end']['port']}`。",
               f"路径 {path['total_delay_ns']:.3f} ns：路由 {delays.get('routing', 0):.3f} ns、逻辑 {delays.get('logic', 0):.3f} ns、clk-to-q {delays.get('clk-to-q', 0):.3f} ns、setup {delays.get('setup', 0):.3f} ns。150 MHz 预算约 6.667 ns。", '',
               '这是有限样本中的最佳静态时序估计，不是板上最高频率。各 seed 的关键路径可能不同，不能把 Fmax 差值归因于同一条线的缩短。', '',
               '## 4. 工具限制与结论', '',
               '- 当前 Gowin 后端明确不支持 static 布局，三个 seed 都报错。',
               '- sa 在本设计的初始布局阶段发生 SIGSEGV，三个 seed 都没有完整结果。',
               '- router2 的实验性 tmg-ripup 在 seed 2 触发 base_arch.h:259 的断言；另外两个 seed 完成，但没有达到目标。',
               '- 本组默认路由与显式 router1 的三个样本 Fmax 相同；router2 与 alternate weights 没有提升最好值。',
               '- 权重 30、40 和降低密度的组合没有超过权重 20 的最佳结果。', '',
               '时序权重改变布局优化的取舍；参数变大不保证更快，单个 seed 的改善也不代表所有 seed 都改善。', '',
               '## 5. 文件之间的关系', '',
               '- config.json / progress.json / summary.json / REPORT.md：初始九组的运行配置与汇总；本 REPORT.md 更新为完整实验报告，初始逐组数据仍在 summary.json。',
               '- followup/：四组有针对性的参数调整，含独立配置、日志和汇总。',
               '- weight20-extra-seeds/：权重 20 的另外九个 seed。',
               '- campaign-summary.json：以上三个阶段的总汇；合计实际尝试次数、完整样本、错误、最佳实现和 12-seed 对照。',
               '- 每组 input/：压缩网表、CST 和身份；rtl/：完整 HDL/初始化文件；seed-xxx/：实际命令、日志、最终报告、摘要。',
               '- 每组 best/ 及根目录 best/：保留各组及全实验最佳实现的压缩路由、时序报告和摘要。',
               '- analysis-command.json / analysis.log：重新解析 router2 日志的记录，不增加实际布局布线尝试次数。',
               '- algorithm-fmax.* / weight20-seeds.*：由固定的 JSON 结果生成的科学绘图。', '',
               '完整 routed.json 和解压网表保留本地，Git 保存压缩输入和最佳路线。每项最多运行 600 秒；共享主机并发会影响耗时，本文不做算法运行速度排名。三个阶段存在时间重叠，不把阶段墙钟简单相加作为总耗时。', '',
               '## 6. 重现与重新汇总', '',
               '执行命令和阶段参数见 [14E 教程](../../chapters/14e-seed-sweep/README.md#10-换布局布线算法在同一份电路上尝试不同解法)。完成三个阶段后：', '',
               '```bash', 'python chapters/14e-seed-sweep/summarize_algorithms.py',
               'python chapters/14e-seed-sweep/plot_algorithms.py --input results/14e-algorithms/campaign-summary.json',
               '```', '',
               'summarize_algorithms.py 验证各阶段的输入网表/CST 哈希一致后汇总，不运行 nextpnr。']
    text = '\n'.join(report)+'\n'
    (out/'REPORT.md').write_text(text)
    (out/'README.md').write_text(text)
    print('BEST', best['profile'], best['seed'], best['limiting_fmax_mhz'], 'MHz')


if __name__ == '__main__':
    main()
