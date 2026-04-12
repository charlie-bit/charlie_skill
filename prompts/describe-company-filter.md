# 公司筛选需求引导

帮助你清晰描述公司筛选条件，充分利用 company-filter skill 的能力。

## 第一步：核心条件（至少填一项）

### 1. 目标行业是什么？
> 可以是大类或细分。多个行业用逗号分隔。
>
> 常见选项：SaaS, FinTech, HealthTech, AI/ML, E-commerce, Cybersecurity,
> EdTech, PropTech, CleanTech, DevTools, Blockchain/Web3, IoT, Logistics,
> HR Tech, MarTech, InsurTech, LegalTech, FoodTech, BioTech, Gaming

### 2. 目标地区在哪里？
> 精确到国家、州/省、或城市均可。
>
> 示例：US / US, California / San Francisco, CA / Europe / Southeast Asia

### 3. 公司规模多大？
> 按员工数选择：
> - 1-10（初创团队）
> - 11-50（小型）
> - 51-200（中小型）
> - 201-1000（中型）
> - 1000+（大型）
> - 不限

---

## 第二步：可选条件（按需勾选，缩小范围）

以下条件不是必须的，但每多填一项，结果就更精准。

### 4. 有营收要求吗？
> - 不限
> - <$1M
> - $1M - $10M
> - $10M - $50M
> - $50M+

### 5. 融资阶段有偏好吗？
> - 不限
> - Bootstrapped（自筹）
> - Seed（种子轮）
> - Series A
> - Series B
> - Series C+
> - 已上市 (IPO)
>
> 追问：对融资金额有要求吗？如"最近一轮 >$5M"

### 6. 成立时间有要求吗？
> 如：2020 年之后成立、成立超过 5 年

### 7. 对技术栈有要求吗？
> 如：使用 AWS、Kubernetes、React、Snowflake、Salesforce
>
> 提示：这个条件适合找"正在用某技术"或"可能需要你产品"的公司

### 8. 商业模式偏好？
> - 不限
> - B2B
> - B2C
> - B2B2C
> - Marketplace
> - Platform

### 9. 要找有增长信号的公司吗？
> 如：近 3 个月大量招聘、最近有融资新闻、刚发布新产品
>
> 提示：增长中的公司更可能有采购预算

### 10. 需要定位到关键决策人吗？
> 如：有 CTO、VP Engineering、Head of Sales、CFO
>
> 提示：提前知道决策人角色有助于 outreach

### 11. 对公司状态有要求吗？
> - 活跃运营中
> - 已上市
> - 近期被收购
> - 不限

---

## 第三步：高管名单（可选）

### 12. 是否需要附带高管名单？
> 查询结果会同时关联本地高管数据集，不额外消耗大量 token

### 13. 需要哪些层级？
> - C 层（CEO, CTO, CFO, COO, CMO, CPO, CRO, Founder）
> - VP 层（VP Sales, VP Engineering, VP Marketing, VP Product）
> - D 层（Director of Sales, Head of Eng 等）
> - 全部

### 14. 有职能方向偏好吗？
> 如：只要 Sales 相关（CEO + CRO + VP Sales）
> 或：只要技术决策人（CTO + VP Eng）

---

## 第四步：输出偏好

### 15. 期望的输出格式？
> - Markdown 表格（直接展示）
> - CSV 文件（导入 CRM）
> - 两者都要

### 16. 最多需要多少家公司？
> 如：Top 20、50 家、不限

### 17. 输出需要包含哪些字段？
> 默认字段：公司名、行业、地区、员工数、融资阶段、简介、数据来源
>
> 可选追加：官网、创始人、最近新闻、招聘岗位数、竞争对手

---

## 输出模板

将你的回答整理成以下格式，交给 company-filter skill 执行：

```
## 公司筛选需求

**核心条件**
- 行业: {行业}
- 地区: {地区}
- 规模: {员工数范围}

**可选条件**
- 营收: {营收范围 / 不限}
- 融资: {阶段 / 不限}
- 成立时间: {时间要求 / 不限}
- 技术栈: {技术要求 / 不限}
- 商业模式: {模式 / 不限}
- 增长信号: {信号 / 不限}
- 公司状态: {状态 / 不限}

**高管需求**
- 是否附带高管: {是 / 否}
- 高管层级: {C / VP / D / 全部}
- 职能方向: {Sales / Eng / 全部}

**输出要求**
- 格式: {Markdown / CSV / 两者}
- 数量: {Top N}
- 额外字段: {追加字段 / 默认即可}
```

---

## 快速示例

如果你赶时间，一句话也行：

> "帮我找美国加州做 AI/ML 的 B2B 公司，50-500 人，拿过 Series A 以上"

Skill 会自动解析条件并执行搜索。但填写越详细，结果越精准。
