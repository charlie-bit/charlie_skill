---
name: gmail-manager
description: Gmail 邮件管理，支持收件箱查询、outreach 发送、跟进追踪，通过 Gmail MCP 驱动
category: business
status: active
---

# Gmail Manager — 邮件管理

通过 Gmail MCP 操作 Gmail，覆盖收件箱管理、outreach 发送、跟进追踪全流程。
与 `company-filter` 的 executives 数据深度集成。

## 前置条件

需要配置 Gmail MCP 服务器：
```
MCP Server: gmail 或 google-workspace
权限范围: gmail.readonly + gmail.send + gmail.labels + gmail.modify
```

## 数据文件

```
skills/gmail-manager/data/
├── outreach_log.csv     # 发件记录（状态追踪）
└── last_sync.txt        # 上次同步时间
```

### outreach_log.csv 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| id | 唯一 ID | OUT-001 |
| company_name | 目标公司 | Stripe |
| executive_name | 目标高管 | Patrick Collison |
| executive_title | 职位 | CEO |
| email_to | 收件人邮箱 | patrick@stripe.com |
| template_used | 使用的模板 | cold-outreach |
| subject | 邮件主题 | — |
| sent_at | 发送时间 | 2026-04-08 10:00 |
| status | 状态 | sent / replied / no-response / bounced |
| reply_at | 回复时间 | — |
| follow_up_count | 已跟进次数 | 0 |
| next_follow_up | 下次跟进日期 | 2026-04-15 |
| notes | 备注 | 对方表示感兴趣 |
| thread_id | Gmail 线程 ID | 18abc123 |

---

## 功能一：收件箱查询

按公司名、高管姓名、域名搜索历史邮件，了解已有往来。

### 使用方式

```
查询我和 Stripe 的所有邮件往来
查询来自 @stripe.com 域名的邮件
查询 Patrick Collison 发给我的邮件
查询过去 30 天内所有 FinTech 公司的邮件
```

### 运行流程

```
输入公司名 / 高管名 / 域名
       ↓
Gmail MCP: search_emails(query="from:{domain} OR to:{domain}")
       ↓
按时间倒序排列，提取关键信息
       ↓
输出邮件摘要列表
```

### 输出格式

| 日期 | 发件人 | 主题 | 状态 | 摘要 |
|------|--------|------|------|------|
| 2026-04-01 | patrick@stripe.com | Re: Partnership | 已读 | 对方回复表示… |

---

## 功能二：Outreach 发送

结合 `company-filter` executives 名单和 `email-templates` 模板，发送个性化 outreach。

### 使用方式

```
向 company-filter 筛选出的 AI/ML 公司 CTO 发送 cold-outreach 模板
向 Stripe 的 Patrick Collison 发送会议邀请
批量向名单中 Series A 公司的 VP Sales 发送 demo-request 模板
```

### 单封发送流程

```
指定目标（公司/高管）+ 模板
       ↓
读取 executives.csv 获取联系信息（email_work, name, title, company）
       ↓
读取 email-templates 对应模板，填充变量：
  {{name}}, {{title}}, {{company}}, {{industry}}, {{pain_point}} 等
       ↓
预览渲染后的邮件内容
       ↓
用户确认 → Gmail MCP: send_email / create_draft
       ↓
写入 outreach_log.csv（status: sent）
```

### 批量发送流程

```
指定名单（来自 company-filter 结果）+ 模板
       ↓
逐条渲染个性化内容（每封邮件填充不同的公司/人名信息）
       ↓
批量预览（展示前 3 封 + 摘要）
       ↓
用户确认 → 按间隔逐封发送（避免触发 Gmail 限制，间隔 30-60 秒）
       ↓
全部写入 outreach_log.csv
```

### 发送前检查

- 检查 outreach_log.csv，若该联系人 30 天内已发送过，**警告并跳过**
- 检查 executives.csv 中 email_work 字段是否存在，无邮箱则提示补充
- 批量发送每日上限：50 封（Gmail 建议限制）

---

## 功能三：跟进追踪

追踪已发 outreach 的回复状态，到期自动提醒跟进。

### 使用方式

```
查看所有待跟进的 outreach（超过 7 天未回复）
查看 Stripe 相关的所有 outreach 状态
将 OUT-001 标记为已回复
```

### 跟进规则（默认）

| 跟进次数 | 触发条件 | 使用模板 |
|---------|---------|---------|
| 第 1 次 | 发送后 7 天无回复 | followup-1 |
| 第 2 次 | 第 1 次后 5 天无回复 | followup-2 |
| 放弃 | 第 2 次后 5 天无回复 | 标记 status: archived |

### 运行流程

```
读取 outreach_log.csv
       ↓
筛选 status=sent 且 next_follow_up <= 今天 的记录
       ↓
Gmail MCP: search_emails(thread_id=...) 检查是否已有回复
       ↓
有回复 → 更新 status: replied，记录 reply_at
无回复 → 列出待跟进名单，按模板准备跟进邮件
       ↓
用户确认 → 发送跟进，更新 follow_up_count + next_follow_up
```

### 状态看板输出

```
=== Outreach 状态看板 ===
待跟进:  12 封（已超 7 天无回复）
已回复:  8 封（回复率 24%）
进行中:  21 封（等待回复）
已归档:  5 封（放弃跟进）
总发送:  46 封

最近回复:
  - Stripe / Patrick Collison (CEO) → 2026-04-07 "感谢您的联系..."
  - Plaid / John Smith (VP Sales) → 2026-04-06 "我们很感兴趣..."
```

---

## 功能四：模板库管理

查看、预览、选择 email-templates 中的模板。

### 使用方式

```
列出所有可用邮件模板
预览 cold-outreach 模板
用 meeting-request 模板向 [高管名] 发送邮件
```

---

## 完整 Pipeline

```
company-filter（筛选公司 + 高管）
       ↓
gmail-manager inbox（检查是否已有往来）
       ↓
email-templates（选择合适模板）
       ↓
gmail-manager outreach（发送个性化邮件）
       ↓
gmail-manager followup（追踪回复，定期跟进）
```
