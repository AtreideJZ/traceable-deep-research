#!/usr/bin/env python3
"""
setup_workspace.py — 创建研究工作区并打印 Epistemic Reset 信息。

用途（确定性工作，交给脚本更稳）：
  1. 在指定工作目录下创建 research/ 子目录（幂等，已存在不报错）；
  2. 打印当前日期时间，提醒主智能体"内部知识可能过期"；
  3. 打印开工前检查清单。

用法：
  python3 setup_workspace.py [workspace_dir]
  workspace_dir 缺省为当前目录。

设计原则：任何异常都不崩溃，以非零退出码 + 明确信息告知，供主智能体降级为手动创建目录。
"""
import os
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # 防止非 UTF-8 控制台 UnicodeEncodeError
    except Exception:
        pass


def main() -> int:
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    research_dir = os.path.join(workspace, "research")

    try:
        os.makedirs(research_dir, exist_ok=True)
    except OSError as e:
        print(f"[ERROR] 无法创建目录 {research_dir}: {e}", file=sys.stderr)
        print("[FALLBACK] 请手动创建 {workspace}/research/ 后继续。", file=sys.stderr)
        return 1

    now = datetime.now()
    print("=" * 56)
    print("Traceable Deep Research · 工作区就绪")
    print("=" * 56)
    print(f"工作区目录 : {os.path.abspath(workspace)}")
    print(f"研究输出目录: {os.path.abspath(research_dir)}")
    print(f"当前日期时间: {now.strftime('%Y-%m-%d %H:%M:%S %A')}")
    print("-" * 56)
    print("Epistemic Reset 提醒：")
    print("  · 假设内部知识可能过期，以上为真实当前时间，以此为准。")
    print("  · 用户若提到时间窗（如'近半年/2026 Q1/最新'），当作硬约束。")
    print("  · 检索语言与用户提问语言保持一致。")
    print("  · 所有产物写入上面的研究输出目录，聊天窗只做状态汇报。")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
