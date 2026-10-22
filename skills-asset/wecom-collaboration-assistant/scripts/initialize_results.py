#!/usr/bin/env python3
"""Initialize an explicitly selected result sheet using the optional 8-column template. Read-only unless --apply is explicit."""
import argparse
import copy
import json
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path
from cli_runtime import command, RuntimeUnavailable

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ['产品/模块', '用例编号', '用例名称', '执行人', '执行时间', '测试结果', '实际结果', '测试证据']

class OperationError(Exception):
    pass

def cli(args):
    exe = shutil.which('wecom-cli')
    if not exe:
        raise OperationError('企微工具未安装，请先按首次引导检查。')
    try:
        p = subprocess.run([*command(exe), 'smartsheet', *args], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=90)
    except RuntimeUnavailable as error:
        raise OperationError(str(error)) from None
    except subprocess.TimeoutExpired:
        raise OperationError('操作超时，状态待核对。请先回读目标，不能重复提交新增。') from None
    except OSError:
        raise OperationError('企微工具无法启动，请检查安装与执行权限。') from None
    try:
        out = json.loads(p.stdout)
    except (ValueError, TypeError):
        raise OperationError('工具返回无法解析，状态待核对；不要重试新增。') from None
    if not isinstance(out, dict):
        raise OperationError('工具返回结构不符，状态待核对；不要重试新增。')
    if p.returncode or out.get('errcode', 0):
        code = out.get('errcode', 'unknown')
        if code == 538005:
            raise OperationError('查询权限不足。按随包记录读取规范降级读取，不能绕过权限。')
        if code == 851003 or 'no authority' in str(out.get('errmsg', '')).lower():
            raise OperationError('记录写入受限。停止重试，按随包Webhook说明处理。')
        raise OperationError('企微操作未完成，错误码：' + str(code))
    return {k: v for k, v in out.items() if k not in {'security_notice', 'extra_identity_context'}}

def call(doc, command, payload):
    out = cli([*command.split(), '--json', json.dumps({'docid': doc, **payload}, ensure_ascii=False)])
    if command.endswith(' list'):
        key = command.split()[0]
        if not isinstance(out.get(key), list) or any(not isinstance(row, dict) for row in out[key]):
            raise OperationError('列表响应缺失或结构不符，不能当作空列表继续写入。')
        if out.get('has_more') or out.get('next_cursor'):
            raise OperationError('列表尚有分页，本初始化器不能使用不完整结构；请改用分页接口处理。')
        if payload.get('limit') and len(out[key]) >= payload['limit']:
            raise OperationError('列表达到读取上限，完整性待确认；停止写入。')
    return out

def query(doc, sql):
    out = cli(['records', 'query', '--docid', doc, '--sql', sql])
    values = out.get('values')
    if not isinstance(values, list) or len(values) != 1:
        raise OperationError('查询未返回本次SQL结果，不能当作空表继续写入。')
    try:
        value = json.loads(values[0]) if isinstance(values[0], str) else values[0]
    except ValueError:
        raise OperationError('查询内容无法解析，停止写入并核对目标。') from None
    if (not isinstance(value, dict) or not isinstance(value.get('rows'), list)
            or any(not isinstance(row, dict) for row in value['rows'])):
        raise OperationError('查询行结构不符，不能当作空表继续写入。')
    return value['rows']

def option_maps(fields, plan):
    maps = {}
    for name in ['产品/模块', '测试结果']:
        options = fields[name].get('property_single_select', {}).get('options', [])
        if (not options or any(not o.get('id') or not o.get('text') for o in options)
                or len({o['text'] for o in options}) != len(options)):
            raise OperationError('结果表选项缺标识或名称重复，请先核对。')
        maps[name] = {o['text']: o for o in options}
    if any(r['产品/模块'] not in maps['产品/模块'] for r in plan) or '未执行' not in maps['测试结果']:
        raise OperationError('结果表缺匹配选项；先核对，不新增分类。')
    return maps

def identifier(value):
    return '`' + value.replace('`', '``') + '`'

