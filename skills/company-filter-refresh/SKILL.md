---
name: company-filter-refresh
description: 批量拉取公开数据源，更新公司数据集和高管数据集，建议公司 7-30 天、高管 14 天刷新一次
category: business
status: active
---

# Company Filter Refresh — 数据集刷新

从多个免费公开数据源批量拉取公司及高管数据，更新本地 CSV 数据集。
**集中消耗 token，一次刷新，多次复用。**

## 刷新目标

| 数据集 | 文件 | 建议刷新频率 |
|--------|------|------------|
| 公司数据 | `data/companies.csv` | 每月一次（全量） / 每周（增量） |
| 高管数据 | `data/executives.csv` | 每 14 天（人员变动频繁） |

---

## 一、公司数据刷新

### 数据源 — Tier 1（批量目录页）

| 数据源 | 拉取方式 | 覆盖字段 | 预估数量 |
|--------|---------|---------|---------|
| YC Companies | WebFetch ycombinator.com/companies | name, industry, region, size, stage, description | 4000+ |
| Inc. 5000 | WebFetch inc.com/inc5000/2024 | name, industry, region, revenue, size | 5000 |
| Forbes Cloud 100 | WebFetch forbes.com/cloud100 | name, industry, revenue | 100 |
| Deloitte Fast 500 | WebFetch deloitte.com/fast500 | name, industry, region, growth | 500 |
| Crunchbase Trending | WebSearch site:crunchbase.com/organization | name, industry, stage, founded | 按需 |

### 数据源 — Tier 2（按行业分类）

| 数据源 | 拉取方式 | 覆盖字段 |
|--------|---------|---------|
| G2 Categories | WebFetch g2.com/categories/{industry} | name, size, biz_model |
| Wellfound | WebFetch wellfound.com/companies?filter={industry} | name, stage, size, tech_stack |
| Product Hunt | WebFetch producthunt.com/topics/{industry} | name, description, founded |
| GitHub Awesome Lists | WebFetch github.com/awesome-{industry} | name, description, website |

### 数据源 — Tier 3（技术栈补充）

| 数据源 | 拉取方式 | 覆盖字段 |
|--------|---------|---------|
| BuiltWith | WebFetch builtwith.com/websites-using/{tech} | name, website, tech_stack |
| G2 Integrations | WebFetch g2.com/products/{tech}/integrations | name, tech_stack |

---

## 二、高管数据刷新

### 数据源（按优先级）

#### Tier 1 — 人物基本信息（name, title, linkedin_url）

| 数据源 | 拉取方式 | 覆盖字段 | 说明 |
|--------|---------|---------|------|
| LinkedIn 公司页 | WebFetch linkedin.com/company/{slug}/people | name, title, linkedin_url, location | 公开页 Leadership 板块，最全 |
| Crunchbase 组织页 | WebFetch crunchbase.com/organization/{slug}/people | name, title, role_type | 创始人 + 高管为主 |
| 公司官网 /about | WebFetch {website}/about、/team、/leadership | name, title | 中小公司常见，信息最新 |
| Wellfound 公司页 | WebFetch wellfound.com/company/{slug} | name, title, linkedin_url | 创业公司团队 |
| PitchBook 人物页 | WebSearch site:pitchbook.com/profiles/person {name} {company} | name, title, bio | VC 背景高管 |
| Owler 公司页 | WebFetch owler.com/company/{slug} | name, title | CEO 为主 |

#### Tier 2 — 邮箱与电话（email, phone）

| 数据源 | 拉取方式 | 覆盖字段 | 说明 |
|--------|---------|---------|------|
| Hunter.io | WebFetch hunter.io/search?domain={website} | email_work | 免费额度 25 次/月，邮箱格式推断 |
| Apollo.io | WebFetch apollo.io/people?company={name} | email_work, phone_direct | 免费额度有限，B2B 最全 |
| RocketReach | WebSearch site:rocketreach.co {name} {company} | email_work, phone_mobile | 部分免费预览 |
| Lusha | WebSearch site:lusha.com/profile {name} | phone_mobile, email_work | 直线电话覆盖好 |
| SignalHire | WebFetch signalhire.com/profiles/{linkedin_id} | email_work, phone_direct | 需 LinkedIn URL |
| Clearbit (免费部分) | WebFetch clearbit.com/lookup?domain={website} | email_pattern | 邮箱格式规则推断 |

#### Tier 3 — 社交与内容平台

| 数据源 | 拉取方式 | 覆盖字段 | 说明 |
|--------|---------|---------|------|
| Twitter/X | WebSearch site:twitter.com "{name}" "{company}" | twitter, personal bio | 公开 bio 可含联系方式 |
| GitHub | WebSearch site:github.com "{name}" | github_url | 技术背景高管常见 |
| Medium | WebSearch site:medium.com "{name}" "{company}" | medium_url, publications | 有写作习惯的高管 |
| Substack | WebSearch site:substack.com "{name}" | substack_url | newsletter 作者 |
| Personal Website | WebSearch "{name}" "{company}" CEO site:*.com -linkedin -twitter | personal_website, calendly | 个人域名 |
| YouTube | WebSearch site:youtube.com "{name}" "{company}" talk | youtube_url | 演讲/访谈视频 |

