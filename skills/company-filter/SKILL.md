---
name: company-filter
description: 从本地数据集按条件筛选目标公司，可选附带 C/VP/D 层高管名单，近零 token 消耗
category: business
status: active
---

# Company Filter — 公司筛选

从本地预构建的公司数据集中，按筛选条件快速输出目标公司名单，可选附带 C/VP/D 层高管联系名单。**不触发 WebSearch**，token 消耗极低。

> 数据集由 `company-filter-refresh` skill 定期维护，建议每 7-30 天刷新一次。
> 高管数据建议每 14 天刷新一次（人员变动较频繁）。

## 数据集位置

```
skills/company-filter/data/
├── companies.csv       # 公司主数据集
├── executives.csv      # 高管数据集（C/VP/D 层）
├── exclusions.csv      # 排除名单（客户 / 跟进中 / 已拒绝）
└── last_updated.txt    # 上次刷新时间（companies / executives 分别记录）
```

## companies.csv 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| name | 公司名 | Stripe |
| industry | 行业/细分 | FinTech |
| region | 国家/州/城市 | US, CA, San Francisco |
| size | 员工数范围 | 1000+ |
| stage | 融资阶段 | IPO |
| revenue | 营收范围 | $50M+ |
| founded | 成立年份 | 2010 |
| biz_model | 商业模式 | B2B |
| tech_stack | 技术栈（逗号分隔）| AWS, Kubernetes |
| website | 官网 | stripe.com |
| description | 一句话简介 | 在线支付基础设施 |
| source | 数据来源 | Crunchbase |
| updated_at | 记录更新时间 | 2026-04-08 |

## executives.csv 字段

### 基本信息

| 字段 | 说明 | 示例 |
|------|------|------|
| company_name | 所属公司（关联 companies.csv） | Stripe |
| name | 高管姓名 | Patrick Collison |
| title | 完整职位 | Co-Founder & CEO |
| role_level | 层级 | C / VP / D |
| role_type | 职能方向 | CEO / CTO / CFO / COO / CMO / CRO / CPO / VP Sales / VP Eng / VP Marketing / Director |
| location | 所在城市/时区 | San Francisco, CA / UTC-8 |

### 联系方式

| 字段 | 说明 | 来源 | 示例 |
|------|------|------|------|
| email_work | 工作邮箱 | Hunter.io, Apollo | patrick@stripe.com |
| email_personal | 个人邮箱 | 公开信息 | — |
| phone_direct | 直线电话 | Apollo, RocketReach | — |
| phone_mobile | 手机 | Lusha, SignalHire | — |
| calendly | 预约链接 | 个人网站/LinkedIn | calendly.com/… |

### 社交与内容

| 字段 | 说明 | 示例 |
|------|------|------|
| linkedin_url | LinkedIn 主页 | linkedin.com/in/patrickcollison |
| twitter | Twitter/X 账号 | @patrickc |
| github | GitHub 账号 | github.com/… |
| medium | Medium 主页 | medium.com/@… |
| substack | Substack 订阅 | substack.com/… |
| youtube | YouTube 频道 | youtube.com/… |
| personal_website | 个人网站/博客 | patrickcollison.com |

### 公开影响力

| 字段 | 说明 | 示例 |
|------|------|------|
| speaking_history | 演讲经历（会议/播客） | SaaStr 2024, a16z podcast |
| press_mentions | 近期媒体报道 | Forbes 2024, TechCrunch |
| publications | 发表文章/研究 | Medium post, research paper |

### 元数据

| 字段 | 说明 | 示例 |
|------|------|------|
| source | 数据来源 | LinkedIn, Crunchbase, Apollo |
| confidence | 数据可信度 | high / medium / low |
| updated_at | 记录更新时间 | 2026-04-08 |

## 筛选条件

### 核心条件（至少提供一项）

| 条件 | 字段 | 示例 |
|------|------|------|
| 行业 | industry | SaaS, FinTech, AI/ML |
| 地区 | region | US, California, San Francisco |
| 公司规模 | size | 51-200, 1000+ |

### 可选条件

| 条件 | 字段 | 示例 |
|------|------|------|
| 营收范围 | revenue | $1M-$10M |
| 融资阶段 | stage | Series A, Series B |
| 成立时间 | founded | 2020 年之后 |
| 技术栈 | tech_stack | AWS, Snowflake |
| 商业模式 | biz_model | B2B |

### 高管选项（`--with-executives`）

| 选项 | 说明 | 默认 |
|------|------|------|
| `--with-executives` | 附带高管名单 | 关闭 |
| `--exec-level` | 指定层级：C / VP / D / all | all |
| `--exec-role` | 指定职能：CEO / CTO / Sales / Eng 等 | 不限 |

### 排除名单选项（`--exclude`）

