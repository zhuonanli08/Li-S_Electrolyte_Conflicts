"""Claude v4 debug-set extraction (53 papers): setup, format gate, freeze, validate.

Same source packets, JSON format and post-freeze checks as the GPT run
(output/GPT_v4_调试集53篇_2026-10-24). Extractors see only the frozen spec and
the source text; no earlier extraction or GPT result is read.

  setup             copy+verify sources, render txt, group papers, freeze spec hash
  check  <draft>    format gate only (JSON, keys, enums, evidence ids, references)
  freeze <draft>    check, then write independent_predictions/{ID}.json once (never overwrite)
  validate          run step8f.validate() on all frozen predictions; write validation/
"""
import argparse
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'Claude_v4_调试集53篇_2026-10-25'
GPT = ROOT / 'output' / 'GPT_v4_调试集53篇_2026-10-24'
CONDITIONS = ['sulfur_loading', 'ES', 'ES_unit', 'Li_thickness', 'rate',
              'formation', 'temperature', 'LiNO3', 'one_C']
ROLES = ['溶剂化溶剂', '弱或非溶剂化溶剂', '盐', '添加剂']
BASIS = ['numeric', 'qualitative', 'figure_only']
DIRS = ['变好', '变坏', '差异小', '不判']
SIDES = ['强侧', '弱侧', '其他']
CATS = ['正极反应', '多硫化物穿梭', '负极锂', '电解液消耗']
SOURCES = ['本文结论', '本文结论（与他文一致）', '本文推测', '转述他文或通用说法']
TOP = {'paper_id': str, 'doi': str, 'formulations': list, 'control_id': (str, type(None)),
       'control_type': str, 'gradients': list, 'properties': list, 'tests': list,
       'mechanisms': list, 'design_claims': list, 'figure_requests': list,
       'gaps': list, 'source_review': dict}

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def setup():
    mf = json.loads((GPT / 'manifest.json').read_text(encoding='utf-8'))
    for sub in ['sources', 'sources_txt', 'drafts', 'independent_predictions', 'freeze', 'revisions']:
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GPT / 'manifest.json', OUT / 'manifest.json')
    sizes = {}
    for m in mf:
        src = GPT / 'sources' / f"{m['id']}.json"
        dst = OUT / 'sources' / f"{m['id']}.json"
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), m['id']
        segs = json.loads(dst.read_text(encoding='utf-8'))
        lines = [f"# {m['id']} | {m['doi']} | {m['title']}",
                 f"# 正文句数 {sum(s['part']=='main' for s in segs)}，SI 句数 {sum(s['part']=='si' for s in segs)}"]
        part = None
        for s in segs:
            if s['part'] != part:
                part = s['part']
                lines.append('\n===== 正文 =====' if part == 'main' else '\n===== SI =====')
            lines.append(f"[{s['id']} p{s['page']}] {s['text']}")
        (OUT / 'sources_txt' / f"{m['id']}.txt").write_text('\n'.join(lines) + '\n', encoding='utf-8')
        sizes[m['id']] = sum(len(s['text']) for s in segs)
    # first-fit decreasing: <=3 papers and <=170k characters per extractor
    groups = []
    for pid in sorted(sizes, key=sizes.get, reverse=True):
        for g in groups:
            if len(g['ids']) < 3 and g['chars'] + sizes[pid] <= 170000:
                g['ids'].append(pid); g['chars'] += sizes[pid]; break
        else:
            groups.append({'ids': [pid], 'chars': sizes[pid]})
    for i, g in enumerate(groups, 1):
        g['name'] = f'G{i:02}'
    save(OUT / 'groups.json', groups)
    print(len(mf), 'papers;', len(groups), 'groups')
    for g in groups:
        print(g['name'], g['chars'], ' '.join(g['ids']))

