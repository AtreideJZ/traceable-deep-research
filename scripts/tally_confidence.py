#!/usr/bin/env python3
"""
tally_confidence.py — 统计各维度文件的可信度分布，汇总冲突清单。

背景：Phase 3 各维度证据模板含 "Confidence: high/medium/low"；Phase 4 交叉验证文件含
"Conflict Zone" 冲突条目。交付前需要一份客观的可信度画像与冲突清单。手工计数易错漏，
交给脚本更稳。

用法：
  python3 tally_confidence.py [research_dir]
  research_dir 缺省为 ./research。

输出：
  · 终端打印可信度分布表 + 冲突清单；
  · 写入 {research_dir}/_confidence_summary.md。

鲁棒性：目录不存在、无文件、无匹配字段，均提示而不崩溃。
"""
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # 防止非 UTF-8 控制台 UnicodeEncodeError
    except Exception:
        pass

CONF_RE = re.compile(r"Confidence\s*[:：]\s*(high|medium|low)", re.IGNORECASE)
# 冲突区标题行： "## 冲突" / "### 冲突 N" / "Conflict Zone" / "Conflict N"
CONFLICT_RE = re.compile(r"^#{1,6}\s*.*(冲突|conflict)", re.IGNORECASE)


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
        print("[FALLBACK] 请核对 research/ 路径，或按 verification-engine.md 手动统计。", file=sys.stderr)
        return 1

    md_files = collect_md_files(research_dir)
    if not md_files:
        print(f"[WARN] {research_dir} 下未找到可处理的 .md 文件。", file=sys.stderr)
        return 0

    counts = {"high": 0, "medium": 0, "low": 0}
    per_file = {}
    conflicts = []  # (文件名, 行号, 标题文本)

    for path in md_files:
        name = os.path.basename(path)
        local = {"high": 0, "medium": 0, "low": 0}
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for lineno, line in enumerate(f, 1):
                    cm = CONF_RE.search(line)
                    if cm:
                        lvl = cm.group(1).lower()
                        local[lvl] += 1
                        counts[lvl] += 1
                    if CONFLICT_RE.match(line.strip()):
                        conflicts.append((name, lineno, line.strip()))
        except OSError as e:
            print(f"[WARN] 跳过无法读取的文件 {path}: {e}", file=sys.stderr)
            continue
        if any(local.values()):
            per_file[name] = local

    total = sum(counts.values())
    lines = ["# 可信度分布汇总", ""]
    if total == 0:
        lines.append("未在任何文件中发现 `Confidence: high/medium/low` 字段。")
        lines.append("请确认各维度文件采用了标准证据模板。")
    else:
        lines.append(f"证据条目总数（含 Confidence 标注）：{total}\n")
        lines.append("| 级别 | 数量 | 占比 |")
        lines.append("|---|---|---|")
        for lvl in ("high", "medium", "low"):
            pct = f"{counts[lvl] / total * 100:.1f}%" if total else "0%"
            lines.append(f"| {lvl.capitalize()} | {counts[lvl]} | {pct} |")
        lines.append("")
        lines.append("## 各文件分布")
        lines.append("| 文件 | High | Medium | Low |")
        lines.append("|---|---|---|---|")
        for name in sorted(per_file):
            c = per_file[name]
            lines.append(f"| {name} | {c['high']} | {c['medium']} | {c['low']} |")
        lines.append("")

    lines.append("## 冲突清单（Conflict Zone）")
    if conflicts:
        lines.append(f"发现 {len(conflicts)} 处冲突区标记：\n")
        for name, lineno, title in conflicts:
            lines.append(f"- `{name}` 第 {lineno} 行：{title}")
    else:
        lines.append("未发现显式冲突区标记。若研究涉及争议数据，请确认 Phase 4 是否遗漏冲突分析。")
    lines.append("")

    # 低可信占比预警
    if total and counts["low"] / total > 0.4:
        lines.append("> [!] 低可信条目占比超过 40%，建议触发 Phase 5 定向复核后再交付。")

    out_text = "\n".join(lines)
    out_path = os.path.join(research_dir, "_confidence_summary.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out_text)
    except OSError as e:
        print(f"[WARN] 无法写入 {out_path}: {e}", file=sys.stderr)

    print(out_text)
    print(f"\n[OK] 已写入 {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