#### Tier 4 — 公开影响力（演讲、媒体）

| 数据源 | 拉取方式 | 覆盖字段 | 说明 |
|--------|---------|---------|------|
| SEC EDGAR | WebFetch sec.gov/cgi-bin/browse-edgar?company={name} | name, title | 仅上市公司，含董事会成员 |
| Bloomberg Profiles | WebSearch site:bloomberg.com/profile/person "{name}" | title, bio, press_mentions | 大公司高管传记 |
| Forbes Profiles | WebSearch site:forbes.com/profile "{name}" | press_mentions, bio | 知名高管 |
| TechCrunch | WebSearch site:techcrunch.com "{name}" "{company}" | press_mentions | 融资/产品新闻 |
| PR Newswire | WebSearch site:prnewswire.com "{company}" "appoints" OR "names" | name, title | 新高管任命公告 |
| BusinessWire | WebSearch site:businesswire.com "{company}" "appoints" | name, title | 同上 |
| SaaStr / Conf 演讲 | WebSearch site:saastr.com OR site:disrupt.techcrunch.com "{name}" | speaking_history | 演讲经历 |
| Podcast 嘉宾 | WebSearch podcast "{name}" "{company}" CEO interview | speaking_history | 播客访谈记录 |

### 高管拉取流程

```
取 companies.csv 中的公司列表
       ↓
Tier 1：对每家公司拉取 LinkedIn/Crunchbase/官网 → 得到人员名单
       ↓
Tier 2：对每位高管补充邮箱/电话（Hunter.io → Apollo → RocketReach）
       ↓
Tier 3：补充社交账号（Twitter → GitHub → Medium → 个人网站）
       ↓
Tier 4：补充影响力数据（SEC → Bloomberg → 演讲记录）
       ↓
解析：name, title → 推断 role_level（C/VP/D）和 role_type
设置 confidence：多源交叉验证 = high，单源 = medium，推断 = low
       ↓
去重（以 company_name + name 为唯一键）
       ↓
写入 data/executives.csv
```

### role_level 推断规则

| 关键词 | role_level | role_type |
|--------|-----------|----------|
| CEO, Chief Executive | C | CEO |
| CTO, Chief Technology | C | CTO |
| CFO, Chief Financial | C | CFO |
| COO, Chief Operating | C | COO |
| CMO, Chief Marketing | C | CMO |
| CPO, Chief Product | C | CPO |
| CRO, Chief Revenue | C | CRO |
| Founder, Co-Founder | C | Founder |
| VP Sales, VP of Sales | VP | VP Sales |
| VP Engineering, VP Eng | VP | VP Eng |
| VP Marketing | VP | VP Marketing |
| VP Product | VP | VP Product |
| Director of Sales | D | Director |
| Director of Engineering | D | Director |
| Head of Sales | D | Director |

---

## 刷新模式

### 全量刷新（月度）
```
刷新目标: companies + executives
拉取范围: 所有 Tier 1 数据源 + 所有公司的高管页
预估 token: ~80K
建议频率: 每月一次
```

### 公司增量刷新（周度）
```
刷新目标: companies only
拉取范围: Tier 1 中有「最新」排序的页面，只追加新记录
预估 token: ~10K
建议频率: 每周一次
```

### 高管刷新（双周）
```
刷新目标: executives only
拉取范围: 对现有公司列表重新拉取高管页
预估 token: ~30K（取决于公司数量）
建议频率: 每 14 天一次
```

### 定向刷新（按行业 / 按公司）
```
刷新目标: 指定行业或指定公司列表
示例: company-filter-refresh --industry FinTech --executives
预估 token: ~15-20K
```

## 使用方式

```
运行 company-filter-refresh          # 全量刷新
运行 company-filter-refresh --companies-only   # 只刷新公司
运行 company-filter-refresh --executives       # 只刷新高管
运行 company-filter-refresh --industry AI/ML   # 定向刷新
```

## 输出摘要

```
刷新完成
─── 公司数据 ───────────────────────────
新增: 342 家 | 更新: 89 家 | 去重: 12 条
数据集总量: 4,231 家
覆盖行业: SaaS, FinTech, AI/ML, HealthTech ...

─── 高管数据 ───────────────────────────
新增: 1,205 人 | 更新: 234 人 | 去重: 45 条
数据集总量: 12,840 人
C 层: 3,201 | VP 层: 5,890 | D 层: 3,749
联系方式覆盖率:
  工作邮箱: 38% | 手机/直线: 12% | LinkedIn: 91%
  Twitter: 54% | GitHub: 23% | 个人网站: 18%
  演讲记录: 29% | 媒体报道: 41%

下次建议刷新:
  公司数据: 2026-05-08
  高管数据: 2026-04-22
```

## Token 消耗对比

| 刷新模式 | 预估 token | 支撑查询次数 |
|---------|-----------|------------|
| 全量刷新（公司+高管） | ~80K | 无限次（月度内） |
| 高管增量刷新 | ~30K | 无限次（双周内） |
| 每次实时 WebSearch 查高管 | ~8K/次 | 仅 1 次 |