def make_plan(cases, seed_ids, existing, module_field="产品/模块"):
    if not seed_ids or len(seed_ids) != len(set(seed_ids)):
        raise OperationError("用例范围为空或编号重复，请明确本次范围。")
    # Only the explicitly selected cases; preserve existing execution results.
    selected = {}
    for row in cases:
        key = row.get('用例编号')
        if key in seed_ids:
            if key in selected:
                raise OperationError('用例库有重复编号，先核对再初始化。')
            if not row.get(module_field) or not row.get('用例名称'):
                raise OperationError('用例缺已有产品/模块归属或名称，请先核对；不得自动新增分类。')
            selected[key] = row
    if set(selected) != set(seed_ids):
        raise OperationError('指定用例未齐全，请先核对；不会自行补造。')
    existing_keys = [r.get('用例编号') for r in existing if r.get('用例编号') in seed_ids]
    if len(existing_keys) != len(set(existing_keys)):
        raise OperationError('结果表中指定编号重复，请先核对，不自动覆盖。')
    existing_ids = set(existing_keys)
    return [{'产品/模块': selected[key][module_field], '用例编号': key,
             '用例名称': selected[key]['用例名称'], '测试结果': '未执行'}
            for key in seed_ids if key not in existing_ids]

def resolve_target(target_url=None):
    if not target_url:
        raise OperationError('必须明确指定本次目标链接；本包没有默认文档。')
    url = urllib.parse.urlparse(target_url)
    parts = url.path.rstrip('/').split('/')
    if (url.scheme != 'https' or url.netloc != 'doc.weixin.qq.com'
            or len(parts) != 3 or parts[1] != 'smartsheet' or not parts[-1]):
        raise OperationError('目标不是有效企微智能表格链接。')
    return parts[-1], urllib.parse.urlunparse(url._replace(fragment=''))

def verify_views(views, tfields):
    by_title = {v['view_title']: v for v in views.get('views', [])}
    for name in ['按模块查看', '失败与阻塞']:
        if name not in by_title:
            raise OperationError('默认结果视图缺失，先回读核对。')
        groups = by_title[name].get('property', {}).get('group_spec', {}).get('groups', [])
        if not any(g.get('field_title') == '产品/模块' or g.get('field_id') == tfields['产品/模块']['field_id'] for g in groups):
            raise OperationError('视图未按模块分组，不能报告完成。')
    spec = by_title['失败与阻塞'].get('property', {}).get('filter_spec', {})
    expected = {o['id'] for o in tfields['测试结果']['property_single_select']['options'] if o['text'] in ['失败', '阻塞']}
    actual = set()
    conditions = spec.get('conditions', [])
    for c in conditions:
        if c.get('field_title') != '测试结果' and c.get('field_id') != tfields['测试结果']['field_id']:
            raise OperationError('视图筛选字段不符，不能报告完成。')
        if c.get('operator') != 'is':
            raise OperationError('视图筛选操作不符，不能报告完成。')
        actual.update(c.get('string_value', {}).get('value', []))
    if spec.get('conjunction') != 'or' or len(conditions) != 2 or actual != expected or len(expected) != 2:
        raise OperationError('失败与阻塞筛选回读不符，不能报告完成。')

def configure_views(doc, target, tfields):
    views = call(doc, 'views list', {'sheet_title': target, 'limit': 100})
    owned = ['按模块查看', '失败与阻塞']
    missing = [name for name in owned if name not in {v['view_title'] for v in views.get('views', [])}]
    if missing:
        call(doc, 'views add', {'sheet_title': target, 'views': [{'view_title': name, 'view_type': 'grid'} for name in missing]})
        views = call(doc, 'views list', {'sheet_title': target, 'limit': 100})
    updates = []
    for v in views['views']:
        if v['view_title'] not in owned:
            continue
        prop = {'frozen_field_count': 2, 'group_spec': {'groups': [{'field_title': '产品/模块', 'desc': False}]}}
        if v['view_title'] == '失败与阻塞':
            prop['filter_spec'] = {'conjunction': 'or', 'conditions': [{'field_title': '测试结果', 'field_type': 'single_select', 'operator': 'is', 'string_value': {'value': [name]}} for name in ['失败', '阻塞']]}
        else:
            prop['sort_spec'] = {'sort_infos': [{'field_title': '用例编号', 'desc': False}]}
        updates.append({'view_id': v['view_id'], 'property': prop,
                        'col_infos': [{'field_title': n, 'width': 400 if n == '实际结果' else 160 if n in ['执行人', '执行时间'] else 120 if n == '测试结果' else 280} for n in HEADERS]})
    call(doc, 'views update', {'sheet_title': target, 'views': updates})
    views = call(doc, 'views list', {'sheet_title': target, 'limit': 100})
    verify_views(views, tfields)
    return views

