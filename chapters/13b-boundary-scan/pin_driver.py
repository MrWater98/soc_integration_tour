"""Local pin-level RTL driver; no dependency on another chapter."""
import os
import csv
import hashlib
from pathlib import Path
import select
import shutil
import subprocess

class Pins:
    def __init__(self, chapter, output):
        self.output=Path(output); self.output.mkdir(parents=True,exist_ok=True)
        rtl=self.output/'rtl'; rtl.mkdir(exist_ok=True)
        manifest=[]
        for name in ('tap.sv','pin_bridge.sv'):
            shutil.copyfile(chapter/name,rtl/name)
            manifest.append({'file':name,'sha256':hashlib.sha256((rtl/name).read_bytes()).hexdigest()})
        import json
        (rtl/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (rtl/'files.f').write_text('tap.sv\npin_bridge.sv\n')
        subprocess.run(['iverilog','-g2012','-s','pin_bridge','-o',str((self.output/'sim').resolve()),'-f','files.f'],cwd=rtl,check=True)
        self.proc=subprocess.Popen(['vvp',str((self.output/'sim').resolve()),'+wave='+str((self.output/'pins.vcd').resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,bufsize=0)
        self.trace=(self.output/'pins.csv').open('w'); self.csv=csv.writer(self.trace)
        self.csv.writerow(['event','tck','tms','tdi','trst_n','fault','tdo','state','ir','user','pin_out','pin_in'])
        self.buffer=b'';self.index=0;self.last=None;self.levels=(0,1,0,1,0)
        self.set(0,1,0,0);self.set(0,1,0,1)
    def set(self,ck,ms,di,rst=1,mode=0):
        self.levels=(ck,ms,di,rst,mode)
        self.proc.stdin.write((' '.join(map(str,self.levels))+'\n').encode());self.proc.stdin.flush()
        while True:
            while b'\n' not in self.buffer:
                if not select.select([self.proc.stdout],[],[],5)[0]:
                    raise TimeoutError('RTL pin response timed out')
                chunk=os.read(self.proc.stdout.fileno(),4096)
                if not chunk:raise RuntimeError('RTL terminated')
                self.buffer+=chunk
            raw,self.buffer=self.buffer.split(b'\n',1)
            line=raw.decode()
            if line.startswith('PIN '):break
        self.last=list(map(int,line.split()[1:]));self.csv.writerow([self.index,*self.levels,*self.last]);self.trace.flush();self.index+=1
        return self.last
    def tick(self,tms,tdi=0,mode=0):
        before=self.set(0,tms,tdi,mode=mode);self.set(1,tms,tdi,mode=mode);self.set(0,tms,tdi,mode=mode)
        return before[0]
    def reset(self):
        for _ in range(5):self.tick(1)
        self.tick(0)
    def scan(self,value,bits,ir=False,mode=0,hold_output=None):
        self.tick(1,mode=mode)
        if ir:self.tick(1,mode=mode)
        self.tick(0,mode=mode);self.tick(0,mode=mode)
        result=0
        for i in range(bits):
            result|=self.tick(int(i==bits-1),(value>>i)&1,mode)<<i
            if hold_output is not None:assert self.last[4]==hold_output,'output changed during Shift'
        self.tick(1,mode=mode);self.tick(0,mode=mode)
        return result
    def close(self):
        self.proc.stdin.close()
        try:self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait();raise
        self.trace.close()
        if self.proc.returncode:raise RuntimeError('RTL process failed')
