#!/usr/bin/env python3
"""Build a separate nextpnr viewer for restoring Gowin routed snapshots."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parents[1]
REVISION = '861c57be9c9a0c38ab60b0eabd19903db37efa22'


def run(command, **kwargs):
    subprocess.run(command, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 16:
        parser.error('jobs must be 1..16')
    source = ROOT/'external/nextpnr-gui-viewer'
    deps = ROOT/'external/nextpnr-viewer-deps'
    out = ROOT/'results/14e-gui'
    deps.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    if not (source/'.git').exists():
        run(['git', 'clone', '--filter=blob:none', '--no-checkout',
             'https://github.com/YosysHQ/nextpnr.git', str(source)])
        run(['git', 'checkout', REVISION], cwd=source)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if head != REVISION:
        raise RuntimeError('Viewer source must match pinned revision ' + REVISION)
    run(['git', 'submodule', 'update', '--init', '--recursive'], cwd=source)
    patch = CHAPTER/'patches/nextpnr-readonly-gui.patch'
    applied = subprocess.run(['git', 'apply', '--reverse', '--check', str(patch)],
                             cwd=source, capture_output=True).returncode == 0
    if not applied:
        run(['git', 'apply', '--check', str(patch)], cwd=source)
        run(['git', 'apply', str(patch)], cwd=source)
    if not Path('/usr/include/x86_64-linux-gnu/qt5/QtWidgets/QApplication').exists():
        raise RuntimeError('Qt5 development headers required: qtbase5-dev and libqt5opengl5-dev')
    cmake = deps/'cmake/data/bin/cmake'
    if not cmake.exists():
        run([sys.executable, '-m', 'pip', 'install', '--target', str(deps), 'cmake==4.4.4'])
    eigen = deps/'usr/lib/cmake/eigen3'
    if not eigen.exists():
        run(['apt', 'download', 'libeigen3-dev'], cwd=deps)
        package = sorted(deps.glob('libeigen3-dev_*.deb'))[-1]
        run(['dpkg-deb', '-x', str(package), str(deps)])
        candidates = list(deps.rglob('Eigen3Config.cmake'))
        if len(candidates) != 1:
            raise RuntimeError('Cannot locate extracted Eigen3 configuration')
        eigen = candidates[0].parent
    # This extracted Ubuntu package exports /usr/include/eigen3. Provide its
    # headers through an existing source include directory without installing it.
    include_link = source/'common/place/Eigen'
    if not include_link.exists():
        include_link.symlink_to(deps/'usr/include/eigen3/Eigen', target_is_directory=True)
    build = source/'build'
    command = [str(cmake), '-S', str(source), '-B', str(build), '-G', 'Ninja',
               '-DARCH=himbaechel', '-DHIMBAECHEL_UARCH=gowin', '-DHIMBAECHEL_GOWIN_DEVICES=',
               '-DBUILD_GUI=ON', '-DBUILD_TESTS=OFF', '-DUSE_IPO=OFF',
               '-DCMAKE_BUILD_TYPE=RelWithDebInfo', '-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O1 -g1 -DNDEBUG',
               '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', '-DEigen3_DIR='+str(eigen),
               '-DPython3_EXECUTABLE=/usr/bin/python3', '-DPYTHON_EXECUTABLE=/usr/bin/python3',
               '-DEXTERNAL_CHIPDB=ON',
               '-DEXTERNAL_CHIPDB_ROOT='+str(ROOT/'external/fpga-tools/oss-cad-suite/share/nextpnr'),
               '-DIMPORT_BBA_FILES='+str(ROOT/'external/fpga-tools/oss-cad-suite/share/nextpnr')]
    with (out/'configure.log').open('w') as log:
        run(command, stdout=log, stderr=subprocess.STDOUT)
    with (out/'build.log').open('w') as log:
        run(['ninja', '-C', str(build), 'nextpnr-himbaechel', '-j'+str(args.jobs)],
            stdout=log, stderr=subprocess.STDOUT)
    binary = build/'nextpnr-himbaechel'
    metadata = {'source_revision': head, 'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
                'purpose': 'view saved placement/routing; original frequency experiments use unmodified OSS CAD Suite',
                'binary': str(binary), 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                'configure_command': command,
                'tool_version': subprocess.check_output([str(binary), '--version'], stderr=subprocess.STDOUT, text=True).strip()}
    (out/'build-manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print('Viewer built:', binary)


if __name__ == '__main__':
    main()
