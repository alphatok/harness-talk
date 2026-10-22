"""Resolve npm's Windows shim to Node argv; never pass document data to cmd.exe."""
import json
import shutil
from pathlib import Path


class RuntimeUnavailable(Exception):
    pass


def command(executable):
    path = Path(executable)
    if path.suffix.lower() not in {'.cmd', '.bat', '.ps1'}:
        return [str(path)]
    # npm global on Windows, or a project-local node_modules/.bin shim.
    roots = [path.parent / 'node_modules' / '@wecom' / 'cli',
             path.parent.parent / '@wecom' / 'cli']
    sibling_node = path.parent / 'node.exe'
    node = str(sibling_node) if sibling_node.is_file() else shutil.which('node')
    if not node:
        raise RuntimeUnavailable('Windows CLI需要Node运行时，请按跨平台初始化流程修复。')
    for root in roots:
        try:
            package = json.loads((root / 'package.json').read_text(encoding='utf-8'))
            if not isinstance(package, dict) or package.get('name') != '@wecom/cli':
                continue
            bins = package.get('bin')
            entry = bins.get('wecom-cli') if isinstance(bins, dict) else bins
            if not isinstance(entry, str):
                continue
            target = (root / entry).resolve()
            if target.is_relative_to(root.resolve()) and target.is_file():
                return [node, str(target)]
        except (OSError, ValueError):
            continue
    raise RuntimeUnavailable('未定位Windows CLI的真实入口；请按跨平台流程检查当前npm包的bin配置。')
