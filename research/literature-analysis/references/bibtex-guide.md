# BibTeX 生成指南（BibTeX Export）

对应工作流 I。从 OpenAlex/Crossref 元数据生成 BibTeX 条目，与 Zotero、Overleaf 互通。

## 条目类型对照

| 文献类型 | BibTeX 类型 | 必填字段 |
| --- | --- | --- |
| 期刊论文 | @article | author, title, journal, year, volume, number, pages, doi |
| 会议论文 | @inproceedings | author, title, booktitle, year, pages, doi |
| 书籍 | @book | author/editor, title, publisher, year |
| 学位论文 | @phdthesis / @mastersthesis | author, title, school, year |
| 预印本 | @misc | author, title, year, eprint(arXiv ID), archivePrefix="arXiv" |
| 网页 | @misc | author, title, year, howpublished="\\url{...}", note=访问日期 |

## 生成规则

- 作者字段：`and` 连接；"姓, 名"形式（BibTeX 对姓前名后最稳）；中文作者写全名。
- 标题：保持原文大小写，易被 LaTeX 转小写的词（如 IEEE、GPT、RAG）用花括号包裹：`title = {A Survey on {RAG}}`。
- DOI：有 DOI 就写 `doi` 字段，不带 URL 前缀。
- key 命名：`第一作者姓+年份+标题首词`，如 `vaswani2017attention`，同一 bib 内不重复。
- 从 OpenAlex 自动生成的脚本骨架：

```python
w = get(f"https://api.openalex.org/works/{wid}")  # get 见主 SKILL.md

def bibtex_name(display_name):
    # "Yann LeCun" -> "LeCun, Yann"; "Geoffrey E. Hinton" -> "Hinton, Geoffrey E."
    parts = display_name.rsplit(" ", 1)   # 最后一词为姓（西文习惯）
    return f"{parts[-1]}, {parts[0]}" if len(parts) == 2 else display_name

authors = " and ".join(bibtex_name(a["author"]["display_name"]) for a in w.get("authorships", []))
year = w.get("publication_year", "n.d.")
title = w.get("title", "").replace("{", "\\{")
doi = (w.get("doi") or "").replace("https://doi.org/", "")
print(f"@article{{key{year},\n  author = {{{authors}}},\n  title = {{{title}}},\n  journal = {{{w.get('primary_location', {}).get('source', {}).get('display_name', '')}}},\n  year = {{{year}}},\n  doi = {{{doi}}}\n}}")
```

姓前名后转换陷阱：不能用 `replace(" ", ", ", 1)`——它把第一个空格当分隔，会输出 "Yann, LeCun"（名当姓）。必须 `rsplit(" ", 1)` 取最后一词为姓。

## 中文文献

中文文献推荐用 biblatex 的 gb7714-2015 样式包（`biblatex-gb7714-2015`，对应 GB/T 7714-2015），普通 BibTeX 对中文排序与"等/et al."处理不佳。中文期刊文章条目字段与英文相同，author 写中文全名。

## 验证

生成的 .bib 文件必须过一遍 `biber --tool` 或 Overleaf 编译检查；批量生成时抽查 3 条与原始元数据逐字段对照。
