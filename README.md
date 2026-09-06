# hermes-academic-skills

Four academic skills for the Hermes Agent, built and battle-tested on a real research workflow. All data sources are free-tier (OpenAlex, Crossref, Unpaywall, arXiv, Europe PMC, PubMed, DOAJ) and every recipe was verified against live APIs or real numerical results.

Author: Junfu Shi (SJF, xngg1021), Hermes Agent. License: MIT.

## Skills

| Skill | Version | What it does |
| --- | --- | --- |
| `research/academic-source-verification` | 1.1.0 | Verify a paper is real: three-database cross-check (OpenAlex / Crossref / Semantic Scholar), retraction & correction check via Crossref (Retraction Watch data), OA full-text location (Unpaywall), PDF content verification |
| `research/literature-analysis` | 1.1.0 | 12 workflows around a paper: similarity search, local sentence-level plagiarism check, counter-evidence mining, author profile, mock peer review, fallacy annotation (30 types), review matrix, journal matching, BibTeX export, bilingual reading, research-gap analysis, reproduction helper |
| `research/academic-writing` | 1.1.0 | Writing & submission: 3-layer editing, 6 citation styles (APA 7 / MLA 9 / Chicago 18 / IEEE / AMA 11 / GB/T 7714-2015), journal instruction retrieval, AI-content detection channels, submission letters, China academia scenarios |
| `research/math-computation` | 1.2.0 | Cross-domain computation hub with 2-layer routing: domain detection (finance / social science / biomedicine / physics-engineering / pure math) then task-to-tool mapping. 16 libraries, 7 reference files, all recipes numerically verified |

## Data-source tiers

- Free (works out of the box): OpenAlex, Crossref, Unpaywall, arXiv, Europe PMC, PubMed E-utilities, DOAJ
- Freemium (free registration): Semantic Scholar (rate-limit lift + citation contexts), Scite free tier, Dimensions free, CiNii appid
- Paid (bring your own key): Scopus, Web of Science, Dimensions API, Scite Pro; AI detection: GPTZero / Copyleaks / Originality.ai

## Notes

- Current version is written in Chinese (author's working language). An English release edition is in preparation before upstream PRs.
- No API keys or personal paths are hardcoded; placeholder emails are intentional and must be replaced per Unpaywall's validation.
- Verified on: Windows 11 (Chinese locale), Hermes Agent v2026.8.31, Python 3.11 venv with sympy 1.14 / numpy 2.4 / scipy 1.17 / pandas 2.3 / statsmodels 0.14 / lifelines 0.30 / arch 8.0 / pingouin 0.6.
