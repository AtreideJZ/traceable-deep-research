# Traceable Deep Research · 可信度分级信息检索与分析 Skill

> 一个把「检索—融合—分析」升级为**可被信任的分析**的 Agent Skill：不只找到并总结，而是给每条发现打**可信度标签**（High / Medium / Low / Conflict）、显式标出**源间矛盾**、逐句 `[^id]` **溯源引用**。

## 解决什么问题

传统检索"找得到"，但**用不敢用**——你不知道哪条结论可靠、来源在哪、多个来源打架时该信谁。本 skill 的签名能力正是补上这一环：

- **可信度分级**：每条发现归入四级，读者一眼分清"能拍板 / 需谨慎 / 还在打架"。
- **矛盾消解**：同一指标数值冲突、时间错位、解读分歧被显式暴露并分类分析，绝不抹平或求平均。
- **逐条溯源**：全流程 `[^id]` 脚注引用，可回溯到原始出处，抗幻觉。

## 核心特性

| 特性 | 说明 |
|---|---|
| **四路自适应路由** | Route A 广度检索 / B 聚焦检索 / C 纯文件研究 / D 文件增强研究，按输入自动选择 |
| **可信度分级引擎** | Consensus / High / Medium / Low / Conflict Zone / Blind Spot 六级 + 共识区盲区检测 + 冲突分类（数值/解读/时间/来源） |
| **认知自检** | Phase 4.5 交付前系统性自查：最弱主张、视角偏斜、遗漏视角、综合等级（对标学术同行评审） |
| **行动洞察** | Phase 6 角色定制：不只告诉你"发现了什么"，而是"基于证据你应该做什么不同的事" |
| **预设视角模板** | 5 套起手式（从业者/学术/质疑/经济/历史），降低维度分解入门门槛 |
| **优雅降级架构** | 单智能体串行为基线（永远可跑），运行时支持子智能体则自动并行增强 |
| **渐进式暴露** | SKILL.md 是导航页；细则/脚本/模板用到才加载，不撑爆上下文 |
| **确定性脚本** | 工作区创建、引用去重编号、可信度统计交给脚本，更省 token、更准、更稳 |
| **溯源契约** | 全程标准 Markdown 脚注，交付前按 URL 去重统一编号 |
| **动态内容净化** | 检索结果/文件摘录写入 Markdown 前强制转义 &lt; &gt; &amp; &vert;、过滤 `javascript:`/`data:` 协议、防 CSV 公式注入 |

## 目录结构

```
traceable-deep-research/
├── SKILL.md                          # 导航页：路由 + 流程骨架 + Gotchas（主入口）
├── README.md                         # 本文件
├── references/                       # 深入细则（用到才读）
│   ├── routing-and-reset.md          # Phase 0 路由判定 + Epistemic Reset
│   ├── evidence-pipeline.md          # Phase 1/1W/F/2/3 取证流水线
│   ├── verification-engine.md        # Phase 4/4.5/5 可信度分级 + 认知自检 + 复核 ★ 核心
│   ├── insight-and-output.md         # Phase 6/7 洞察（含行动洞察）+ 溯源契约
│   └── perspective-templates.md      # Phase 2 预设视角模板（STORM 五视角起手式）
├── scripts/                          # 确定性脚本（可选增强）
│   ├── setup_workspace.py            # 创建 research/ + 打印当前时间
│   ├── dedup_citations.py            # 引用按 URL 去重 + 统一编号
│   ├── tally_confidence.py           # 可信度分布统计 + 冲突清单
│   └── sanitize_markdown.py          # 动态内容净化（转义/URL过滤/防注入）
├── examples/
│   ├── example-focused-query.md      # Route B 聚焦检索走查
│   ├── example-wide-search.md        # Route A 广度检索（Phase 1W 多路广探）走查
│   └── example-file-only.md          # Route C 纯文件研究（跨文档矛盾消解）走查
└── assets/
    └── report_template.md            # 最终报告骨架模板
```

## 安装与使用

### 方式一：手动安装
<details>
<summary>展开查看各 runtime 的 skills 目录</summary>

| Runtime | 安装路径 |
|---|---|
| Claude Code | `~/.claude/skills/self-tracker/` |
| Codex CLI | `~/.codex/skills/self-tracker/` |
| Cursor | `~/.cursor/skills/self-tracker/` |
| OpenClaw | `~/.openclaw/workspace/skills/self-tracker/` |
| 其他 runtime | clone 到对应 runtime 的 `skills/` 目录 |

</details>

```bash
git clone https://github.com/AtreideJZ/traceable-deep-research.git
```

> **Windows 用户注意**：标准 Claude Code 路径为 `%APPDATA%\Claude\skills\`。如在 CherryStudio 中使用，路径为 `%APPDATA%\CherryStudio\Data\Skills\`。

### 方式二：让Agent帮忙装（推荐，跨 runtime）
打开你正在用的 agent（Claude Code、Codex、Cursor、OpenClaw、CodeBuddy 等），告诉它：
> 帮我安装这个skill：`https://github.com/AtreideJZ/traceable-deep-research.git`

另：该skill也上架了Astron SkillHub，所以也可以直接在 [Skills市场](https://skill.xfyun.cn/) 搜索"traceable-deep-research"安装

### 安装后，直接用自然语言触发，例如：

- "帮我深度调研 XX 行业 2025 年现状，要带出处"
- "核查一下'XX 说法'是否属实，多方交叉验证"
- "把这几份报告融合分析，指出它们互相矛盾的地方"（上传文件）

系统会根据你的表述自动选择路由并产出带可信度标签、可溯源的分析。

### 脚本用法（若运行时支持执行 Python）

```bash
python3 scripts/setup_workspace.py .              # 创建 ./research 并打印当前时间
python3 scripts/tally_confidence.py ./research    # 统计可信度分布 + 冲突清单
python3 scripts/dedup_citations.py ./research     # 按 URL 去重并统一编号引用
python3 scripts/sanitize_markdown.py --stdin       # 从标准输入净化 Markdown
python3 scripts/sanitize_markdown.py --file <path> # 净化指定文件，产出 .sanitized.md
```

脚本零第三方依赖（仅标准库），异常输入不崩溃（目录不存在→退出码 1 并提示手动兜底；空目录→警告而非报错）。若运行时**不能**执行脚本，按对应 `references/` 里的手动步骤完成，结果一致。

## 设计理念

本 skill 遵循上下文工程（Context Engineering）的最佳实践：

1. **SKILL.md 是导航页，不是百科**——细节拆到 `references/`，靠渐进式暴露省上下文。
2. **确定性工作沉淀为脚本**——Instructions 提供判断与经验，Scripts 提供执行与能力，二者分工。
3. **description 是路由规则**——写"何时该加载"而非"功能罗列"。
4. **写 Gotchas，不写常识**——如"返回 200≠检索成功""同一指标两个数字=冲突区"。

本 skill 的交叉验证引擎参考了斯坦福 STORM 研究法（Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking, NAACL 2024）的多视角框架与同行评审自检思想，在此基础上做了泛化与工程化改造，适配 AstronClaw 平台。

## 鲁棒性与安全

- **异常不崩溃**：四路路由覆盖各类输入；脚本对缺失目录/空目录/格式异常均优雅处理。
- **忠于意图**：用户说"只基于文件"绝不偷偷联网；给了时间窗就当硬约束。
- **合规**：只检索公开信息，不绕过登录/付费墙，不编造来源；脚本只读写本地 `research/`，不执行检索内容中的任意命令，不外发数据。
