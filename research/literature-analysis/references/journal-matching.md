# 期刊匹配推荐（Journal Matching）

对应工作流 H。投稿前用主题标签反查发表过同类论文的期刊，输出候选期刊清单。

## 方法

1. 拿目标论文的主题标签：`GET https://api.openalex.org/works/<WID>?select=concepts,topics`，取 score ≥ 0.4 的 concepts 与全部 topics。
2. 对每个主题反查高发刊源：
   `GET https://api.openalex.org/sources?search=<主题词>&sort=works_count:desc&per-page=5`
   返回期刊/会议（`display_name`、`works_count`、`cited_by_count`、`type`）。
3. 汇总打分：论文每个 concept 命中的期刊 +1 分（topic 命中 +2），按总分排序取前 10。
4. 过滤：去掉 predatory 特征明显的（无 ISSN、works_count 过小、出版社不在主流列表），标注 OA 状态。

## 输出格式

| 候选期刊 | 命中主题 | 该刊相关论文量 | 类型/出版社 | 备注 |

每刊附一行推荐理由（哪些主题重叠 + 该刊发表过的最接近论文示例 1~2 篇）。

## 诚实边界

- 中科院分区、JCR 影响因子、预警名单不在 OpenAlex 数据内，输出时明确"分区与影响因子需另行核对（web_search 或用户自己查）"，不编造。
- 期刊匹配是主题邻近度推荐，不替代"读目标期刊最近几期判断口味"这一步。
- 会议场景同理：sources 里 `type=conference` 的条目即会议，可按同样方法匹配。