def check(path):
    """Return (data, errors). Format only: content correctness is judged after freeze."""
    errs = []
    try:
        d = json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        return None, [f'JSON 解析失败：{e}']
    if not isinstance(d, dict):
        return None, ['顶层必须是对象']
    for k, t in TOP.items():
        if k not in d:
            errs.append(f'缺顶层字段 {k}')
        elif not isinstance(d[k], t):
            errs.append(f'顶层字段 {k} 类型错')
    if errs:
        return d, errs
    pid = d['paper_id']
    srcp = OUT / 'sources' / f'{pid}.json'
    if not srcp.exists():
        return d, [f'未知 paper_id {pid}']
    if Path(path).stem.split('_')[0] != pid:
        errs.append(f'文件名与 paper_id 不一致：{Path(path).name} vs {pid}')
    ids = {s['id'] for s in json.loads(srcp.read_text(encoding='utf-8'))}

    def walk(o, where):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('evidence_ids', 'anchor_quote_ids'):
                    if not isinstance(v, list):
                        errs.append(f'{where}.{k} 必须是列表')
                        continue
                    for x in v:
                        if x not in ids:
                            errs.append(f'{where}.{k} 原句编号不存在：{x}')
                else:
                    walk(v, f'{where}.{k}')
        elif isinstance(o, list):
            for i, x in enumerate(o):
                walk(x, f'{where}[{i}]')
    walk(d, pid)

    fids = [f.get('id') for f in d['formulations']]
    tids = [t.get('id') for t in d['tests']]
    mids = [m.get('id') for m in d['mechanisms']]
    rids = [r.get('id') for t in d['tests'] for r in t.get('results', [])]
    for name, xs in [('配方', fids), ('测试', tids), ('机制', mids), ('结果', rids)]:
        if None in xs or '' in xs:
            errs.append(f'{name}缺 id')
        if len(xs) != len(set(xs)):
            errs.append(f'{name} id 重复')
    if d['control_id'] is not None and d['control_id'] not in fids:
        errs.append(f'control_id 不在配方里：{d["control_id"]}')
    for f in d['formulations']:
        for k in ['name', 'components', 'raw_formula', 'evidence_ids']:
            if k not in f:
                errs.append(f'配方 {f.get("id")} 缺 {k}')
        for c in f.get('components', []):
            if c.get('role') not in ROLES:
                errs.append(f'配方 {f.get("id")} 组分 {c.get("name")} 角色非法：{c.get("role")}')
            for k in ['name', 'amount', 'unit']:
                if k not in c:
                    errs.append(f'配方 {f.get("id")} 组分缺 {k}')
    for g in d['gradients']:
        for k in ['name', 'order', 'values', 'solvation_axis', 'evidence_ids']:
            if k not in g:
                errs.append(f'梯度 {g.get("name")} 缺 {k}')
        for x in g.get('order', []):
            if x not in fids:
                errs.append(f'梯度 {g.get("name")} 引用未知配方 {x}')
    for p in d['properties']:
        for k in ['name', 'values', 'direction', 'method', 'system', 'evidence_ids']:
            if k not in p:
                errs.append(f'性质 {p.get("name")} 缺 {k}')
    for t in d['tests']:
        tid = t.get('id')
        for k in ['name', 'cell', 'conditions', 'formulations', 'evidence_ids', 'results']:
            if k not in t:
                errs.append(f'测试 {tid} 缺 {k}')
        for k in CONDITIONS:
            if k not in t.get('conditions', {}):
                errs.append(f'测试 {tid} 条件缺 {k}（没写填“未报告”）')
        for x in t.get('formulations', []):
            if x not in fids:
                errs.append(f'测试 {tid} 引用未知配方 {x}')
        for r in t.get('results', []):
            rid = r.get('id')
            for k in ['metric', 'A', 'B', 'value_A', 'value_B', 'unit', 'point', 'basis',
                      'direction_text', 'same_conditions', 'evidence_ids', 'reason']:
                if k not in r:
                    errs.append(f'结果 {rid} 缺 {k}')
            for k in ['A', 'B']:
                if r.get(k) not in fids:
                    errs.append(f'结果 {rid} 的 {k} 不是配方 id：{r.get(k)}')
            if r.get('basis') not in BASIS:
                errs.append(f'结果 {rid} basis 非法：{r.get("basis")}')
            if r.get('direction_text') not in DIRS:
                errs.append(f'结果 {rid} direction_text 非法：{r.get("direction_text")}')
            if not isinstance(r.get('same_conditions'), bool):
                errs.append(f'结果 {rid} same_conditions 必须是 true/false')
            if r.get('basis') != 'figure_only' and not r.get('evidence_ids'):
                errs.append(f'结果 {rid} 没有原句')
    for m in d['mechanisms']:
        mid = m.get('id')
        for k in ['summary', 'A', 'B', 'property', 'categories', 'source_type',
                  'evidence_ids', 'test_ids', 'side']:
            if k not in m:
                errs.append(f'机制 {mid} 缺 {k}')
        if not m.get('evidence_ids'):
            errs.append(f'机制 {mid} 没有原句')
        for c in m.get('categories', []):
            if c not in CATS:
                errs.append(f'机制 {mid} 过程大类非法：{c}')
        if m.get('source_type') not in SOURCES:
            errs.append(f'机制 {mid} 来源非法：{m.get("source_type")}')
        if m.get('side') not in SIDES:
            errs.append(f'机制 {mid} side 非法：{m.get("side")}')
        for x in m.get('test_ids', []):
            if x not in tids:
                errs.append(f'机制 {mid} 引用未知测试 {x}')
        for k in ['A', 'B']:
            if m.get(k) not in fids + ['全梯度']:
                errs.append(f'机制 {mid} 的 {k} 不是配方 id 或“全梯度”：{m.get(k)}')
    for x in d['design_claims']:
        if 'summary' not in x or not x.get('evidence_ids'):
            errs.append('设计主张缺 summary 或原句')
    for x in d['figure_requests']:
        for k in ['test_id', 'figure', 'part', 'metric', 'A', 'B', 'target_point',
                  'anchor_quote_ids', 'reason']:
            if k not in x:
                errs.append(f'读图登记缺 {k}')
        if x.get('test_id') not in tids:
            errs.append(f'读图登记引用未知测试 {x.get("test_id")}')
        if x.get('part') not in ('main', 'si'):
            errs.append(f'读图登记 part 只能是 main/si：{x.get("part")}')
    for k in ['main', 'si', 'notes']:
        if k not in d['source_review']:
            errs.append(f'source_review 缺 {k}')
    return d, errs

