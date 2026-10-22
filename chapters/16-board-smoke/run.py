#!/usr/bin/env python3
"""Prepare, detect, load SRAM and capture UART on Tang Primer 20K Dock."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/16-tang20k')
    parser.add_argument('--detect',action='store_true',help='perform an actual JTAG detection')
    parser.add_argument('--load-sram',action='store_true',help='actually configure FPGA SRAM; never writes Flash')
    parser.add_argument('--bitstream',type=Path,default=ROOT/'results/15-tang20k-build/tutorial14.fs')
    parser.add_argument('--serial',help='actual serial device, e.g. /dev/serial/by-id/...')
    parser.add_argument('--baud',type=int,default=115200)
    parser.add_argument('--seconds',type=float,default=15)
    args=parser.parse_args()
    if args.seconds<=0 or args.baud<=0:parser.error('seconds and baud must be positive')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    loader=shutil.which('openFPGALoader')
    load_cmd=[loader or 'openFPGALoader','-b','tangprimer20k',str(args.bitstream.resolve())]
    report={'board':'Tang Primer 20K Dock','loader':loader,'load_command':load_cmd,'jtag':'SKIP','sram_configuration':'SKIP','uart':'SKIP'}
    serial=None
    try:
        if args.serial:
            import serial as pyserial
            serial=pyserial.Serial(port=None,baudrate=args.baud,timeout=.1)
            serial.dtr=False;serial.rts=False;serial.port=args.serial;serial.open()
        if args.detect or args.load_sram:
            if not loader:raise RuntimeError('openFPGALoader not installed; activate the tools environment')
            command=[loader,'-b','tangprimer20k','--detect']
            probe=subprocess.run(command,capture_output=True,text=True,timeout=30)
            (out/'detect.log').write_text(probe.stdout+probe.stderr);probe.check_returncode()
            report['jtag']='PASS: detection command completed; verify device identity in detect.log'
        if args.load_sram:
            data=args.bitstream.read_bytes()
            if not data:raise RuntimeError('bitstream empty')
            report['bitstream_sha256']=hashlib.sha256(data).hexdigest()
            load=subprocess.run(load_cmd,capture_output=True,text=True,timeout=90)
            (out/'load.log').write_text(load.stdout+load.stderr);load.check_returncode()
            report['sram_configuration']='PASS: loader completed; user logic tested separately'
        if serial:
            received=bytearray();deadline=time.monotonic()+args.seconds
            while time.monotonic()<deadline:received.extend(serial.read(4096))
            (out/'uart.bin').write_bytes(received);text=received.decode('ascii',errors='replace');(out/'uart.txt').write_text(text)
            print(text,end='')
            if '14 HELLO:' not in text and '14 ALIVE:' not in text:raise RuntimeError('no firmware marker captured; inspect baud, USB port and reset')
            report['uart']='PASS: real firmware marker captured'
        if not(args.detect or args.load_sram or args.serial):
            report['reason']='no hardware action selected; prepared command only; no USB hardware accessed'
            print('SKIP 16 hardware; to run on the connected board:')
            print(' '.join(load_cmd))
        report['manual_checks']={'heartbeat':'PENDING','button_press_release':'PENDING','reset_restart':'PENDING','cold_boot':'PENDING'}
    except Exception as exc:
        report['status']='FAIL';report['error']=str(exc);raise
    finally:
        if serial:serial.close()
        (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
