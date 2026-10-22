"""Local path setup, JSON output and source hashing for the Tang tutorial."""
import hashlib,json,os,sys
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parent.parent if CHAPTER.parent.name=='chapters' else CHAPTER
sys.path.insert(0,str(ROOT))
try:
    from tutorial_paths import add_litex_to_path
except ModuleNotFoundError as exc:
    if exc.name!='tutorial_paths':raise
    def add_litex_to_path(root):
        if os.environ.get('LITEX_ROOT'):sys.path.insert(0,os.environ['LITEX_ROOT'])

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
