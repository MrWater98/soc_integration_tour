# Source from any working directory. Preserve the user's Python environment.
_soc_tools_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_soc_tools_bin="$_soc_tools_root/external/fpga-tools/oss-cad-suite/bin"
if [ ! -x "$_soc_tools_bin/nextpnr-himbaechel" ]; then
    echo "Missing OSS CAD Suite: extract it under external/fpga-tools/" >&2
    return 1
fi
export PATH="$_soc_tools_bin:$PATH"
unset _soc_tools_root _soc_tools_bin