def initialize(apply=False, target_url=None, case_ids=None, source_sheet='用例库',
               result_sheet='测试结果', module_field='产品/模块', all_cases=False,
               configure_standard_views=False):
    doc, resolved_url = resolve_target(target_url)
    if bool(case_ids) == bool(all_cases):
        raise OperationError('显式指定用例编号，或选择全部用例；二者必须选一。')
    if case_ids and len(case_ids) != len(set(case_ids)):
        raise OperationError('指定用例编号重复。')
    if source_sheet == result_sheet or not all([source_sheet, result_sheet, module_field]):
        raise OperationError('源表、结果表必须不同，且字段名不能为空。')
    schema = json.loads((ROOT / 'assets/table-schema.json').read_text(encoding='utf-8'))
    sheets = call(doc, 'sheets list', {}).get('sheets', [])
    source = source_sheet
    target = result_sheet
    if source not in {s.get('title') for s in sheets}:
        raise OperationError('指定用例库不存在，不新建替代表。')
    source_fields = call(doc, 'fields list', {'sheet_title': source, 'limit': 100})
    by_name = {f['field_title']: f for f in source_fields.get('fields', [])}
    for key in ['用例编号', '用例名称', module_field]:
        if key not in by_name:
            raise OperationError('用例库缺所需字段，先核对实际结构。')
    module_definition = by_name[module_field]
    if module_definition['field_type'] != 'single_select':
        raise OperationError('模块字段与已知模板不兼容，先核对。')
    modules = module_definition['property_single_select'].get('options', [])
    module_names = {m['text'] for m in modules}
    cases = query(doc, 'SELECT `用例编号`, `用例名称`, ' + identifier(module_field) + ' FROM ' + identifier(source) + ' LIMIT 1000')
    # If the table is larger, don't silently initialize a partial set.
    if len(cases) >= 1000:
        raise OperationError('用例库超过本初始化器的有界读取范围，请按编号筛选后处理。')
    target_exists = target in {s.get('title') for s in sheets}
    target_fields = None
    existing = []
    if target_exists:
        target_fields = call(doc, 'fields list', {'sheet_title': target, 'limit': 100})
        fields = target_fields.get('fields', [])
        expected = schema['测试结果']['fields']
        if {f['field_title']: f['field_type'] for f in fields} != {f['field_title']: f['field_type'] for f in expected}:
            raise OperationError('已有测试结果表不是约定8列，不删除或修改现有结构，请先核对。')
        existing = query(doc, 'SELECT RECORD_ID, `用例编号`, `产品/模块`, `测试结果` FROM ' + identifier(target) + ' LIMIT 1000')
        if len(existing) >= 1000:
            raise OperationError('结果表达到本初始化器读取上限，不进行不完整查重。')
    selected_ids = [row.get('用例编号') for row in cases] if all_cases else case_ids
    if any(not isinstance(key, str) or not key.strip() for key in selected_ids):
        raise OperationError('指定范围内存在空编号或非文本编号。')
    plan = make_plan(cases, selected_ids, existing, module_field)
    if any(r['产品/模块'] not in module_names for r in plan):
        raise OperationError('归属不在已有模块选项中，需用户确认，不能自动新增。')
    if target_exists:
        option_maps({f['field_title']: f for f in target_fields['fields']}, plan)
    if len(existing) + len(plan) >= 1000:
        raise OperationError('追加后将超过完整回读范围，请缩小或拆分目标表。')
    if len(plan) > 100:
        raise OperationError('本初始化器单次最多追加100条，请缩小本次编号范围。')
    summary = {'target': '本次指定智能表格', 'result_sheet': target, 'source_cases': len(cases),
               'seed_scope': len(selected_ids), 'missing_to_seed': len(plan),
               'mode': 'apply' if apply else 'dry-run', 'result_columns': HEADERS}
    if not apply:
        return summary
    if not target_exists:
        fields = copy.deepcopy(schema['测试结果']['fields'])
        fields[0]['property_single_select']['options'] = [{k: m[k] for k in ['text', 'style'] if k in m} for m in modules]
        call(doc, 'sheets add', {'sheet_title': target, 'fields': fields})
        # Mandatory width setup immediately after new fields.
        views = call(doc, 'views list', {'sheet_title': target, 'limit': 100})
        if not views.get('views'):
            raise OperationError('表已创建但视图未返回，请先回读，不重复新建。')
        call(doc, 'views update', {'sheet_title': target, 'views': [{
            'view_id': views['views'][0]['view_id'], 'view_title': '按模块查看',
            'col_infos': [{'field_title': n, 'width': 400 if n == '实际结果' else 160 if n in ['执行人', '执行时间'] else 120 if n == '测试结果' else 280} for n in HEADERS],
            'property': {'frozen_field_count': 2, 'group_spec': {'groups': [{'field_title': '产品/模块', 'desc': False}]},
                         'sort_spec': {'sort_infos': [{'field_title': '用例编号', 'desc': False}]}}
        }]})
        target_fields = call(doc, 'fields list', {'sheet_title': target, 'limit': 100})
    tfields = {f['field_title']: f for f in target_fields['fields']}
    maps = option_maps(tfields, plan)
    if plan:
        # Existing records were read above, and on a newly created sheet verify it is empty first.
        if not target_exists:
            blanks = query(doc, 'SELECT RECORD_ID, `用例编号` FROM ' + identifier(target) + ' LIMIT 5')
            if blanks:
                raise OperationError('新表存在默认空行，请核对后处理；本脚本不自行删除。')
        records = []
        for row in plan:
            row = dict(row)
            for n in ['产品/模块', '测试结果']:
                row[n] = [{'id': maps[n][row[n]]['id'], 'text': row[n]}]
            records.append({'values': row})
        call(doc, 'records add', {'sheet_title': target, 'records': records})
    if not target_exists or configure_standard_views:
        configure_views(doc, target, tfields)
    # Validate exactly the new seeds, don't treat another colleague's rows as ours.
    verified = query(doc, 'SELECT * FROM ' + identifier(target) + ' LIMIT 1000')
    for seeded in plan:
        hits = [r for r in verified if r.get('用例编号') == seeded['用例编号']]
        if len(hits) != 1 or any(hits[0].get(k) != v for k, v in seeded.items()):
            raise OperationError('回读内容或条数不一致，停止并核对，不重复导入。')
        if any(hits[0].get(k) for k in ['执行人', '执行时间', '实际结果', '测试证据']):
            raise OperationError('初始化行含非预期执行信息，停止并核对。')
    final_fields = call(doc, 'fields list', {'sheet_title': target, 'limit': 100})
    if set(f['field_title'] for f in final_fields['fields']) != set(HEADERS):
        raise OperationError('结果字段回读不一致。')
    views = call(doc, 'views list', {'sheet_title': target, 'limit': 100})
    final_sheets = call(doc, 'sheets list', {})
    sheet = next(s for s in final_sheets['sheets'] if s['title'] == target)
    summary.update({'seeded_this_call': len(plan), 'records_visible': len(verified), 'verified': True,
                    'views': [v['view_title'] for v in views['views']],
                    'url': resolved_url + ('&' if '?' in resolved_url else '?') + 'tab=' + sheet['sheet_id']})
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--target-url', required=True, help='本次明确指定的企微智能表格')
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--case-ids', nargs='+', help='明确指定本次用例编号')
    scope.add_argument('--all-cases', action='store_true', help='明确选择源表全部用例')
    parser.add_argument('--source-sheet', default='用例库')
    parser.add_argument('--result-sheet', default='测试结果')
    parser.add_argument('--module-field', default='产品/模块')
    parser.add_argument('--configure-standard-views', action='store_true', help='明确允许配置按模块查看、失败与阻塞两个同名视图')
    args = parser.parse_args()
    try:
        print(json.dumps(initialize(args.apply, args.target_url, args.case_ids, args.source_sheet, args.result_sheet, args.module_field, args.all_cases, args.configure_standard_views), ensure_ascii=False, indent=2))
    except OperationError as error:
        print(json.dumps({'status': 'needs_attention', 'reason': str(error)}, ensure_ascii=False))
        sys.exit(1)
if __name__ == '__main__':
    main()
