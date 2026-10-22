#!/usr/bin/env python3
"""Create publication-style static figures from recorded seed-sweep results."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'results/14e');args=p.parse_args()
 out=args.input.resolve();x=json.loads((out/'summary.json').read_text());rows=[r for r in x['results'] if 'system_fmax_mhz' in r];best=x['best'];target=x['configuration']['target_mhz'];colors=['#16a34a' if r['seed']==best['seed'] else '#2563eb' for r in rows]
 fig,axes=plt.subplots(1,2,figsize=(13,5.5),layout='constrained');fig.patch.set_facecolor('#f5f7fb')
 a,b=axes;seeds=[str(r['seed']) for r in rows];a.bar(seeds,[r['system_fmax_mhz'] for r in rows],color=colors)
 a.axhline(target,color='#dc2626',linestyle='--',label=f'{target:g} MHz target');a.set_ylim(0,max(target,max(r['system_fmax_mhz'] for r in rows))*1.1)
 for i,r in enumerate(rows):a.text(i,r['system_fmax_mhz']+1,f'{r["system_fmax_mhz"]:.1f}',ha='center',fontsize=8)
 a.set_title('Fixed netlist + CST; only seed changes',loc='left',fontweight='bold');a.set_xlabel('nextpnr seed');a.set_ylabel('Shared system-clock Fmax estimate (MHz)');a.legend(frameon=False);a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
 ranked=sorted(rows,key=lambda r:r['system_fmax_mhz'],reverse=True)
 logic=[];routing=[]
 for r in ranked:
  d=r['critical_path']['delay_ns_by_type'];routing.append(d.get('routing',0));logic.append(sum(v for k,v in d.items() if k!='routing'))
 yy=range(len(ranked));b.barh(yy,logic,label='Logic + FF timing',color='#f59e0b');b.barh(yy,routing,left=logic,label='Routing',color='#7c3aed');b.axvline(1000/target,color='#dc2626',linestyle='--',label=f'{1000/target:.2f} ns budget')
 b.set_yticks(list(yy),[f'seed {r["seed"]}' for r in ranked]);b.invert_yaxis();b.set_xlabel('Shared system-clock critical-path delay (ns)');b.set_title('Critical-path contributions, ranked by Fmax',loc='left',fontweight='bold');b.legend(frameon=False,fontsize=8);b.grid(axis='x',alpha=.2);b.set_axisbelow(True)
 for ax in axes:ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
 fig.suptitle('Tang Primer 20K | 14E seed exploration | nextpnr timing estimates',fontsize=14,fontweight='bold')
 fig.supxlabel('Finite sampled search, not a proven global maximum. No bitstream packing or board frequency measurement.',fontsize=9)
 fig.savefig(out/'seed-fmax.png',dpi=180);fig.savefig(out/'seed-fmax.svg');plt.close(fig)
 print(out/'seed-fmax.png')
if __name__=='__main__':main()