def cmd_check(path):
    d, errs = check(path)
    if errs:
        print(f'格式检查未通过（{len(errs)} 处）：')
        for e in errs[:80]:
            print(' -', e)
        return 1
    n = sum(len(t['results']) for t in d['tests'])
    print(f"格式检查通过：{d['paper_id']} 配方 {len(d['formulations'])}、测试 {len(d['tests'])}、"
          f"结果 {n}、机制 {len(d['mechanisms'])}、读图登记 {len(d['figure_requests'])}")
    return 0

def cmd_freeze(path):
    if cmd_check(path):
        print('未冻结：先改正格式问题。')
        return 1
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    pid = d['paper_id']
    dst = OUT / 'independent_predictions' / f'{pid}.json'
    raw = Path(path).read_bytes()
    try:
        with open(dst, 'xb') as f:  # 'x': the first frozen version can never be overwritten
            f.write(raw)
    except FileExistsError:
        print(f'{pid} 已冻结，不能覆盖；改动只能另存 revisions/。')
        return 1
    digest = hashlib.sha256(raw).hexdigest()
    save(OUT / 'freeze' / f'{pid}.json',
         {'paper_id': pid, 'sha256': digest, 'path': f'independent_predictions\\{pid}.json',
          'frozen_at': datetime.datetime.now().isoformat(timespec='seconds')})
    print(f'已冻结 {pid} sha256={digest}')
    return 0

def cmd_validate():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import step8f_validate_independent as v8f
    import collections
    mf = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    locks = {}
    for p in sorted((OUT / 'freeze').glob('*.json')):
        x = json.loads(p.read_text(encoding='utf-8'))
        locks[x['paper_id']] = x
    issues, evidence, directions, counts = [], [], [], {}
    for p in sorted((OUT / 'independent_predictions').glob('*.json')):
        raw = p.read_bytes()
        d = json.loads(raw)
        pid = d['paper_id']
        if pid not in locks:
            raise ValueError(f'{pid} 没有冻结记录')
        if locks[pid]['sha256'] != hashlib.sha256(raw).hexdigest():
            raise ValueError(f'冻结预测被修改：{pid}')
        src = {s['id']: s for s in json.loads((OUT / 'sources' / f'{pid}.json').read_text(encoding='utf-8'))}
        ii, ee, dd = v8f.validate(d, src)
        issues += ii; evidence += ee; directions += dd
        counts[pid] = {'formulations': len(d['formulations']), 'tests': len(d['tests']),
                       'results': sum(len(t['results']) for t in d['tests']),
                       'mechanisms': len(d['mechanisms']),
                       'figure_requests': len(d['figure_requests'])}
    save(OUT / 'prediction_freeze.json', {k: {'sha256': v['sha256'], 'path': v['path']} for k, v in sorted(locks.items())})
    dest = OUT / 'validation'
    save(dest / 'issues.json', issues); save(dest / 'evidence.json', evidence)
    save(dest / 'numeric_directions.json', directions)
    stats = {'completed_papers': len(counts), 'expected_papers': len(mf),
             'missing_papers': [m['id'] for m in mf if m['id'] not in counts],
             'counts': counts, 'issue_types': dict(collections.Counter(i['code'] for i in issues)),
             'precision': None, 'recall': None, 'note': '机械检查，不能替代语义核对或召回率'}
    save(dest / 'status.json', stats)
    print(json.dumps({k: v for k, v in stats.items() if k != 'counts'}, ensure_ascii=False))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['setup', 'check', 'freeze', 'validate'])
    ap.add_argument('path', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'setup':
        setup()
    elif a.cmd == 'validate':
        cmd_validate()
    else:
        sys.exit((cmd_check if a.cmd == 'check' else cmd_freeze)(a.path))
