#!/usr/bin/env python3
"""Pinned ICS55 standard-cell pilot: mapping, functional gate simulation and ideal-clock STA."""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pdk',type=Path,default=ROOT/'external/icsprout55-pdk');p.add_argument('--output',type=Path,default=ROOT/'results/18');p.add_argument('--period-ns',type=float,default=20);a=p.parse_args()
 if a.period_ns<=0:p.error('period must be positive')
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'summary.json').unlink(missing_ok=True);rtl=out/'rtl';rtl.mkdir(exist_ok=True)
 base=a.pdk.resolve()/'IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR'
 lib=base/'liberty/ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib';model=base/'verilog/ics55_LLSC_H7CR.v'
 if not lib.exists():raise RuntimeError('Run fetch_pdk.py first: pinned Liberty missing')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.pdk,text=True).strip()
 if commit!='ebc3f7e5d22a67f9423e0d980cd056291a58f307':raise RuntimeError('Wrong PDK revision')
 shutil.copy2(HERE/'counter.v',rtl/'counter.v');shutil.copy2(model,rtl/model.name)
 def run(cmd,name):
  r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=180);(out/name).write_text(r.stdout+r.stderr);r.check_returncode();return r.stdout+r.stderr
 yosys=shutil.which('yosys') or ROOT/'external/fpga-tools/oss-cad-suite/bin/yosys'
 script=f'read_verilog {rtl}/counter.v; hierarchy -check -top counter; synth -top counter; dfflibmap -liberty {lib}; abc -liberty {lib}; clean; check; stat -liberty {lib}; write_verilog -noattr -noexpr {rtl}/mapped.v'
 (out/'synth.ys').write_text(script+'\n');run([yosys,'-s',out/'synth.ys'],'synthesis.log')
 net=(rtl/'mapped.v').read_text();cells=set(re.findall(r'^\s+(\w+H7R)\s+\\?\w+',net,re.M))
 if not cells:raise RuntimeError('No mapped ICS55 cells')
 views={k:(base/path).read_text() for k,path in [('lef','lef/ics55_LLSC_H7CR.lef'),('cdl','cdl/ics55_LLSC_H7CR.cdl')]}
 for cell in cells:
  for kind,text in views.items():
   if not re.search(r'\b'+re.escape(cell)+r'\b',text):raise RuntimeError(f'{cell} missing {kind}')
 run(['iverilog','-g2012','-Dfunctional','-s','tb','-o',out/'counter.vvp',rtl/'mapped.v',rtl/model.name,HERE/'tb.sv'],'compile.log')
 sim=run(['vvp',out/'counter.vvp'],'simulation.log');assert 'PASS18' in sim
 sta=shutil.which('sta') or ROOT/'external/opensta/usr/bin/sta'
 tcl=f'read_liberty {lib}\nread_verilog {rtl}/mapped.v\nlink_design counter\ncreate_clock -name core -period {a.period_ns} [get_ports clk]\nset_input_delay 1 -clock core [get_ports reset]\nset_output_delay 1 -clock core [get_ports count*]\nreport_checks -path_delay max -format full_clock_expanded\nreport_checks -path_delay min\nexit\n'
 (out/'constraints.sdc').write_text(f'create_clock -name core -period {a.period_ns} [get_ports clk]\nset_input_delay 1 -clock core [get_ports reset]\nset_output_delay 1 -clock core [get_ports count*]\n')
 (out/'timing.tcl').write_text(tcl);timing=run([sta,'-exit',out/'timing.tcl'],'timing.log')
 if re.search(r'^Error:',timing,re.M):raise RuntimeError('OpenSTA reported error')
 if 'slack (VIOLATED)' in timing:raise RuntimeError('STA timing constraint violated')
 if 'slack (MET)' not in timing:raise RuntimeError('No constrained timing path reported')
 report={'status':'PASS: standard-cell pilot','pdk_commit':commit,'corner':lib.name,'liberty_sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'cells':sorted(cells),'period_ns':a.period_ns,'simulation_cycles':70000,'sta':'ideal clock, no extracted wire RC','physical_design':'NOT_RUN','drc_lvs':'NOT_RUN','spec_freeze':'PENDING macro, IO, package and manufacturing decisions'}
 (rtl/'sources.json').write_text(json.dumps({'top':'counter','files':[{'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(rtl.iterdir()) if f.suffix=='.v'],'simulation_define':'functional'},indent=2)+'\n')
 (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
