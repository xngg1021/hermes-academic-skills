---
name: academic-source-verification
description: "核查文献真实性:交叉核对被引数、撤稿状态、开放获取全文与原文内容。"
version: 1.1.0
author: SJF, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, citations, open-access, crossref, openalex, semantic-scholar, unpaywall, retraction]
    related_skills: [arxiv, ocr-and-documents, grounded-citations, literature-analysis]
---

# 学术来源核查 Skill

验证一篇论文/文献是否真实存在、交叉核对它的元数据与被引数、核查撤稿与更正状态、下载可获得的开放获取全文做内容验证。与 `arxiv` skill 互补：`arxiv` 负责"检索发现论文"，本 skill 负责"核查论文 + 拿全文"。

核心原则：引用一个科研结论前，先证明它真实、未被撤稿、被引数有据、结论原文可查——而不是凭记忆或二手转述。

## When to Use

- 用户要求"下载论文交叉核查""验证这个文献是不是真的""核对被引数"
- 建模/论证里引用了文献，需要坐实它的标题/作者/年份/期刊/被引数
- 需要拿到论文全文（开放获取）并确认下载的是正确的那篇
- 核查一篇文献是否已被撤稿或发过更正（引用的底线检查）
- 查经典专著/公版书的原文（Ebbinghaus 遗忘曲线、Miller 1956 等）

Don't use for: 纯检索发现论文（用 `arxiv` skill）、OCR/解析已下载的 PDF 正文（用 `ocr-and-documents`）。

## Prerequisites

无需任何 API key、无需额外安装（Python stdlib urllib + 已装的 pymupdf）。四个数据库/服务都是免费公开接口：

| 服务 | 用途 | 限制 |
| --- | --- | --- |
| OpenAlex | 元数据最全（含 OA 状态），无速率限制 | 被引数对 arXiv 预印本严重低估 |
| Crossref | 经典被引数口径 + **撤稿/更正记录** | 查不到 data-DOI 形式的 arXiv DOI |
| Semantic Scholar | 第三个独立被引数来源 | 无 key 时 1 req/sec，易 429 |
| Unpaywall | OA 全文定位（is_oa + best_oa_location），120M+ 文章 | 需带 email 参数 |

## 核查四道关

### 第一关：三库交叉核对（真实性 + 被引数）

一次拿三个独立来源，标题/作者/年份/期刊吻合 + 被引数同量级 = 论文确认。

| 库 | 端点 | 关键字段 |
| --- | --- | --- |
| OpenAlex | `https://api.openalex.org/works/https://doi.org/{DOI}` | `cited_by_count`、`publication_year`、`authorships`、`primary_location.source.display_name`、`open_access.oa_status` + `oa_url` |
| Crossref | `https://api.crossref.org/works/{DOI}` | `message.is-referenced-by-count` |
| Semantic Scholar | `https://api.semanticscholar.org/graph/v1/paper/DOI:{DOI}?fields=citationCount,influentialCitationCount,year`（或 `arXiv:{id}`） | `citationCount` |

请求要带 `User-Agent`（带 mailto 更礼貌），否则部分端点会拒。三库被引数必然不同（收录范围不同），只需同量级，不必精确相等。

用 `execute_code` 批量查并打印对照表；每篇论文之间 sleep 0.3~1.1s 防止 Semantic Scholar 429。

### 第二关：撤稿与更正核查（Crossref update 记录）

2026 年的标准做法：Crossref REST API 已并入 Retraction Watch 撤稿数据（2023-09 起共享，6 万+ 条记录），程序化核查走 Crossref，不再依赖已弃用的 Labs 注解接口（2026-05 弃用）。

方法两步：

```python
# 1. 查原始 DOI 的 update-to：指向更正/撤稿/关注通知的 DOI 列表
import json, urllib.request
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "verify/1.0 (mailto:user@example.com)"})
    return json.load(urllib.request.urlopen(req, timeout=15))

m = get(f"https://api.crossref.org/works/{doi}")["message"]
updates = m.get("update-to", [])  # 每个元素有 DOI、type、label
# 2. 逐个查 update 的类型：type 为 "retraction" = 撤稿，"correction" = 更正，"expression-of-concern" = 关注
for u in updates:
    t = u.get("type", "?")
    # type 不是 retraction 时，再查该 update DOI 的 message.type 确认
```

判断规则：`update-to` 非空且存在 type 为 retraction 的记录 = **该文献已被撤稿**，必须停止引用并如实告知用户；correction 或 expression-of-concern = 文献有已知问题，引用时注明。`update-to` 为空 = 无记录（正常文献）。

兜底：Crossref 无记录但存疑时，到 Retraction Watch 数据库网页（retractiondatabase.org）人工核对；arXiv 预印本撤稿看 abs 页的 withdrawal 标记。

### 第三关：OA 全文定位（Unpaywall 首选）

