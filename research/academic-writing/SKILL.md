---
name: academic-writing
description: "学术写作:润色编辑、引用规范生成、期刊投稿格式检索、AI 生成成分检测。"
version: 1.1.0
author: SJF, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [writing, citation, journal-submission, ai-detection, editing]
    related_skills: [literature-analysis, academic-source-verification, docx, pdf, ocr-and-documents]
---

# 学术写作 Skill

四个工作流：论文辅助编辑（本地文件与编辑平台）、引用规范生成（多风格批量排版）、期刊投稿格式检索（最新投稿须知）、AI 生成成分检测（渠道聚合）。与 `literature-analysis` 分工：那个管"读论文"，本技能管"写论文与投稿"。

核心原则：编辑不改作者原意与数据；引用条目不编造字段；AI 检测结果只作概率参考不作事实判定；期刊指南注明检索日期。输出语言默认跟随用户输入语言；引文与论文原文保留原文不翻译。

## When to Use

- 用户要求润色、修改、审查本地论文（docx/pdf/md/tex）
- 用户在 Overleaf/Word 在线等平台编辑，需要辅助编辑建议
- 用户要求"按 APA/MLA/Chicago/IEEE/GB-T 格式排参考文献"
- 用户要投稿某期刊，需要最新的投稿格式与引用规范
- 用户要求检测论文的 AI 生成成分比例
- 用户要求写投稿信、审稿回复信（rebuttal）或预印本提交材料
- 用户需要学位论文盲审格式核查、开题报告框架、中文期刊投稿或 CCF 目录查询

## 工作流 A：论文辅助编辑

输入：本地文件（`read_file` 直接读 docx/pdf/md；tex 按文本读）、平台文本（用户粘贴）、或浏览器里的在线编辑器。

三层编辑，逐层执行并分开报告：

1. **语言层**：语法错误、时态一致性（方法用过去时、结论用现在时）、术语全文统一、拼写。逐条给"原文 → 修改后 → 理由"。
2. **结构层**：IMRaD 结构核对（摘要是否含目的/方法/结果/结论四要素）、段落过渡、标题层级、图表编号与正文引用对应。
3. **论证层**：每个 claim 是否有对应证据句；结论是否超出实验范围；"显著/证明/首次"等强措辞是否过火。

编辑规则（硬约束）：不改变作者原意，不增删数据，不确定的修改标"建议"而不是直接改；所有修改集中成 diff 式清单供用户逐条确认；docx 的实际写入用 `docx` 技能（python-docx）执行，改前先备份。

## 工作流 B：引用规范生成

用户选择风格后，按 `references/citation-styles.md` 的规则生成文中引用与文末参考文献条目。现行版本（2026 核查）：APA 7th（2020）、MLA 9th（2021）、Chicago 18th（2024 年发布，注意部分机构仍指定 17th，先确认再排）、IEEE（持续更新）、AMA 11th（2020）、GB/T 7714-2015（中文期刊通行）。

执行方式：

1. 让用户确认风格与目标刊物（中文期刊默认 GB/T 7714-2015）。
2. 逐条解析文献信息（作者、年份、标题、期刊/出版社、卷期页、DOI），缺字段标"【待补】"，禁止编造。
3. 按风格规则输出格式化条目 + 文中引用样例（正文内 (Author, Year) 或 [1] 式）。
4. 批量转换时输出对照表（原始信息 → 格式化条目），便于核对。

## 工作流 C：期刊投稿格式检索

用户给出期刊名 → 检索该刊最新投稿指南：

1. `web_search` 用"<期刊名> Instructions for Authors"（中文期刊用"<期刊名> 投稿须知 投稿指南"）找官网页面，优先期刊官网域名。
2. `web_extract` 抓取指南页，提取：字数/页数限制、摘要结构要求、正文结构、参考文献风格、图表规范（分辨率、格式）、投稿系统入口、审稿周期说明。
3. 输出"投稿清单"（逐项要求 + 来源链接 + 检索日期）。指南页若为动态渲染抓不到，用 `browser_exec` 兜底，或如实说明只能拿到部分信息。

注意：投稿指南频繁改版，输出必须注明检索日期，并建议用户投稿前对照官网最终确认。

