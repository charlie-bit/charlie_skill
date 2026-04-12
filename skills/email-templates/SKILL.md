---
name: email-templates
description: Sales outreach 邮件模板库，覆盖冷开发、跟进、会议邀请等场景，支持变量填充
category: business
status: active
---

# Email Templates — 邮件模板库

Sales outreach 场景的邮件模板集合。所有模板支持变量填充，与 company-filter executives 数据直接打通。

## 模板目录

```
skills/email-templates/templates/
├── cold-outreach.md       # 冷开发：首次联系
├── followup-1.md          # 跟进 #1：7 天无回复
├── followup-2.md          # 跟进 #2：再 5 天无回复
├── meeting-request.md     # 会议邀请
├── demo-request.md        # 产品 Demo 邀请
├── referral.md            # 转介绍开场
├── event-followup.md      # 活动后跟进（会议/Meetup）
├── linkedin-to-email.md   # LinkedIn 联系后转邮件
└── breakup.md             # 最终告别邮件（放弃跟进前）
```

## 变量系统

所有模板使用 `{{变量名}}` 占位，由 gmail-manager 在发送前填充。

### 收件人变量（来自 executives.csv）

| 变量 | 来源字段 | 示例 |
|------|---------|------|
| `{{name}}` | executives.name | Patrick |
| `{{full_name}}` | executives.name | Patrick Collison |
| `{{title}}` | executives.title | CEO |
| `{{company}}` | executives.company_name | Stripe |
| `{{industry}}` | companies.industry | FinTech |
| `{{company_size}}` | companies.size | 1000+ |
| `{{stage}}` | companies.stage | IPO |
| `{{region}}` | companies.region | San Francisco, CA |
| `{{website}}` | companies.website | stripe.com |

### 发件人变量（用户配置）

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{sender_name}}` | 你的名字 | Charlie |
| `{{sender_title}}` | 你的职位 | Account Executive |
| `{{sender_company}}` | 你的公司 | Acme Corp |
| `{{sender_product}}` | 你的产品/服务 | Acme Analytics |
| `{{calendly_link}}` | 预约链接 | calendly.com/charlie |
| `{{case_study}}` | 相关案例 | "我们帮助 X 公司..." |

### 场景变量（每次发送时指定）

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{pain_point}}` | 目标痛点 | 数据分析效率低 |
| `{{value_prop}}` | 价值主张 | 减少 60% 报表时间 |
| `{{social_proof}}` | 社会证明 | 已服务 50+ FinTech 公司 |
| `{{trigger_event}}` | 触发事件 | 看到你们刚完成 Series B |

---

## 模板详情

### cold-outreach — 冷开发首次联系

**适用**：从未有过往来的高管，首次接触

**主题**：`Quick question for {{company}}'s {{title}}`

**正文**：
```
Hi {{name}},

I came across {{company}} while researching leading {{industry}} companies 
in {{region}} — impressive work on {{trigger_event}}.

I work with {{title}}s at companies like yours to {{value_prop}}.
{{social_proof}}.

Would it make sense to connect for a quick 15-minute call to see 
if there's a fit? I'm happy to work around your schedule.

{{calendly_link}}

Best,
{{sender_name}}
{{sender_title}} @ {{sender_company}}
```

---

### followup-1 — 第一次跟进（7 天无回复）

**适用**：cold-outreach 发送 7 天后无回复

**主题**：`Re: Quick question for {{company}}'s {{title}}`

**正文**：
```
Hi {{name}},

Just floating this back to the top of your inbox — 
I know things get busy.

One specific reason I reached out: {{pain_point}} is something 
I hear from many {{industry}} leaders, and we've helped companies 
like {{company}} solve it by {{value_prop}}.

Worth a 15-minute chat?

{{calendly_link}}

{{sender_name}}
```

---

### followup-2 — 第二次跟进（再 5 天无回复）

**适用**：第一次跟进后 5 天仍无回复

**主题**：`Re: Quick question for {{company}}'s {{title}}`

**正文**：
```
Hi {{name}},

I'll keep this brief — I don't want to be a nuisance.

I genuinely think {{sender_product}} could help {{company}} 
with {{pain_point}}. Here's a quick case study: {{case_study}}.

If the timing isn't right, no worries at all. 
But if there's any interest, I'm here.

{{calendly_link}}

{{sender_name}}
```

---

### meeting-request — 会议邀请

**适用**：已有初步接触，邀请正式会议

**主题**：`Meeting request: {{sender_company}} × {{company}}`