| 选项 | 说明 | 默认 |
|------|------|------|
| `--exclude` | 启用排除名单过滤 | **开启**（默认过滤） |
| `--exclude-reason` | 只排除特定原因：customer / in_pipeline / rejected / dnd | 全部 |
| `--show-excluded` | 显示被排除的公司及原因（用于审查） | 关闭 |
| `--no-exclude` | 关闭排除过滤，显示全部结果 | 关闭 |

## exclusions.csv 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| company_name | 公司名（匹配 companies.csv） | Stripe |
| reason | 排除原因 | customer / in_pipeline / rejected / dnd |
| since | 加入排除名单的日期 | 2026-04-08 |
| expires_at | 排除到期日（空 = 永久）| 2026-10-08 |
| notes | 备注说明 | "Q4 revisit"、"已是客户 2 年" |
| added_by | 谁加入的 | charlie |
| source | 来源 | manual / gmail-manager / crm |

### reason 说明

| reason | 含义 | 默认排除期 |
|--------|------|----------|
| `customer` | 已签约客户 | 永久 |
| `in_pipeline` | 正在跟进中 | 自动同步自 outreach_log.csv |
| `rejected` | 明确拒绝或无意向 | 180 天（可配置） |
| `dnd` | Do Not Contact，永不联系 | 永久 |

## 运行流程

### 标准查询（默认，含排除过滤）

```
用户提供筛选条件
       ↓
读取 data/companies.csv → 按条件过滤
       ↓
读取 data/exclusions.csv（默认启用）
  ├── 自动同步 gmail-manager/outreach_log.csv → 补充 in_pipeline 记录
  └── 对比排除名单，移除命中条目
       ↓
输出公司列表 + 排除摘要（"已过滤 X 家：N 客户 / M 跟进中 / K 拒绝"）
```

### 带高管

```
用户提供筛选条件 + --with-executives
       ↓
读取 companies.csv → 条件过滤 → 排除过滤
       ↓
关联读取 executives.csv，按 --exec-level / --exec-role 过滤
       ↓
合并输出：公司 + 高管名单
```

### 查看被排除的公司（`--show-excluded`）

```
用户提供筛选条件 + --show-excluded
       ↓
正常过滤后，额外输出被排除名单：
  公司名 | 排除原因 | 加入时间 | 到期时间 | 备注
```

**token 消耗**：多一次 exclusions.csv 读取，仍为近零。

## 使用方式

### 查询

基础查询（自动过滤排除名单）：
```
从本地数据集找：AI/ML 行业，美国加州，51-200 人，Series A 或 B
```

附带高管：
```
从本地数据集找：AI/ML 行业，美国加州，51-200 人，Series A 或 B
--with-executives --exec-level C --exec-role CTO,VP Sales
```

查看哪些公司被排除了：
```
从本地数据集找：FinTech 行业，美国 --show-excluded
```

忽略排除名单（全量查看）：
```
从本地数据集找：FinTech 行业，美国 --no-exclude
```

### 排除名单管理

添加到排除名单：
```
将 Stripe 加入排除名单，原因：customer
将 Plaid 加入排除名单，原因：rejected，备注："Q4 再跟进"，到期：2026-10-01
将 Brex 加入排除名单，原因：dnd
```

从排除名单移除：
```
将 Plaid 从排除名单移除
```

查看完整排除名单：
```
显示排除名单，按原因分类
```

参考 `prompts/describe-company-filter.md` 获取完整引导。

## 输出格式

### 仅公司列表

| 公司名 | 行业 | 地区 | 员工数 | 融资阶段 | 简介 | 官网 |
|--------|------|------|--------|---------|------|------|

### 公司 + 高管（`--with-executives`）

| 公司名 | 行业 | 地区 | 高管姓名 | 职位 | 层级 | LinkedIn | Email |
|--------|------|------|---------|------|------|---------|-------|
| Stripe | FinTech | US/SF | Patrick Collison | Co-Founder & CEO | C | linkedin.com/... | — |
| Stripe | FinTech | US/SF | John Collison | Co-Founder & President | C | linkedin.com/... | — |

### CSV 导出（可选）

带高管时导出两个文件：
- `companies_result.csv`
- `executives_result.csv`（关联 company_name）

## 降级策略

| 场景 | 处理 |
|------|------|
| 公司数 < 5 | 提示运行 company-filter-refresh 刷新 |
| 高管数据缺失某公司 | 标记 [待补充]，提示运行 company-filter-refresh --executives |
| executives.csv 超过 14 天未刷新 | 查询前警告数据可能过期 |
| exclusions.csv 不存在 | 自动创建空文件，提示可手动添加排除条目 |
| outreach_log.csv 同步失败 | 跳过 in_pipeline 自动同步，仅使用手动排除记录，并提示 |
| rejected 条目已过期 | 查询时自动提示："X 家公司排除已到期，是否重新纳入名单？" |

## 注意事项

- 高管数据变动频率高于公司数据，建议每 14 天刷新一次
- Email 字段需通过 Hunter.io 等工具补充，本 skill 不直接爬取
- LinkedIn URL 仅供参考，访问需登录
