#!/usr/bin/env python3
"""Plot completed algorithm trials, including failed/timed-out case counts."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', type=Path, default=ROOT/'results/14e-algorithms/summary.json')
args = parser.parse_args()
summary = json.loads(args.input.read_text())
profiles = summary['profiles']
fig, ax = plt.subplots(figsize=(max(12, len(profiles)*1.25), 6), constrained_layout=True)
for index, row in enumerate(profiles):
    valid = [r for r in row.get('results', []) if r['status'] in ('PASS', 'TIMING_FAIL')]
    for case_index, case in enumerate(valid):
        offset = (case_index-(len(valid)-1)/2)*0.13
        ax.scatter(index+offset, case['limiting_fmax_mhz'], color='#2677b8', s=32)
    if valid:
        ax.plot([index-0.25, index+0.25], [row['median_mhz']]*2, color='#dd7d13', lw=3)
        best = row['best']['limiting_fmax_mhz']
        ax.annotate(f'{best:.2f}', (index, best), xytext=(0, 8), textcoords='offset points', ha='center', fontsize=9)
    else:
        ax.text(index, 105, 'No timing\nresult', ha='center', fontsize=9)
ax.axhline(150, color='#ba3434', linestyle='--', label='150 MHz target')
ax.scatter([], [], color='#2677b8', label='Completed seed result')
ax.plot([], [], color='#dd7d13', lw=3, label='Median')
labels = [f"{r['profile']}\n{r.get('valid_runs', 0)}/{len(r.get('results', []))} valid" for r in profiles]
ax.set_xticks(range(len(profiles)), labels, rotation=35, ha='right')
ax.set_ylabel('Limiting clock Fmax estimate (MHz)')
ax.set_title('Tang Primer 20K: fixed netlist, different nextpnr algorithms')
ax.grid(axis='y', alpha=0.25)
ax.legend(loc='lower right')
for extension in ('png', 'svg'):
    fig.savefig(args.input.parent/f'algorithm-fmax.{extension}', dpi=180)
print('Saved algorithm-fmax.png / .svg')
if 'expanded_weight20' in summary:
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    for label, results, color in [
        ('Default timing weight 10', summary['baseline_12_seeds']['results'], '#2677b8'),
        ('Timing weight 20', summary['expanded_weight20']['results'], '#dd7d13'),
    ]:
        valid = [r for r in results if r['status'] in ('PASS', 'TIMING_FAIL')]
        ax.plot([r['seed'] for r in valid], [r['limiting_fmax_mhz'] for r in valid],
                marker='o', color=color, label=label)
    ax.axhline(150, color='#ba3434', linestyle='--', label='150 MHz target')
    ax.set_xticks(range(1, 13))
    ax.set_xlabel('Seed (discrete experiment ID)')
    ax.set_ylabel('Limiting clock Fmax estimate (MHz)')
    ax.set_title('Same netlist and 12 seeds: change only heap timing weight')
    ax.grid(alpha=0.25)
    ax.legend()
    for extension in ('png', 'svg'):
        fig.savefig(args.input.parent/f'weight20-seeds.{extension}', dpi=180)
    print('Saved weight20-seeds.png / .svg')