**正文**：
```
Hi {{name}},

Following our recent exchange, I'd love to set up a proper 
30-minute meeting to explore how {{sender_product}} can 
specifically address {{pain_point}} for {{company}}.

I've put together a short agenda:
1. Your current approach to {{pain_point}} (5 min)
2. How we've helped similar {{industry}} companies (10 min)
3. Potential fit & next steps (15 min)

Does any of the following work for you?
{{calendly_link}}

Looking forward to connecting.

{{sender_name}}
{{sender_title}} @ {{sender_company}}
```

---

### demo-request — 产品 Demo 邀请

**适用**：高管表现出兴趣，邀请产品演示

**主题**：`{{sender_product}} demo for {{company}} — 20 minutes`

**正文**：
```
Hi {{name}},

I'd love to show you exactly how {{sender_product}} works 
for {{industry}} companies at the {{stage}} stage.

In 20 minutes, I can walk you through:
- How we handle {{pain_point}}
- {{value_prop}} — with live data
- Setup timeline and pricing overview

{{social_proof}}

Grab a slot that works for you:
{{calendly_link}}

{{sender_name}}
```

---

### referral — 转介绍开场

**适用**：通过共同联系人介绍

**主题**：`{{referrer_name}} suggested I reach out`

**正文**：
```
Hi {{name}},

{{referrer_name}} mentioned you're the right person to 
talk to about {{pain_point}} at {{company}}.

I work with {{sender_company}} to help {{industry}} teams 
{{value_prop}}. {{social_proof}}.

Would love to connect for 15 minutes — does this week work?

{{calendly_link}}

{{sender_name}}
```

> 额外变量：`{{referrer_name}}` — 介绍人姓名

---

### event-followup — 活动后跟进

**适用**：会议/Meetup 现场认识后的邮件跟进

**主题**：`Great meeting you at {{event_name}}`

**正文**：
```
Hi {{name}},

It was great chatting at {{event_name}}! 
I enjoyed our conversation about {{event_topic}}.

As I mentioned, {{sender_product}} helps {{industry}} companies 
like {{company}} to {{value_prop}}.

Would love to continue the conversation — 
are you free for a quick call this week?

{{calendly_link}}

{{sender_name}}
```

> 额外变量：`{{event_name}}`、`{{event_topic}}`

---

### linkedin-to-email — LinkedIn 联系后转邮件

**适用**：LinkedIn 上已建立连接，转移到邮件深入沟通

**主题**：`Following up from LinkedIn, {{name}}`

**正文**：
```
Hi {{name}},

Thanks for connecting on LinkedIn! 

I wanted to reach out directly — I've been following {{company}}'s 
growth in the {{industry}} space, and I think there's a real 
opportunity for us to work together on {{pain_point}}.

{{value_prop}}. {{social_proof}}.

Open to a quick 15-minute call?

{{calendly_link}}

{{sender_name}}
{{sender_title}} @ {{sender_company}}
```

---

### breakup — 最终告别（放弃前最后一封）

**适用**：两次跟进后仍无回复，发送最后一封

**主题**：`Closing the loop, {{name}}`

**正文**：
```
Hi {{name}},

I've reached out a few times and haven't heard back — 
which usually means either the timing is off or it's not a fit, 
and that's completely okay.

I'll stop reaching out after this. But if {{pain_point}} 
ever becomes a priority for {{company}}, I'd love to reconnect.

Wishing you and the {{company}} team continued success.

{{sender_name}}
```

---

## 使用方式

### 在 gmail-manager 中调用

```
用 cold-outreach 模板向 Stripe 的 Patrick Collison (CEO) 发送邮件
pain_point: 支付数据分析效率低
value_prop: 减少 60% 财务报表时间
```

### 直接查看模板

```
列出所有模板
预览 demo-request 模板
```

## 自定义模板

在 `templates/` 下新建 `{name}.md` 文件，遵循以下格式：
1. 文件头注释：适用场景、主题行
2. 正文：使用 `{{变量名}}` 占位
3. 在本 SKILL.md 模板目录中登记

## 最佳实践

- **个性化优先**: 至少填充 `{{name}}`、`{{company}}`、`{{pain_point}}` 三个变量，避免显得模板化
- **主题行简短**: 不超过 50 字符，避免在移动端被截断
- **CTA 单一**: 每封邮件只有一个行动号召（预约链接或回复问题）
- **跟进间隔**: 冷开发 7 天、第一次跟进 5 天、最终告别，超过 2 次跟进效果递减
