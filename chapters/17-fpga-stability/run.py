#!/usr/bin/env python3
"""Bounded on-board campaign: RAM patterns, IRQ progress, UART nonces and warm resets."""
import argparse,math,hashlib,json,re,secrets,shutil,subprocess,time
from pathlib import Path
import serial
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'results/17');p.add_argument('--output',type=Path,default=ROOT/'results/17-hardware');p.add_argument('--serial',required=True);p.add_argument('--seconds',type=float,default=60);p.add_argument('--warm-resets',type=int,default=3);p.add_argument('--min-rounds',type=int,default=100);p.add_argument('--min-irqs',type=int,default=10);p.add_argument('--load',action='store_true');p.add_argument('--expect-fault',action='store_true');p.add_argument('--board-id',default='Tang Primer 20K Dock; serial not recorded');p.add_argument('--ambient-c',type=float);p.add_argument('--supply-v',type=float);p.add_argument('--measurement-note',default='No external thermometer/voltmeter connected');args=p.parse_args()
 if not math.isfinite(args.seconds) or args.seconds<5 or args.warm_resets<0 or args.min_rounds<1 or args.min_irqs<1:p.error('seconds >=5; warm resets >=0')
 src=args.input.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'summary.json').unlink(missing_ok=True)
 cfg=json.loads((src/'manifest.json').read_text())['config'];bitstream=src/'build/tutorial17.fs'
 if args.expect_fault and not cfg['inject_fault']:raise ValueError('Expected-fault run requires injected-fault firmware')
 port=serial.Serial(port=None,baudrate=cfg['baud'],timeout=.05);port.dtr=False;port.rts=False;port.port=args.serial;port.open();port.reset_input_buffer()
 report={'status':'FAIL','parameters':vars(args).copy(),'board':'Tang Primer 20K Dock','clock_hz':cfg['sys_clk_hz'],'warm_resets':0,'echoes':0,'max_rounds':0,'max_irqs':0,'boots':0,'cold_boot':'NOT_RUN: requires physical power cycling','temperature_voltage':'NOT_MEASURED','fault_caught':False,'epochs':[],'ambient_c':args.ambient_c,'supply_v':args.supply_v,'measurement_note':args.measurement_note,'board_id':args.board_id,'ram_counter_scope':'completed main_ram Wishbone transfers, 32-bit modulo counters','total_rounds_lower_bound':0,'total_irqs_lower_bound':0,'total_ram_reads_lower_bound':0,'total_ram_writes_lower_bound':0}
 report['parameters']={k:str(v) if isinstance(v,Path) else v for k,v in report['parameters'].items()};epoch=None;previous_reads=previous_writes=None
 pending={};buffer=b'';reset_target=None;reset_at=0;last_progress=time.monotonic();last_echo=0
 try:
  if args.load:
   loader=shutil.which('openFPGALoader') or str(ROOT/'external/fpga-tools/oss-cad-suite/bin/openFPGALoader')
   probe=subprocess.run([loader,'-b','tangprimer20k','--detect'],capture_output=True,text=True,timeout=30)
   (out/'detect.log').write_text(probe.stdout+probe.stderr);probe.check_returncode()
   if 'GW2A(R)-18(C)' not in probe.stdout+probe.stderr:raise RuntimeError('Unexpected FPGA')
   build=json.loads((src/'build/summary.json').read_text());data=bitstream.read_bytes()
   if hashlib.sha256(data).hexdigest()!=build['bitstream_sha256']:raise RuntimeError('Bitstream hash mismatch')
   report['bitstream_sha256']=build['bitstream_sha256'];load=subprocess.run([loader,'-b','tangprimer20k',str(bitstream)],capture_output=True,text=True,timeout=60)
   (out/'load.log').write_text(load.stdout+load.stderr);load.check_returncode()
  started=time.monotonic();deadline=started+args.seconds
  with (out/'uart.log').open('w') as log:
   while time.monotonic()<deadline:
    now=time.monotonic();buffer+=port.read(port.in_waiting or 1)
    while b'\n' in buffer:
     raw,buffer=buffer.split(b'\n',1);line=raw.decode('ascii',errors='replace').strip();log.write(f'{now-started:.6f} {line}\n');log.flush()
     if '17 FAIL' in line:
      report['fault_caught']=True
      if not args.expect_fault:raise RuntimeError('Firmware detected error: '+line)
      expected=0x10000000 | (cfg['stress_words']//2)
      fault=re.search(r'17 FAIL code=([0-9A-F]{8})',line)
      if not fault or int(fault[1],16)!=expected:raise RuntimeError('Wrong fault captured: '+line)
      report['status']='PASS: injected RAM error captured';break
     boot=re.search(r'17 BOOT hz=([0-9A-F]{8}) seed=([0-9A-F]{8})',line)
     if boot:
      assert int(boot[1],16)==cfg['sys_clk_hz'] and int(boot[2],16)==cfg['seed'],'Wrong loaded firmware'
      if report['boots'] and reset_target is None:raise RuntimeError('Unexpected spontaneous reboot')
      report['boots']+=1;last_progress=now
      epoch={'boot':report['boots'],'start_seconds':now-started,'rounds':0,'irqs':0,'ram_reads':0,'ram_writes':0};report['epochs'].append(epoch);previous_reads=previous_writes=None
      if reset_target is not None:
       assert report['boots']>=reset_target;report['warm_resets']+=1;reset_target=None
     progress=re.search(r'17 PASS rounds=([0-9A-F]{8}) irq=([0-9A-F]{8}) errors=([0-9A-F]{8})',line)
     if progress and report['boots']:
      rounds,irqs,errors=map(lambda x:int(x,16),progress.groups());assert errors==0
      report['max_rounds']=max(rounds,report['max_rounds']);report['max_irqs']=max(irqs,report['max_irqs']);last_progress=now
      if epoch is None:raise RuntimeError('Progress without observed boot; use --load')
      if rounds<epoch['rounds'] or irqs<epoch['irqs']:raise RuntimeError('Counter regressed without boot')
      report['total_rounds_lower_bound']+=rounds-epoch['rounds'];report['total_irqs_lower_bound']+=irqs-epoch['irqs'];epoch['rounds']=rounds;epoch['irqs']=irqs
      counts=re.search(r'reads=([0-9A-F]{8}) writes=([0-9A-F]{8})',line)
      if counts:
       reads,writes=(int(x,16) for x in counts.groups())
       for key,value,previous in [('reads',reads,previous_reads),('writes',writes,previous_writes)]:
        delta=value if previous is None else (value-previous)&0xffffffff
        report['total_ram_'+key+'_lower_bound']+=delta;epoch['ram_'+key]+=delta
       previous_reads,previous_writes=reads,writes
     echo=re.search(r'17 ECHO ([0-9A-F]{8})',line)
     if echo:
      token=echo[1]
      if token not in pending:raise RuntimeError('Unexpected/repeated nonce echo '+token)
      del pending[token];report['echoes']+=1
    if report['fault_caught']:break
    if not report['boots'] and now-started>5:raise TimeoutError('Initial boot not observed')
    if now-last_progress>5:raise TimeoutError('No firmware progress for 5 seconds')
    for token,when in pending.items():
     if now-when>3:raise TimeoutError('Missing UART echo '+token)
    if reset_target is not None and now-reset_at>5:raise TimeoutError('Warm reset did not restart firmware')
    if report['boots'] and reset_target is None and now-last_echo>.5:
     token=secrets.token_hex(4).upper();port.write(('E'+token+'\n').encode());pending[token]=now;last_echo=now
    # Reset only between completed transactions; require progress afterward.
    reset_due=started+(report['warm_resets']+1)*args.seconds/(args.warm_resets+1)
    if report['boots'] and report['warm_resets']<args.warm_resets and reset_target is None and not pending and now>=reset_due:
     reset_target=report['boots']+1;reset_at=now;port.write(b'R\n')
   report['elapsed_seconds']=time.monotonic()-started
   report['pending_echoes_at_end']=len(pending)
   report['longest_observed_epoch_seconds']=max((started+report['elapsed_seconds'] if i==len(report['epochs'])-1 else started+report['epochs'][i+1]['start_seconds'])-(started+e['start_seconds']) for i,e in enumerate(report['epochs'])) if report['epochs'] else 0
  if args.expect_fault:assert report['fault_caught'],'Fault injection escaped checker'
  else:
   assert report['max_rounds']>=args.min_rounds and report['max_irqs']>=args.min_irqs,'Insufficient RAM/IRQ progress'
   assert report['echoes']>=3 and report['warm_resets']==args.warm_resets and reset_target is None,'Insufficient UART/reset checks'
   assert report['boots']==args.warm_resets+1,'Missing initial boot'
   assert report['total_ram_reads_lower_bound']>0 and report['total_ram_writes_lower_bound']>0,'Missing hardware RAM counters'
   report['status']='PASS: bounded hardware campaign'
   if args.ambient_c is not None or args.supply_v is not None:report['temperature_voltage']='MANUAL_SINGLE_POINT: not a range qualification'
 except Exception as exc:report['error']=str(exc);raise
 finally:
  port.close();(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
  (out/'REPORT.md').write_text('# 17 板上压力测试\n\n'+report['status']+'\n\n'+f"时钟 {report['clock_hz']} Hz；RAM 最大轮数 {report['max_rounds']}；IRQ 最大计数 {report['max_irqs']}；UART nonce {report['echoes']}；热复位 {report['warm_resets']}。\n\n累计轮数、IRQ、RAM 读写事务下界与各启动阶段见 summary.json。计数截至最后一次日志；RAM 是从设备 ACK 计数，非指令数。冷启动、电压与温度扫描尚未执行。\n")
 print(report['status'],out)
if __name__=='__main__':main()
