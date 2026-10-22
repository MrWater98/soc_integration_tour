#!/usr/bin/env python3
"""Import tutorial stages 13–20A without changing the tour's existing 00–12."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RENAMES = {
    '01-single-vex': '01-cpu-bringup',
    '05-decode': '05-memory-map',
    '06-soc': '06-litex-soc',
}


def stage(name: str) -> int | None:
    match = re.match(r'^(\d+)(?:[a-z])?(?:-|$)', name)
    return int(match[1]) if match else None


def selected(path: Path) -> bool:
    parts = path.parts
    if parts[0] == 'instructor' or path.stem.lower() in ('review', 'small_quiz', 'quiz', 'questions', 'answers'):
        return False
    if parts[0] in ('chapters', 'results') and len(parts) > 1:
        number = stage(parts[1])
        return number is not None and 13 <= number <= 20
    if parts[0] == 'docs':
        return True
    return str(path) in ('PLAN.md', 'tutorial_paths.py')


def tour_markdown(text: str) -> str:
    """Adapt course material to a continuous, self-contained project guide."""
    original = text
    text = re.sub(r'^## 课堂回顾\n.*?(?=^## |\Z)', '', text, flags=re.M | re.S)
    if text != original:
        text = text.rstrip() + '\n'
    text = text.replace('## Questions and answers', '## Implementation notes')
    text = text.replace('## 问答', '## 实现说明')
    text = text.replace('正文回答当前问题，用具体动作解释因果；必要的问答放在本章合适位置。',
                        '正文按实现流程展开，用具体动作解释因果，把必要的概念说明放在对应代码和实验附近。')
    replacements = {
        '- 第一次用到位（bit）': '- 第一次用到位（bit）、字节（byte）、字（word）和十六进制（hex）换算时，用真实文件中的数值和从 0 开始的地址表逐步解释；明确字宽取决于上下文，直接展示容量、末字节地址与末字首地址的换算过程。',
        '- 每章固定包含：': '- 每章固定包含输入清单、目标、概念速查、结构图、最小代码、参数及选值理由、运行命令、输出清单、正常/边界/故障验证、排查步骤、本章速记和下一阶段入口。首次出现的缩写要解释。',
        '- 每章 README 的“课堂回顾”': '- tour 按实现流程连续讲解：先给结构和数据流，再读代码、运行命令与实际结果。概念直接在正文解释，计算过程和失效定位紧贴对应实验。',
        '- 图和表要能拿着日志核对：': '- 图和表要能拿着日志核对：标出数据方向、地址单位、一次事务的等待与完成、字节通道和关键字段。用真实输出逐步解释现象，说明哪些数值来自协议、哪些来自当前配置或一次观测。',
        '2. **读者能解释现象**': '2. **读者能解释现象**：第一次出现的总线或外设接口先给需求、数据方向和最小交互图，再拿真实日志/CSV/VCD 逐项对照，直接展示地址、数据与握手结果的推导过程。',
        '3. **读者能记住并复述**': '3. **主线连续清楚**：章节正文完整说明输入、输出、完成条件及下一阶段的需要；关键结论可从当前代码、生成文件和运行记录核对。',
    }
    lines = []
    for line in text.splitlines():
        line = next((replacement for prefix, replacement in replacements.items()
                     if line.startswith(prefix)), line)
        lines.append(line)
    return '\n'.join(lines) + '\n'


def content(source: Path, relative: Path) -> bytes:
    data = (source / relative).read_bytes()
    # Source/docs get local paths. Historical logs, manifests and RTL remain exact.
    if relative.suffix == '.md' and relative.parts[0] != 'results':
        text = tour_markdown(data.decode('utf-8')).replace('soc_integration_tutorial/', 'soc_integration_tour/')
        for old, new in RENAMES.items():
            text = text.replace(f'chapters/{old}', f'chapters/{new}')
        if str(relative) == 'PLAN.md':
            text = ('> tour 同步说明：本计划引入 tutorial 的完整路线与进度。'
                    'tour 的章节按连续讲解组织，00–12 的历史验收尚未逐项重跑；'
                    '13–20A 的同步范围及本地验收见 [进度说明](docs/progress/README.md)。\n\n' + text)
        return text.encode('utf-8')
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT.parent / 'soc_integration_tutorial')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='Copy selected files and record provenance')
    mode.add_argument('--check', action='store_true', help='Fail if selected files differ or are missing')
    args = parser.parse_args()
    source = args.source.resolve()
    if source == ROOT or not (source / '.git').exists():
        parser.error('--source must point to the separate tutorial Git checkout')
    listing = subprocess.run(
        ['git', '-C', str(source), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        check=True, capture_output=True,
    ).stdout
    paths = sorted({Path(p.decode()) for p in listing.split(b'\0') if p})
    files = [p for p in paths if selected(p) and (source / p).is_file()]
    changed = []
    records = []
    for relative in files:
        data = content(source, relative)
        destination = ROOT / relative
        if not destination.is_file() or destination.read_bytes() != data:
            changed.append(str(relative))
            if args.apply:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                destination.chmod((source / relative).stat().st_mode & 0o777)
        records.append({'path': str(relative), 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    if args.apply:
        # Result inclusion rules are shared; existing tour results remain untouched.
        (ROOT / '.gitignore').write_bytes((source / '.gitignore').read_bytes())
        revision = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'],
                                  check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(['git', '-C', str(source), 'status', '--porcelain'],
                                check=True, capture_output=True, text=True).stdout
        manifest = {'source': 'soc_integration_tutorial', 'source_head': revision,
                    'source_dirty': bool(status), 'scope': '13–20A, docs, PLAN, path helper',
                    'historical_results': 'Copied evidence; not a fresh execution in tour',
                    'files': records}
        report = ROOT / 'docs/progress/sync-manifest.json'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'mode': 'apply' if args.apply else 'check' if args.check else 'preview',
                      'files': len(files), 'bytes': sum(r['bytes'] for r in records),
                      'changed': len(changed), 'examples': changed[:12]},
                     ensure_ascii=False, indent=2))
    if args.check and changed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
