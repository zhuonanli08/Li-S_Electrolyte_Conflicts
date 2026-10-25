"""Qwen v4 debug-set extraction (53 papers) via 并行智算云 (llmapi.paratera.com).

Same frozen spec (parts 1-2 of the Claude extraction_spec.md), same source
packets, same JSON format, same format gate and post-freeze checks as the
Claude/GPT runs. One API call per paper; format errors (never content hints)
are sent back for at most 2 repair rounds; the first passing JSON is frozen.

  setup               copy+verify sources, build and hash the system prompt
  run ID [ID ...]     extract, check, freeze the given papers (skip frozen ones)
  run all [--workers N]
  validate            run step8f.validate() on all frozen predictions
  trial ID --label L --model M [--thinking]
                      setting comparison: same prompt, writes only to 设置对比/{L}/ (not the main freeze)
"""
import argparse
import datetime
import hashlib
import json
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import step9a_claude_debug53 as s9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / '云端_2026-10-25_千问调试集53篇'
CLAUDE = s9.OUT
s9.OUT = OUT  # step9a.check()/validate() read sources and freeze records from OUT
BASE_URL = 'https://llmapi.paratera.com/v1'
MODEL = 'Qwen3.8-27B'
MAX_TOKENS = 65536
REPAIR_ROUNDS = 2
LOCK = threading.Lock()

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HEADER = """# 锂硫电解液论断式提取规程（千问 API 版，2026-10-25）

你是锂硫电池电解液文献的提取员。本说明第一部分逐字抄自现行课题方案 §0 和 §5.7，第二部分是输出格式；与 Claude、GPT 调试集用的是同一份规程。第三部分是 API 版的工作要求。

---

"""

PART3 = """
---

# 第三部分：工作要求（API 版）

- 下一条消息是一篇论文的全文（正文 + SI，若有），每行开头方括号里的 `M0001`/`S0001` 是原句编号，`p` 后是页码。
- 只依据这篇原文和本说明提取，不用常识或其他文献补数。通读全文（正文 + SI；参考文献列表可略读），不只靠关键词。
- 只输出一个 JSON 对象（第二部分的格式），不要任何解释、不要 Markdown 代码块标记。所有说明性文字用简体中文。
- `source_review.notes` 写明是否通读正文与 SI；原文没有 SI 时 `si` 填 false 并写明。

**提取要求重申**：
- 每个数字必须出现在它挂的原句里（测试条件的数可以在本篇其他条件原句里）；反算的数在 reason 里写公式。
- 机制一句一条，标来源和过程大类；作者说法覆盖整条梯度时记“全梯度”；只靠转述句支撑的说法照记但 source_type 标“转述他文或通用说法”。作者在同一篇里自己写的例外也挂上。
- 只读两类图：Li‖S 循环类测试里文字缺的同一测试容量侧；梯度上只在图里有数的档。阻抗谱、XPS、SEM、电压曲线等不登记。读图只登记到 figure_requests，不目测估数。
- 不确定的照原文写并在 reason 或 gaps 说明，不编造、不用常识补数。
"""

def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf-8')).hexdigest()

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def setup():
    for sub in ['sources', 'sources_txt', 'raw', 'drafts', 'independent_predictions', 'freeze', 'failed']:
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CLAUDE / 'manifest.json', OUT / 'manifest.json')
    mf = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    for m in mf:
        for sub, ext in [('sources', 'json'), ('sources_txt', 'txt')]:
            src, dst = CLAUDE / sub / f"{m['id']}.{ext}", OUT / sub / f"{m['id']}.{ext}"
            shutil.copyfile(src, dst)
            assert sha(src.read_bytes()) == sha(dst.read_bytes()), m['id']
    spec = (CLAUDE / 'extraction_spec.md').read_text(encoding='utf-8').splitlines()
    start = spec.index('# 第一部分：方案原文（§0 主线、§5.7 论断式提取）')
    end = spec.index('# 第三部分：工作流程与隔离（每个子代理必须遵守）')
    body = '\n'.join(spec[start:end]).rstrip().rstrip('-').rstrip()
    prompt = HEADER + body + '\n' + PART3
    (OUT / 'prompt_system.md').write_text(prompt, encoding='utf-8')
    save(OUT / 'run_config.json', {
        'date': '2026-10-25',
        'platform': '并行智算云 llmapi.paratera.com（OpenAI 兼容接口）',
        'model': MODEL, 'enable_thinking': False, 'temperature': 0, 'max_tokens': MAX_TOKENS,
        'repair_rounds': REPAIR_ROUNDS,
        'repair_policy': '只回传 step9a.check() 的格式错误（JSON、字段、枚举、原句编号存在、编号引用），不提示内容对错',
        'prompt': 'prompt_system.md = Claude extraction_spec.md 第一、二部分逐字 + API 版第三部分；论文全文作为用户消息',
        'prompt_sha256': sha(prompt),
        'claude_spec_sha256': sha((CLAUDE / 'extraction_spec.md').read_bytes()),
        'sources': '从 Claude_v4_调试集53篇_2026-10-25 复制（逐个 SHA256 核对一致；该文件夹的 sources 已与 GPT_v4 核对过）',
        'freeze': 'independent_predictions/{ID}.json 独占创建、不覆盖；SHA256 记在 freeze/{ID}.json',
        'scope': len(mf)})
    print('setup 完成：', len(mf), '篇；prompt', len(prompt), '字符，sha256', sha(prompt)[:16])

def client():
    from openai import OpenAI
    return OpenAI(base_url=BASE_URL, api_key='proxy-injected', timeout=1800, max_retries=0)

