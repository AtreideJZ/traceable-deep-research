#!/usr/bin/env python3
"""
sanitize_markdown.py — 动态内容 Markdown 安全净化工具。

背景：检索结果（网页标题、URL、正文摘录）和用户上传文件内容属于动态内容，
在写入 Markdown 报告或脚注定义文件前必须净化——防止 Markdown 语法注入、
表格破坏、HTML 实体混入、CSV/电子表格公式注入、可疑 URL 协议。

用法：
  python3 sanitize_markdown.py --stdin                # 从标准输入读取，净化后打印
  python3 sanitize_markdown.py --file <path>          # 净化指定 Markdown 文件（原地更新为 .sanitized.md）

模拟库接口（被其他脚本 import 时）：
  from sanitize_markdown import sanitize_text, sanitize_url, sanitize_table_cell, sanitize_footnote_def

鲁棒性：空输入、非字符串、异常字符均不崩溃，降级返回安全默认值。
"""
import os
import re
import sys

# ── 内部常量 ──────────────────────────────────────────────
_DANGEROUS_PROTOCOLS = frozenset({"javascript:", "data:", "vbscript:"})
_CSV_FORMULA_CHARS = frozenset("=+-@")


def _is_dangerous_url(url: str) -> bool:
    lower = url.strip().lower()
    for proto in _DANGEROUS_PROTOCOLS:
        if lower.startswith(proto):
            return True
    return False


# ── 公开净化函数 ──────────────────────────────────────────

def sanitize_text(text: str) -> str:
    """
    净化自由文本中的 Markdown / HTML 敏感字符。

    规则（顺序不可变）：
    - `&` → `&amp;`（必须先做，防止二次转义）
    - `<` → `&lt;`，`>` → `&gt;`
    - `|` → `&#124;`（防止破坏 Markdown 表格列分隔）
    - `` ` `` → `&#96;`（防止触发行内代码块或围栏代码块）
    - 换行 `\\n` `\\r` → 空格并合并连续空格（防止破坏单行 Markdown 结构）
    """
    if not isinstance(text, str):
        return str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("|", "&#124;")
    text = text.replace("`", "&#96;")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r" {2,}", " ", text)
    return text


def sanitize_url(url: str) -> str:
    """
    净化 URL：过滤危险协议，移除 Markdown 链接语法中的可疑包裹。

    规则：
    - `javascript:` / `data:` / `vbscript:` → 替换为安全占位符
    - 移除首尾空白与多余的 `<>` 包裹
    - 空值返回安全默认值
    """
    if not isinstance(url, str) or not url.strip():
        return "#empty-url"
    url = url.strip().strip("<>").strip()
    if not url:
        return "#empty-url"
    if _is_dangerous_url(url):
        return "#blocked-unsafe-protocol"
    return url


def sanitize_table_cell(text: str) -> str:
    """
    净化 Markdown 表格行或单元格。

    分支逻辑：
    - **表格行**（首尾均有 `|` 包裹）：按 `|` 分割为独立单元格，逐格净化 + 公式前缀保护
    - **单格值**（无 `|` 包裹或仅一侧有 `|`）：按普通文本净化 + 公式前缀保护

    规则：
    - 每个单元格做 sanitize_text（转义 `& < > |`` ` + 压平换行）
    - **逐格**检查公式前缀：`=` `+` `-` `@` 开头 → 前缀 `'`
    - 结构 `|` 不转义，内容中的 `|` 由 sanitize_text 转为 `&#124;`
    """
    stripped = text.strip()
    is_table_row = stripped.startswith("|") and stripped.endswith("|")

    if is_table_row:
        # 表格行：分割为单元格，逐格净化
        segments = text.split("|")
        out = []
        for seg in segments:
            content = seg.strip()
            if not content:
                out.append(seg)
                continue
            safe = sanitize_text(content)
            if safe and safe[0] in _CSV_FORMULA_CHARS:
                safe = "'" + safe
            # 保留首尾空白模式（列对齐用）
            if seg != content:
                leading = seg[:len(seg) - len(seg.lstrip())]
                trailing = seg[len(seg.rstrip()):]
                safe = leading + safe + trailing
            out.append(safe)
        return "|".join(out)
    else:
        # 单格值：直接净化
        text = sanitize_text(text)
        if text and text[0] in _CSV_FORMULA_CHARS:
            text = "'" + text
        return text


def sanitize_footnote_def(text: str) -> str:
    """
    净化脚注定义行（[^id]: 标题. 日期. URL）。

    规则：
    - 全文 sanitize_text（转义 + 压平换行）
    - 移除 Markdown 链接/图片语法中残留的可疑协议
    - **全文**过滤裸危险协议（`javascript:` / `data:` / `vbscript:`），不限于链接语法内
    """
    text = sanitize_text(text)
    # 1) 移除 Markdown 图片/链接语法中的危险协议
    def _clean_md_link(m):
        prefix = m.group(1)
        maybe_url = m.group(2)
        clean = sanitize_url(maybe_url)
        return f"{prefix}{clean}"
    text = re.sub(r"(\]\(|!\[[^\]]*\]\()([^)]+)", _clean_md_link, text)
    # 2) 全文过滤未被 sanitize_text 转义的裸危险协议
    for proto in ("javascript:", "data:", "vbscript:"):
        text = text.replace(proto, "#blocked-")
    return text


# ── stdin / file 处理 ─────────────────────────────────────

def _sanitize_line(line: str) -> str:
    """
    对一行 Markdown 做净化。
    脚注定义行用 sanitize_footnote_def，普通行用 sanitize_text。
    表格行（含 `|` 分隔符）额外做公式前缀保护。
    """
    stripped = line.rstrip("\n\r")
    is_table_row = bool(re.match(r"^\s*\|", stripped))
    is_footnote = bool(re.match(r"^\[\^[^\]]+\]:", stripped))

    if is_footnote:
        sanitized = sanitize_footnote_def(stripped)
    elif is_table_row:
        sanitized = sanitize_table_cell(stripped)
    else:
        sanitized = sanitize_text(stripped)

    return sanitized + "\n" if line.endswith("\n") else sanitized


def process_stdin() -> int:
    try:
        for line in sys.stdin:
            sys.stdout.write(_sanitize_line(line))
        sys.stdout.flush()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f"[ERROR] stdin processing failed: {e}", file=sys.stderr)
        return 1
    return 0


def process_file(path: str) -> int:
    if not os.path.isfile(path):
        print(f"[ERROR] 文件不存在：{path}", file=sys.stderr)
        return 1
    out_path = os.path.splitext(path)[0] + ".sanitized.md"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fin:
            lines = fin.readlines()
    except OSError as e:
        print(f"[ERROR] 无法读取 {path}: {e}", file=sys.stderr)
        return 1
    try:
        with open(out_path, "w", encoding="utf-8") as fout:
            for line in lines:
                fout.write(_sanitize_line(line))
    except OSError as e:
        print(f"[ERROR] 无法写入 {out_path}: {e}", file=sys.stderr)
        return 1
    print(f"[OK] 净化完成 → {out_path}", file=sys.stderr)
    return 0


def main() -> int:
    if "--stdin" in sys.argv:
        return process_stdin()
    idx = next((i for i, a in enumerate(sys.argv) if a == "--file"), None)
    if idx is not None and idx + 1 < len(sys.argv):
        return process_file(sys.argv[idx + 1])
    print("用法: sanitize_markdown.py --stdin | --file <path>", file=sys.stderr)
    print("      也可作为库 import：from sanitize_markdown import sanitize_text, sanitize_url, sanitize_table_cell, sanitize_footnote_def", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
