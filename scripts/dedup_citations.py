#!/usr/bin/env python3
"""
dedup_citations.py — 扫描 research/ 下所有 Markdown，按 URL 去重脚注引用并统一编号。

背景：溯源契约要求正文 [^id] + 文末 [^id]: 标题. 日期. URL。不同维度文件常给同一
URL 起不同 id，交付前需按 URL 去重、按正文首次出现顺序分配显示编号，生成合并参考列表。
这是确定性工作，脚本比手工更准更省 token。

用法：
  python3 dedup_citations.py [research_dir]
  research_dir 缺省为 ./research。

输出：
  · 终端打印去重后的参考文献列表（含 [n] 显示编号、原始 id 别名、出现次数）；
  · 写入 {research_dir}/_references.md。

鲁棒性：目录不存在、无 md 文件、脚注格式不规范，均给出提示而不崩溃。
"""
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # 防止非 UTF-8 控制台 UnicodeEncodeError
    except Exception:
        pass

# 导入净化函数——对脚注定义文本中的动态内容做安全处理
try:
    from sanitize_markdown import sanitize_text as _sanitize  # 同目录 import
except ImportError:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir not in sys.path:
        sys.path.insert(0, _script_dir)
    try:
        from sanitize_markdown import sanitize_text as _sanitize
    except ImportError:
        # 脚本不可用时的兜底：内联最小净化
        def _sanitize(t):
            if not isinstance(t, str):
                return str(t)
            return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                     .replace("|", "&#124;").replace("`", "&#96;")
                     .replace("\r", " ").replace("\n", " "))

# 脚注定义：  [^id]: 标题. 日期. URL   （URL 可选）
DEF_RE = re.compile(r"^\[\^([^\]]+)\]:\s*(.+?)\s*$")
# 正文脚注引用： [^id]
REF_RE = re.compile(r"\[\^([^\]]+)\]")
# 从定义文本里抽取 URL（取第一个 http/https 链接）
URL_RE = re.compile(r"https?://[^\s)>\]]+")


def collect_md_files(research_dir):
    files = []
    for root, _dirs, names in os.walk(research_dir):
        for n in names:
            if n.lower().endswith(".md") and not n.startswith("_"):
                files.append(os.path.join(root, n))
    return sorted(files)


def main() -> int:
    research_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "research")
    if not os.path.isdir(research_dir):
        print(f"[ERROR] 目录不存在：{research_dir}", file=sys.stderr)
        print("[FALLBACK] 请手动核对 research/ 路径，或按 insight-and-output.md 手动去重。", file=sys.stderr)
        return 1

    md_files = collect_md_files(research_dir)
    if not md_files:
        print(f"[WARN] {research_dir} 下未找到可处理的 .md 文件。", file=sys.stderr)
        return 0

    # id -> 定义文本（同一 id 多处定义时保留首个非空）
    definitions = {}
    # 正文首次出现顺序（用于分配显示编号）
    first_seen_order = []
    seen_ids = set()

    for path in md_files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = DEF_RE.match(line)
                    if m:
                        cid, text = m.group(1), m.group(2)
                        if cid not in definitions or not definitions[cid]:
                            definitions[cid] = text
                        continue
                    for rm in REF_RE.finditer(line):
                        cid = rm.group(1)
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            first_seen_order.append(cid)
        except OSError as e:
            print(f"[WARN] 跳过无法读取的文件 {path}: {e}", file=sys.stderr)

    if not first_seen_order and not definitions:
        print("[WARN] 未发现任何 [^id] 脚注引用或定义。", file=sys.stderr)
        return 0

    # 把 id 归并到 URL（无 URL 的定义按其文本作为分组键，视为文件来源引用）
    def group_key(cid):
        text = definitions.get(cid, "")
        um = URL_RE.search(text or "")
        if um:
            return um.group(0)
        return f"__nokey__:{(text or cid).strip()}"

    # 按正文首次出现顺序遍历，给每个分组键分配显示编号
    key_to_num = {}
    key_to_ids = {}
    key_to_text = {}
    order_for_numbering = first_seen_order + [c for c in definitions if c not in seen_ids]
    display = 0
    for cid in order_for_numbering:
        k = group_key(cid)
        if k not in key_to_num:
            display += 1
            key_to_num[k] = display
            key_to_text[k] = definitions.get(cid, "(缺定义，需补全)")
            key_to_ids[k] = []
        key_to_ids[k].append(cid)

    # 生成输出
    lines = ["# 合并参考文献（按正文首次出现排序）", ""]
    lines.append(f"共 {len(key_to_num)} 条唯一来源，来自 {len(md_files)} 个文件。\n")
    for k, num in sorted(key_to_num.items(), key=lambda x: x[1]):
        ids = ", ".join(f"[^{i}]" for i in key_to_ids[k])
        text = _sanitize(key_to_text[k])  # 动态内容净化：防止 Markdown 注入
        lines.append(f"[{num}] {text}")
        lines.append(f"    别名: {ids}")
        if text.startswith("(缺定义"):
            lines.append("    [!] 该引用在正文出现但缺少定义，请补全 [^id]: 标题. 日期. URL")
        lines.append("")

    out_text = "\n".join(lines)
    out_path = os.path.join(research_dir, "_references.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out_text)
    except OSError as e:
        print(f"[WARN] 无法写入 {out_path}: {e}", file=sys.stderr)

    print(out_text)
    print(f"\n[OK] 已写入 {out_path}")

    # 缺定义的 id 单独警示
    missing = [c for c in first_seen_order if c not in definitions]
    if missing:
        print(f"[!] {len(missing)} 个引用缺少定义: {', '.join(missing)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