def call(cli, messages, model=MODEL, thinking=False):
    """Streamed chat call; returns (text, finish_reason, usage, seconds, reasoning_chars)."""
    t0 = time.time()
    for attempt in range(4):
        try:
            stream = cli.chat.completions.create(
                model=model, messages=messages, temperature=0, max_tokens=MAX_TOKENS,
                stream=True, stream_options={'include_usage': True},
                extra_body={'enable_thinking': thinking})
            parts, finish, usage, reasoning = [], None, None, 0
            for ch in stream:
                if ch.usage:
                    usage = ch.usage.model_dump()
                if ch.choices:
                    c = ch.choices[0]
                    if c.delta and c.delta.content:
                        parts.append(c.delta.content)
                    if c.delta and getattr(c.delta, 'reasoning_content', None):
                        reasoning += len(c.delta.reasoning_content)
                    if c.finish_reason:
                        finish = c.finish_reason
            return ''.join(parts), finish, usage, round(time.time() - t0, 1), reasoning
        except Exception as e:  # network / rate limit: back off and retry the same request
            if attempt == 3:
                raise
            print(f'  调用出错（{type(e).__name__}: {str(e)[:200]}），{2 ** (attempt + 1)}s 后重试')
            time.sleep(2 ** (attempt + 1))

def strip_json(text):
    t = text.strip()
    if t.startswith('```'):
        t = t.split('\n', 1)[1] if '\n' in t else t
        if t.rstrip().endswith('```'):
            t = t.rstrip()[:-3]
    return t.strip()

def extract(pid, cli, dest=OUT, model=MODEL, thinking=False):
    if (dest / 'independent_predictions' / f'{pid}.json').exists():
        return {'paper_id': pid, 'status': '已冻结，跳过'}
    system = (OUT / 'prompt_system.md').read_text(encoding='utf-8')
    paper = (OUT / 'sources_txt' / f'{pid}.txt').read_text(encoding='utf-8')
    messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': paper}]
    log = {'paper_id': pid, 'model': model, 'enable_thinking': thinking, 'rounds': []}
    for sub in ['raw', 'drafts', 'independent_predictions', 'freeze', 'logs']:
        (dest / sub).mkdir(parents=True, exist_ok=True)
    for rnd in range(REPAIR_ROUNDS + 1):
        text, finish, usage, secs, reasoning = call(cli, messages, model, thinking)
        (dest / 'raw' / f'{pid}_r{rnd}.txt').write_text(text, encoding='utf-8')
        draft = dest / 'drafts' / f'{pid}_r{rnd}.json'
        draft.write_text(strip_json(text), encoding='utf-8')
        d, errs = s9.check(draft)
        if finish == 'length':
            errs = [f'输出被截断（达到 max_tokens={MAX_TOKENS}）'] + errs
        log['rounds'].append({'round': rnd, 'finish_reason': finish, 'usage': usage,
                              'seconds': secs, 'chars': len(text), 'reasoning_chars': reasoning,
                              'format_errors': errs[:80],
                              'n_format_errors': len(errs)})
        if not errs:
            raw = json.dumps(d, ensure_ascii=False, indent=2).encode('utf-8')
            dst = dest / 'independent_predictions' / f'{pid}.json'
            with open(dst, 'xb') as f:  # first frozen version can never be overwritten
                f.write(raw)
            save(dest / 'freeze' / f'{pid}.json',
                 {'paper_id': pid, 'sha256': sha(raw), 'path': f'independent_predictions/{pid}.json',
                  'round': rnd, 'frozen_at': datetime.datetime.now().isoformat(timespec='seconds')})
            log['status'] = f'冻结（第 {rnd} 轮通过）'
            break
        if finish == 'length' or rnd == REPAIR_ROUNDS:
            log['status'] = '失败：' + ('输出被截断' if finish == 'length' else f'修正 {REPAIR_ROUNDS} 轮后格式仍不通过')
            break
        messages += [{'role': 'assistant', 'content': text},
                     {'role': 'user', 'content': f'格式检查未通过（{len(errs)} 处）：\n' +
                      '\n'.join(f'- {e}' for e in errs[:80]) +
                      '\n请只改正这些格式问题，输出改正后的完整 JSON 对象，不要其他文字。'}]
    save(dest / 'logs' / f'{pid}.json', log)
    if not log['status'].startswith('冻结'):
        save(dest / 'failed' / f'{pid}.json', log)
    tok = [r['usage'] or {} for r in log['rounds']]
    with LOCK:
        print(f"{pid}: {log['status']}；轮数 {len(log['rounds'])}；输入 {sum(u.get('prompt_tokens', 0) for u in tok)} "
              f"输出 {sum(u.get('completion_tokens', 0) for u in tok)} token；"
              f"{sum(r['seconds'] for r in log['rounds'])} s", flush=True)
    return log

def run(ids, workers):
    mf = [m['id'] for m in json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))]
    ids = mf if ids == ['all'] else ids
    bad = [i for i in ids if i not in mf]
    assert not bad, f'未知编号 {bad}'
    cli = client()
    def one(pid):
        try:
            return extract(pid, cli)
        except Exception as e:
            log = {'paper_id': pid, 'status': f'失败：调用异常 {type(e).__name__}: {str(e)[:300]}'}
            save(OUT / 'failed' / f'{pid}.json', log)
            print(f'{pid}: {log["status"]}', flush=True)
            return log
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, ids))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['setup', 'run', 'validate', 'trial'])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--label')
    ap.add_argument('--model', default=MODEL)
    ap.add_argument('--thinking', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'setup':
        setup()
    elif a.cmd == 'run':
        run(a.ids, a.workers)
    elif a.cmd == 'trial':
        cli = client()
        for pid in a.ids:
            extract(pid, cli, OUT / '设置对比' / a.label, a.model, a.thinking)
    else:
        s9.cmd_validate()
