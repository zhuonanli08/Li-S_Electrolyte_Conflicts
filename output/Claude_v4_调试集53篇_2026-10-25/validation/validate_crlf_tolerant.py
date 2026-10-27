# 一次性：本机 Windows 冻结的文件经 git 由 CRLF 转为 LF，校验码按 CRLF 还原后比对；不改 step9a 与冻结记录
import sys, pathlib
root = pathlib.Path('/home/user/Li-S_Electrolyte_Conflicts/scripts')
sys.path.insert(0, str(root))
src = (root / 'step9a_claude_debug53.py').read_text(encoding='utf-8')
old = "        if locks[pid]['sha256'] != hashlib.sha256(raw).hexdigest():"
new = ("        if locks[pid]['sha256'] != hashlib.sha256(raw).hexdigest() and "
       "locks[pid]['sha256'] != hashlib.sha256(raw.replace(b'\\r\\n', b'\\n').replace(b'\\n', b'\\r\\n')).hexdigest():")
assert src.count(old) == 1
src = src.replace(old, new).replace("if __name__ == '__main__':", "if False:")
g = {'__file__': str(root / 'step9a_claude_debug53.py'), '__name__': 'step9a_tolerant'}
exec(compile(src, 'step9a_tolerant', 'exec'), g)
g['cmd_validate']()
