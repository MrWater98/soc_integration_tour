#!/usr/bin/env python3
"""Fetch pinned RVT pilot views in an isolated external PDK checkout."""
import argparse,hashlib,json,subprocess,tarfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TAG='v1.10.102'
COMMIT='ebc3f7e5d22a67f9423e0d980cd056291a58f307'
def main():
 p=argparse.ArgumentParser();p.add_argument('--pdk',type=Path,default=ROOT/'external/icsprout55-pdk');args=p.parse_args();pdk=args.pdk.resolve()
 if not pdk.exists():subprocess.run(['git','clone','--depth','1','--branch',TAG,'https://github.com/openecos-projects/icsprout55-pdk.git',str(pdk)],check=True)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=pdk,text=True).strip()==COMMIT,'Wrong PDK checkout'
 metadata=subprocess.check_output(['curl','-fsSL','--retry','3','--max-time','90',f'https://api.github.com/repos/openecos-projects/icsprout55-pdk/releases/tags/{TAG}']);assets={x['name']:x for x in json.loads(metadata)['assets']}
 records=[]
 for name in ('ics55_LLSC_H7CR_liberty.tar.bz2','ics55_LLSC_H7CR_gds.tar.bz2'):
  asset=assets[name];target=pdk/name
  if not target.exists():
   subprocess.run(['curl','-fL','--retry','3','--max-time','300',asset['browser_download_url']+'?t='+str(time.time_ns()),'-o',str(target.with_suffix('.part'))],check=True)
   target.with_suffix('.part').rename(target)
  assert target.stat().st_size==asset['size'],'Asset length mismatch'
  digest=hashlib.sha256(target.read_bytes()).hexdigest()
  if asset.get('digest'):assert asset['digest']=='sha256:'+digest,'Upstream asset digest mismatch'
  parent=pdk/'IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR'
  with tarfile.open(target) as archive:
   for member in archive.getmembers():
    assert (parent/member.name).resolve().is_relative_to(parent.resolve()) and not member.issym() and not member.islnk(),'Unsafe archive member'
   archive.extractall(parent)
  records.append({'name':name,'bytes':asset['size'],'sha256':digest,'url':asset['browser_download_url']});print('Fetched',name,flush=True)
 (pdk/'tutorial-lock.json').write_text(json.dumps({'tag':TAG,'commit':COMMIT,'assets':records},indent=2)+'\n')
if __name__=='__main__':main()
