# 配置规范

## 目录

1. 配置原则
2. Profile 示例
3. 单行业与多行业
4. 数据源配置
5. 查询预算与可比性
6. 凭据安全

## 1. 配置原则

为每个监测项目建立一个 YAML Profile。配置只描述监测逻辑，不保存 API Key、Webhook 或其他凭据。

最小配置：

```yaml
profile:
  name: "AI 记忆媒体情报"
  mode: "industry"
  report_language: "zh-CN"
  ui_language: "zh-CN"
  timezone: "America/Los_Angeles"
  geography: ["US"]
  source_languages: ["en"]
  lookback_days: 7
```

`ui_language` 默认固定为 `zh-CN`。只有用户明确提出才增加语言切换。

地区和时间默认口径：

```yaml
scope:
  geography_semantics: "market_relevance"
  include_current_day: true
  window_type: "calendar_days"
  run_type: "snapshot"
```

- `market_relevance`：收录与目标市场直接相关的报道，不限制媒体注册地；
- `publisher_origin`：只按媒体所在地筛选，仅在用户明确要求时使用；
- `snapshot`：一次性回溯；
- `recurring`：持续更新，另行配置定时机制。

## 2. Profile 示例

```yaml
profile:
  name: "AI Memory 美国媒体情报"
  mode: "portfolio"
  report_language: "zh-CN"
  ui_language: "zh-CN"
  timezone: "America/Los_Angeles"
  geography: ["US"]
  source_languages: ["en"]
  lookback_days: 7

industries:
  - id: "ai-memory"
    name: "AI Memory"
    core_terms:
      - "AI memory"
      - "memory layer"
      - "memory operating system"
      - "persistent memory for AI agents"
    adjacent_terms:
      - "agentic AI"
      - "context engineering"
      - "long-term memory"
    exclude_terms:
      - "human memory disorder"

  - id: "agentic-ai"
    name: "Agentic AI"
    core_terms:
      - "AI agent"
      - "agentic AI"
      - "autonomous agent"
    adjacent_terms:
      - "agent orchestration"
      - "tool use"

entities:
  clients:
    - name: "EverMind"
      aliases: ["EverMind AI"]
      products: ["AI Memory Operating System", "Memory Layer"]
      industry_ids: ["ai-memory", "agentic-ai"]

  competitors:
    - name: "Mem0"
      aliases: ["mem0.ai"]
      industry_ids: ["ai-memory"]
    - name: "Zeta"
      aliases: []
      disambiguation_required: true
      industry_ids: ["ai-memory"]

monitoring:
  include:
    - "industry_news"
    - "client_competitor"
    - "native_coverage"
    - "review"
    - "executive_interview"
    - "journalist_trend"
    - "risk"
    - "pitch_opportunity"
  optional:
    - "deals_affiliate"

# 用户固定规则（默认开启，仅用户当场明确要求时可临时放宽）：
source_policy:
  allowed_publishers: "foreign_media_or_top_cn_overseas_edition"
  exclude_press_releases_from_output: true
  region_tag_required: true
  max_events_per_industry: 3
  pr_actions_brief: true

output:
  format: ["dashboard", "markdown"]
  sections:
    - "executive_summary"
    - "industry_landscape"
    - "client_competitor_watch"
    - "media_opportunities"
    - "risk_watch"
    - "recommended_actions"
  show_original_title: true
  bilingual_interface: false
```

对名称有歧义的公司设置 `disambiguation_required: true`，先确认公司官网、产品或行业，不要静默猜测。

## 3. 单行业与多行业

### 单行业

使用 `mode: industry`，围绕一个行业建立公司、媒体、记者与议题图谱。

### 多行业

使用 `mode: portfolio`，每个行业保留独立：

- 关键词与排除词；
- 媒体注册表和 Tier；
- 风险规则；
- 查询预算；
- 结果数量；
- 趋势结论。

跨行业汇总只比较标准化指标（仅原生报道口径，通稿与转载不参与比较）：

```text
独立事件数
第三方原生报道数
行业 Tier 1 原生报道数
风险事件数
Pitch 机会数
归一化优先级
```

不要直接用总网页数比较不同行业热度。

跨行业公司使用事件级标签：

```yaml
event_tagging:
  primary_industry_required: true
  secondary_industries_allowed: true
  company_level_exclusive_assignment: false
```

例如 Microsoft 的 Agent 产品事件可归入 AI Agent；Azure GPU 集群事件可归入 AI Infrastructure。不要因为公司同时存在两类业务而重复计算同一事件。

## 4. 数据源配置

```yaml
sources:
  primary: "codex_web"
  providers:
    codex_web:
      enabled: true
    google_cse:
      enabled: false
      api_key_env: "GOOGLE_CSE_API_KEY"
      engine_id_env: "GOOGLE_CSE_ID"
      country: "us"
      language: "lang_en"
      safe: "active"
      max_results_per_query: 10
    rss:
      enabled: true
      feeds: []
    gdelt:
      enabled: false
    newsroom:
      enabled: true
      urls: []
    regulatory:
      enabled: true
      urls: []
```

Google CSE 仅适用于已有 Custom Search JSON API 权限的用户。Google 已停止接受新客户，现有客户需在 2027-01-01 前迁移，详见 [Google 官方说明](https://developers.google.com/custom-search/v1/overview)。Provider 必须可替换，不得将分类、聚类和报告逻辑写死到 Google 返回格式。请求参数以 [cse.list 官方文档](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list) 为准。

使用脚本：

```bash
export GOOGLE_CSE_API_KEY="..."
export GOOGLE_CSE_ID="..."
python3 scripts/google_search.py \
  --query '"AI memory" OR "memory layer"' \
  --date-restrict w1 \
  --gl us \
  --lr lang_en
```

脚本输出统一 JSON，供后续标准化处理。不要把 Shell 历史、环境变量或完整请求 URL 写入报告。

## 5. 查询预算与可比性

为多行业项目设置相同或明确披露的预算：

```yaml
collection:
  queries_per_industry: 12
  results_per_query: 10
  max_pages_per_domain: 5
  deduplicate_urls: true
  cluster_events: true
```

其中 `12` 只是起始示例，不是强制标准。按项目复杂度调整，但多行业横向比较时尽量保持一致。

若某行业使用了更多查询或更多定向媒体源，必须在报告口径中披露。趋势比较优先使用比例：

```text
原生报道占比
行业 Tier 1 占比
通稿转原生报道率
风险事件占比
媒体集中度
```

## 6. 凭据安全

- 只通过环境变量读取 API Key。
- 不把 `.env`、Webhook、客户私有词表或内部媒体 Tier 上传到公开仓库。
- 不在错误信息中回显完整请求 URL。
- 不在生成的 HTML、Markdown 或浏览器端 JavaScript 中嵌入密钥。
- 浏览器 Dashboard 只读取已经生成的结果数据，不直接调用带密钥的搜索 API。
