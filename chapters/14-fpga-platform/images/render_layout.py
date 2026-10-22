#!/usr/bin/env python3
"""Render actual nextpnr placement/routing, optionally compare using shared scales."""
import argparse,collections,gzip,hashlib,json,re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
COLORS={'Logic / mux / ALU':'#2563eb','Flip-flop':'#f59e0b','RAM':'#16a34a','DSP':'#0891b2','PLL':'#9333ea','IO':'#e11d48'}

def read_case(path):
 raw=path.read_bytes()
 if path.suffix=='.gz':raw=gzip.decompress(raw)
 top=json.loads(raw)['modules']['top']
 groups=collections.defaultdict(list);wires=collections.Counter();coord=re.compile(r'^X(\d+)Y(\d+)/')
 for cell in top['cells'].values():
  match=coord.match(cell.get('attributes',{}).get('NEXTPNR_BEL',''))
  if not match:continue
  x,y=map(int,match.groups());kind=cell['type']
  if kind in ('DUMMY_CELL','GOWIN_VCC','GOWIN_GND'):continue
  group=('RAM' if kind in ('DPB','SDPB','SP','DP','SDP','BSRAM','RAM16SDP4') else 'DSP' if kind.startswith('MULT') else 'PLL' if 'PLL' in kind.upper() else 'IO' if kind in ('IBUF','OBUF','IOBUF','IOB') else 'Flip-flop' if kind.startswith('DFF') else 'Logic / mux / ALU')
  slot=re.search(r'(?:LUT|DFF|ALU)(\d+)$',cell['attributes']['NEXTPNR_BEL'])
  offset=(int(slot[1])%8-3.5)*.075 if slot else 0
  groups[group].append((x+offset,y))
 for net in top['netnames'].values():
  for token in net.get('attributes',{}).get('ROUTING','').split(';')[::3]:
   match=coord.match(token.strip())
   if match:wires[tuple(map(int,match.groups()))]+=1
 if not groups or not wires:raise RuntimeError('Missing placement/routing attributes')
 summary=json.loads((path.parent/'summary.json').read_text())
 timing=summary.get('report') or json.loads((path.parent/'pnr-report.json').read_text())
 target=summary.get('target_mhz',timing['fmax']['VexRiscv.clk']['constraint'])
 metadata={'input':str(path.resolve()),'input_sha256':hashlib.sha256(raw).hexdigest(),'target_mhz':target,'system_fmax_estimate_mhz':timing['fmax']['VexRiscv.clk']['achieved'],'seed':summary['seed'],'placed_cells':sum(map(len,groups.values())),'routed_wire_occurrences':sum(wires.values())}
 return dict(groups=groups,wires=wires,metadata=metadata)

def render(cases,output,bounds,density_max):
 xmax,ymax=bounds
 fig,axes=plt.subplots(len(cases),2,figsize=(14,7*len(cases)),layout='constrained',squeeze=False)
 fig.patch.set_facecolor('#f5f7fb')
 for row,case in enumerate(cases):
  left,right=axes[row];groups=case['groups'];meta=case['metadata'];frequency=meta['target_mhz']
  for group,color in COLORS.items():
   points=groups.get(group,[])
   if not points:continue
   x,y=zip(*points);left.scatter(x,y,s=11 if group in ('RAM','PLL','IO','DSP') else 3,c=color,alpha=.75,label=f'{group} ({len(points)})',marker='s' if group in ('RAM','DSP') else 'o',zorder=3 if group in ('RAM','PLL','IO','DSP') else 2)
  left.set_title(f'{frequency:g} MHz target | seed {meta["seed"]} | placed cells',loc='left',fontweight='bold')
  left.legend(loc='upper center',bbox_to_anchor=(.5,-.11),ncol=3,fontsize=8,frameon=False)
  grid=np.zeros((ymax+1,xmax+1))
  for (x,y),n in case['wires'].items():grid[y,x]=n
  heat=right.imshow(np.ma.masked_equal(np.log1p(grid),0),origin='lower',extent=(-.5,xmax+.5,-.5,ymax+.5),cmap='magma',interpolation='nearest',vmin=0,vmax=density_max)
  right.set_title(f'{frequency:g} MHz | routed-wire usage | Fmax estimate {meta["system_fmax_estimate_mhz"]:.2f} MHz',loc='left',fontweight='bold',fontsize=11)
  fig.colorbar(heat,ax=right,shrink=.65,label='ln(1 + routed wire occurrences)')
  for ax in (left,right):
   ax.set_facecolor('#e9edf5');ax.set_xlim(-1,xmax+1);ax.set_ylim(-1,ymax+1);ax.set_aspect('equal');ax.set_xlabel('nextpnr tile X');ax.set_ylabel('nextpnr tile Y');ax.grid(alpha=.18,linewidth=.5)
 fig.suptitle('Tang Primer 20K | VexRiscv SoC | actual placement & routing\nGW2A-LV18PG256C8/I7 - shared coordinate bounds and routing color scale',fontsize=15,fontweight='bold')
 fig.supxlabel('Tile-coordinate visualization, not a die photograph. Wire usage is not congestion percentage. Fmax is a tool estimate.',fontsize=9)
 output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180);fig.savefig(output.with_suffix('.svg'));plt.close(fig)
 output.with_suffix('.json').write_text(json.dumps({'cases':[c['metadata'] for c in cases],'coordinate_bounds':bounds,'density_log_scale_max':density_max,'visualization':'BEL locations and routed-wire occurrences; no inferred wire geometry'},indent=2)+'\n')
 print(output)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input',type=Path,default=ROOT/'results/15-tang20k-build/routed.json')
 p.add_argument('--compare',type=Path)
 p.add_argument('--output',type=Path,default=HERE/'tang20k-layout.png')
 args=p.parse_args();cases=[read_case(args.input)]
 if args.compare:cases.append(read_case(args.compare))
 points=[point for c in cases for values in c['groups'].values() for point in values]+[point for c in cases for point in c['wires']]
 bounds=(int(max(x for x,y in points))+1,int(max(y for x,y in points))+1)
 density_max=max(float(np.log1p(max(c['wires'].values()))) for c in cases)
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 render(cases,args.output,bounds,density_max)
 if args.compare:
  for c in cases:
   name='tang20k-layout.png' if c['metadata']['target_mhz']==27 else f'tang20k-layout-{c["metadata"]["target_mhz"]:g}mhz.png'
   render([c],args.output.parent/name,bounds,density_max)
if __name__=='__main__':main()