Unpaywall 是 OA 定位的 SOTA 方案（实时爬取 + 出版商元数据，比 OpenAlex 的 oa_status 更准更新）：

```python
r = get(f"https://api.unpaywall.org/v2/{doi}?email=your.email@gmail.com")  # 必须真实域名邮箱，占位域名返回 422
if r.get("is_oa"):
    loc = r["best_oa_location"]  # url_for_pdf / url，版本 published/accepted/submitted
else:
    loc = None  # 无合法 OA 版本
```

顺序：Unpaywall `best_oa_location` → OpenAlex `oa_url` → Semantic Scholar `openAccessPdf.url` → archive.org（公版书/专著）。付费墙 403 不要死磕。

### 第四关：下载与内容核对

- **arXiv（绿 OA）**：`https://arxiv.org/pdf/{id}` —— 永远可下，最稳。
- **公版书/专著（如 Ebbinghaus 1885）**：走 `archive.org` —— 先用 `https://archive.org/advancedsearch.php?q=<标题>&fl[]=identifier,title,year,mediatype&rows=3&output=json` 搜 identifier，再下 `https://archive.org/download/{identifier}/{identifier}.pdf`（整本书扫描，可能几 MB）。

```python
import pymupdf
doc = pymupdf.open(path)
print(" ".join(doc[0].get_text().split())[:400])  # 首页文字，核对标题/作者
print(doc.page_count)
doc.close()
```

下载统一存到稳定目录（`~/papers/` 或工作目录下的 `papers/`，路径保证 UTF-8 可用），回报绝对路径 + 字节数 + 页数。

## Procedure

1. 确定论文的 DOI/arXiv ID/标题。期刊论文用 DOI，arXiv 预印本用 arXiv ID。
2. `execute_code` 批量查 OpenAlex + Crossref（+ Semantic Scholar），打印三库标题/作者/年份/期刊/被引数对照表。
3. 查 Crossref `update-to`：有 retraction → 停止，报告撤稿；有 correction/expression-of-concern → 注明后继续。
4. 判断真实性：至少两个来源元数据吻合、被引数同量级 → 确认。不一致 → 记下差异，如实报告。
5. 能下 OA 就下（Unpaywall/arXiv/archive.org），下完用 pymupdf 提首页文字核对内容。
6. 付费墙 403 的，报告"元数据+被引+撤稿状态已确认，全文在墙后"，不反复尝试。

## Pitfalls

1. **OpenAlex 对 arXiv 论文被引数严重低估**。预印本的 `cited_by_count` 可能只有几十，真实影响是数千（OpenAlex 只统计它收录的引用）。报数时标注"下限"。
2. **Crossref 查不到 arXiv 的 data-DOI** `10.48550/arXiv.<id>`（返回 404）。改用 arXiv ID 或期刊 DOI（已发表时）。
3. **Semantic Scholar 无 key 极易 429**。请求间隔 ≥1.1s，失败退避重试；持续 429 就退回 OpenAlex + Crossref 两个来源，并如实说明。
4. **update-to 非空 ≠ 撤稿**。它可能指向更正或表达关注。必须看 update 的 type 字段再下结论，不能见 update-to 就报撤稿。
5. **出版商 PDF 付费墙，脚本下载 403**。OpenAlex 的 `oa_status: "bronze"` 只表示"在出版商网站免费可读"，不代表能脚本下载（Wiley 的 pdfdirect 就是 403）。403 后报告墙内，不循环重试。
6. **下载成功 ≠ 内容正确**。必须提取 PDF 首页文字核对标题/作者，防止下到同名错误文件。
7. **Unpaywall 的 email 参数有硬校验**。缺 email 或用占位域名（example.com 无 MX 记录）都返回 422，必须填真实域名邮箱。`is_oa=false` 时 `best_oa_location` 为 null，先判再取。

输出语言：默认跟随用户输入语言（用户用什么语言问就用什么语言答）；论文标题与引文保留原文，译名首次出现时附原文。

## Verification

```python
import json, urllib.request
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "verify/1.0 (mailto:user@example.com)"})
    return json.load(urllib.request.urlopen(req, timeout=15))

# 用一个真实 DOI 全链路自检（OpenAlex + Crossref + Unpaywall 三端点）
doi = "10.1038/nature14539"
oa = get(f"https://api.openalex.org/works/https://doi.org/{doi}")
assert oa.get("title"), "OpenAlex 无返回"
cr = get(f"https://api.crossref.org/works/{doi}")
assert cr["message"].get("title"), "Crossref 无返回"
up = get(f"https://api.unpaywall.org/v2/{doi}?email=test@gmail.com")
assert "is_oa" in up, "Unpaywall 无返回"
print("academic-source-verification 三端点自检通过")
```

（Semantic Scholar 不放进自检：无 key 时 429 频发，实际核查时按需启用。）
