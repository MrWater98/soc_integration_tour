#!/usr/bin/env python3
"""Real OpenOCD -> TCP remote_bitbang -> pin levels -> Icarus RTL."""
import argparse,json,re,socket,subprocess,threading
from pathlib import Path
from visualize import render
from pin_driver import Pins
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parent.parent if CHAPTER.parent.name=='chapters' else CHAPTER

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'results/13c');p.add_argument('--expected-id',type=lambda value:int(value,0),default=0x12345679);args=p.parse_args()
 args.output.mkdir(parents=True,exist_ok=True)
 for stale in ('summary.json','REPORT.md','pins.html'):(args.output/stale).unlink(missing_ok=True)
 pins=Pins(CHAPTER,args.output);errors=[];counts={'write':0,'read':0,'reset':0};protocol=[]
 listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(15)
 port=listener.getsockname()[1]
 def serve():
  try:
   conn,_=listener.accept()
   with conn:
    conn.settimeout(15)
    while True:
     data=conn.recv(4096)
     if not data:break
     for byte in data:
      ch=chr(byte);protocol.append(ch)
      if '0'<=ch<='7':
       v=byte-48;ck,ms,di=(v>>2)&1,(v>>1)&1,v&1
       pins.set(ck,ms,di,rst=pins.levels[3]);counts['write']+=1
      elif ch=='R':conn.sendall(str(pins.last[0]).encode());counts['read']+=1
      elif ch in 'rstu':
       v=ord(ch)-ord('r');ck,ms,di,_,mode=pins.levels
       pins.set(ck,ms,di,rst=int(not(v&2)),mode=mode);counts['reset']+=1
      elif ch in 'Bb':pass
      elif ch=='Q':return
      else:raise ValueError('Unsupported remote_bitbang command '+repr(ch))
  except Exception as exc:errors.append(repr(exc))
 worker=threading.Thread(target=serve,daemon=True);worker.start()
 cfg=f'''# Local simulation only: no USB adapter, no CPU target.
interface remote_bitbang
remote_bitbang_host 127.0.0.1
remote_bitbang_port {port}
transport select jtag
reset_config trst_only
jtag newtap tutorial tap -irlen 4 -expected-id 0x{args.expected_id:08x}
gdb_port disabled
tcl_port disabled
telnet_port disabled
init
scan_chain
irscan tutorial.tap 3
set first [drscan tutorial.tap 32 0x2468ace1]
set second [drscan tutorial.tap 32 0]
echo "USER_OLD=$first"
echo "USER_NEW=$second"
if {{[expr 0x$first] != 0xcafef00d}} {{error "USER old mismatch"}}
if {{[expr 0x$second] != 0x2468ace1}} {{error "USER new mismatch"}}
irscan tutorial.tap 4
set wrong [drscan tutorial.tap 32 0]
if {{[expr 0x$wrong] != 0}} {{error "wrong-IR bypass mismatch"}}
irscan tutorial.tap 2
set recovered [drscan tutorial.tap 32 0]
if {{[expr 0x$recovered] != 0x12345679}} {{error "ID recovery mismatch"}}
echo "WRONG_IR_DETECTED_AND_RECOVERED"
shutdown
'''
 (args.output/'openocd.cfg').write_text(cfg)
 try:
  result=subprocess.run(['openocd','-f',str(args.output/'openocd.cfg')],capture_output=True,text=True,timeout=30)
  log=result.stdout+result.stderr;(args.output/'openocd.log').write_text(log)
  worker.join(5)
  if worker.is_alive():raise TimeoutError('adapter did not finish')
  if errors:raise RuntimeError(errors)
  if result.returncode:raise RuntimeError('OpenOCD failed; inspect '+str(args.output/'openocd.log'))
  found=re.search(r'tap/device found: (0x[0-9a-fA-F]+)',log)
  assert found and int(found[1],16)==args.expected_id,'Actual TAP ID differs from requested ID'
  assert 'WRONG_IR_DETECTED_AND_RECOVERED' in log
  assert 'user_old=cafef00d' in log.lower()
  assert 'user_new=2468ace1' in log.lower()
  assert counts['read']>0 and counts['write']>0
 finally:
  listener.close();pins.close()
 (args.output/'remote-bitbang.txt').write_text(''.join(protocol)+'\n')
 (args.output/'summary.json').write_text(json.dumps({'status':'PASS','transport':'real OpenOCD remote_bitbang to RTL','counts':counts,'expected_id':f'0x{args.expected_id:08x}','cpu_debug':'NOT_IMPLEMENTED'},indent=2)+'\n')
 (args.output/'REPORT.md').write_text('# 13C OpenOCD 驱动 RTL\n\nPASS：扫描链识别、USER 旧值 cafef00d、新值 2468ace1。\n\n'+f"引脚写入 {counts['write']} 次，TDO 采样 {counts['read']} 次。\n\n真实 OpenOCD 控制真实 TAP RTL；未连接 CPU 调试模块。\n")
 render(args.output/'pins.csv',args.output/'pins.html')
 print('PASS 13C:',counts)
if __name__=='__main__':main()