## 工作流 D：AI 生成成分检测（渠道聚合）

诚实前置（必须向用户说明）：所有 AI 检测器的独立测试假阳性率在 2%~7%，对学术文本尤其不稳，检测分数只能作为概率参考信号，不能作为"这篇是 AI 写的"的事实依据，更不建议用于指控他人。

渠道分层（2026 核查）：

白嫖层（免费注册，额度有限）：
- GPTZero：免费层 1 万词/月（注册即可，无信用卡），API 需 Professional 计划（约 $24.99/月）
- Copyleaks：免费额度（注册），API 最低 $7.99/月起，多语言支持最好，1 credit = 250 词
- TextSight：无需注册每天 3 次网页检测（无 API，只能手动）

付费层（自备 key 自动聚合）：GPTZero API、Copyleaks API、Originality.ai（Pay-as-you-go $30 起，独立测试假阳性 2%~5.7%）。

无 key 状态：本技能只给渠道指引与操作步骤，不假装能自动检测；用户接入 key（写进环境变量）后，检测流程：按 500~1500 词切段分别送检，报告分段得分、整体分布、以及"结果仅供概率参考"的固定声明。

本地无可靠开源检测器，不提供本地检测方案，避免误导。

## 工作流 E：投稿材料（投稿信 / 审稿回复信 / 预印本）

投稿信半页结构、rebuttal 三要素回应法、修改对照表三列格式、arXiv 提交材料清单。模板与语气规则见 `references/submission-letters.md`。不代用户注册账号或代提交，只生成材料与步骤。

## 工作流 F：中文学术场景

学位论文盲审格式核查（以学校模板为最高优先级）、开题报告八段框架、中文期刊投稿规范、CCF 推荐目录查询（带年份与版本说明）。见 `references/china-academia.md`。

## Procedure

1. 识别任务类型（编辑/引用/投稿指南/AI 检测）。
2. 编辑任务：先读原文，按语言、结构、论证三层出报告，改动集中列清单。
3. 引用任务：确认风格 → 解析条目 → 按 `references/citation-styles.md` 排版 → 输出对照表。
4. 投稿任务：检索 → 提取 → 输出带日期和链接的清单。
5. AI 检测：先声明局限，无 key 给渠道指引，有 key 执行分段检测。

## Pitfalls

1. **AI 检测结果不能当事实**。假阳性 2%~7% 意味着 100 篇里可能有 2~7 篇被冤枉；报告分数时必须附此声明，禁止输出"确认是 AI 写的"这类定性结论。
2. **引用条目禁止编造字段**。卷、期、页码、DOI 缺失就标【待补】，宁可让用户补，也不生成看似合理的假字段。
3. **Chicago 18 与 17 并存**。2026 年 CMOS 18 已出版但大量机构仍在用 17th，排版前必须确认目标要求，两个版本页码引用规则有差异。
4. **期刊指南时效**。Instructions for Authors 随时改版，输出必须带检索日期与来源链接。
5. **编辑不改原意**。学术论文润色最大的风险是"顺手改了结论表述"；任何影响语义的修改都要单独标出请用户确认。
6. **中文期刊引用风格**。中文期刊普遍要求 GB/T 7714-2015，别默认给 APA；作者名、期刊名的中英双语著录规则见 `references/citation-styles.md`。
7. **GBK 陷阱**。处理中文 docx/tex 时若脚本报编码错误，先确认文件以 UTF-8 读写；Windows 下默认 GBK 会破坏中文内容（参见 hermes-agent 技能 windows-quirks）。

## Verification

```python
import os
base = os.path.dirname(__file__)
ref = os.path.join(base, "references", "citation-styles.md")
text = open(ref, encoding="utf-8").read()
for style in ("APA", "MLA", "Chicago", "IEEE", "GB/T 7714"):
    assert style in text, f"引用风格 {style} 缺失"
for ref in ("submission-letters.md", "china-academia.md"):
    assert os.path.exists(os.path.join(base, "references", ref)), f"{ref} 缺失"
print("academic-writing 引用风格表与投稿材料自检通过")
```

（AI 检测渠道依赖外部服务与用户自备 key，不进自检；期刊指南检索依赖 web_search，按需验证。）
