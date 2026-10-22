#!/usr/bin/env python3
"""Read-only Python and optional wecom-cli readiness checks. Never installs or authorizes."""
import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from cli_runtime import command, RuntimeUnavailable


def collect(check_wecom=False):
    result = {
        'platform': {'system': platform.system(), 'machine': platform.machine()},
        'python': {'version': '.'.join(map(str, sys.version_info[:3])),
                   'supported': sys.version_info >= (3, 10)},
        'available_package_managers': [name for name in ['winget', 'brew', 'apt-get', 'dnf', 'npm'] if shutil.which(name)],
        'wecom': {'status': 'not_requested'},
        'online_document_test': 'not_run',
    }
    if not check_wecom:
        return result
    executable = shutil.which('wecom-cli')
    if not executable:
        result['wecom'] = {'status': 'missing'}
        return result
    try:
        argv = command(executable)
        version = subprocess.run([*argv, '--version'], capture_output=True,
                                 text=True, encoding='utf-8', errors='replace', timeout=15)
        match = re.search(r'(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])', version.stdout)
        if version.returncode or not match:
            result['wecom'] = {'status': 'version_check_failed'}
            return result
        parts = tuple(map(int, match.groups()))
        if parts < (1, 2, 1):
            result['wecom'] = {'status': 'upgrade_required', 'version': match.group(0)}
            return result
        auth = subprocess.run([*argv, 'auth', 'show', '--status'],
                              capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
        status = auth.stdout.strip()
        if auth.returncode or status not in {'authorized', 'unauthorized'}:
            status = 'auth_check_failed'
        result['wecom'] = {'status': status, 'version': match.group(0)}
    except subprocess.TimeoutExpired:
        result['wecom'] = {'status': 'check_timed_out'}
    except OSError:
        result['wecom'] = {'status': 'execution_failed'}
    except RuntimeUnavailable:
        result['wecom'] = {'status': 'runtime_adapter_required'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wecom', action='store_true', help='Check CLI version and authorization status without modifying either')
    args = parser.parse_args()
    result = collect(args.wecom)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    ready = result['python']['supported'] and (not args.wecom or result['wecom']['status'] == 'authorized')
    return 0 if ready else 1


if __name__ == '__main__':
    sys.exit(main())
