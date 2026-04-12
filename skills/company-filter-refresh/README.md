# Company Filter Refresh

更新 `company-filter` 的本地数据集。支持主动搜索、高管发现、联系方式补充、外部导入。

## 依赖

```bash
# search/discover/enrich 需要（import/merge/email/status 无需）
pip install requests beautifulsoup4
```

## 快速开始

```bash
cd skills/company-filter-refresh

# 查看数据集状态
python3 refresh.py status

# 从 YC 搜索 FinTech 公司
python3 refresh.py search --source yc --industry fintech --limit 30

# 从 Google 搜索
python3 refresh.py search --query "Trimble resellers USA" --limit 20

# 自动发现高管（抓取公司官网 /about /team 页）
python3 refresh.py discover

# 推断缺失邮箱
python3 refresh.py email

# 从 Google/RocketReach 补充联系方式
python3 refresh.py enrich

# 一键全量刷新
python3 refresh.py refresh --mode full --industry "surveying equipment"
```

## 目录结构

```
company-filter-refresh/
├── SKILL.md          # Skill 完整定义（数据源清单、刷新策略）
├── README.md         # 本文件
└── refresh.py        # 刷新脚本

# 数据写入到:
company-filter/data/
├── companies.csv
├── executives.csv
└── last_updated.txt
```

## 子命令参考

### search — 搜索公司

从公开数据源搜索公司，自动合并到 `companies.csv`（去重）。

| 数据源 | `--source` | 特点 |
|--------|-----------|------|
| Google | `google`（默认） | 最灵活，任意关键词 |
| YC Companies | `yc` | 4000+ 创业公司，支持行业/地区过滤 |
| GitHub Awesome | `awesome` | 按主题聚合的公司列表 |

```bash
# Google 搜索（最灵活）
python3 refresh.py search --query "Leica authorized dealer surveying US" --limit 20
python3 refresh.py search --query "AI/ML startups Series A San Francisco"

# YC Companies（创业公司最全）
python3 refresh.py search --source yc --industry fintech --limit 50
python3 refresh.py search --source yc --industry "artificial intelligence" --region US

# GitHub Awesome Lists
python3 refresh.py search --source awesome --topic surveying
python3 refresh.py search --source awesome --topic fintech
```

---

### discover — 发现高管

抓取 `companies.csv` 中每家公司的官网（/about、/team、/leadership 等页面），自动提取 C/VP/D 层高管。

```bash
# 全部公司
python3 refresh.py discover

# 指定公司
python3 refresh.py discover --company "AllTerra Central"
```

**抓取路径优先级**：
`/about` → `/about-us` → `/team` → `/our-team` → `/leadership` → `/management` → `/people` → `/company`

**提取策略**：
1. 结构化 HTML（`<h3>Name</h3><p>Title</p>`）
2. 文本正则匹配（`Name — Title` / `Name, Title`）
3. 自动推断 role_level（C/VP/D）

---

### enrich — 补充联系方式

从 B2B 数据平台搜索，补充 email、phone、linkedin。

```bash
# 全部高管，所有来源
python3 refresh.py enrich

# 指定公司
python3 refresh.py enrich --company "AllTerra Central"

# 只用 Google 搜索
python3 refresh.py enrich --source google

# 只用 RocketReach
python3 refresh.py enrich --source rocketreach
```

**数据来源**：
- Google 搜索（email/phone/linkedin 正则提取）
- RocketReach 公开预览页

---

### email — 推断邮箱

根据高管姓名 + 公司域名，生成邮箱地址。

```bash
# 默认 first.last@domain
python3 refresh.py email

# 指定 pattern
python3 refresh.py email --pattern "{first}.{last}@{domain}"
python3 refresh.py email --pattern "{first}@{domain}"
python3 refresh.py email --pattern "{first_initial}{last}@{domain}"

# 只对某公司
python3 refresh.py email --company "Seiler Geospatial"
```

| Pattern | 示例 |
|---------|------|
| `{first}.{last}@{domain}` | bobby.hempfling@allterracentral.com |
| `{first}@{domain}` | bobby@allterracentral.com |
| `{first_initial}{last}@{domain}` | bhempfling@allterracentral.com |
| `{first}{last}@{domain}` | bobbyhempfling@allterracentral.com |

---

### import — 导入外部 CSV

从 Crunchbase、LinkedIn、Apollo 等平台的导出 CSV 导入。

```bash
python3 refresh.py import companies --file crunchbase.csv \
  --mapping "name=Organization Name,region=Headquarters,website=Website"

python3 refresh.py import executives --file linkedin.csv \
  --mapping "executive_name=Full Name,title=Title,company_name=Company"
```

**常用平台 mapping**：

| 平台 | 导入目标 | mapping |
|------|---------|---------|
| Crunchbase | companies | `name=Organization Name,region=Headquarters Location,website=Website` |
| LinkedIn | executives | `executive_name=Full Name,title=Title,company_name=Company` |
| Apollo.io | executives | `executive_name=Name,email_work=Email,phone=Phone,company_name=Company` |
| ZoomInfo | executives | `executive_name=Full Name,email_work=Email Address,phone=Direct Phone` |
| Hunter.io | executives | `executive_name=Name,email_work=Email,confidence=Confidence` |

---

### merge — 合并 CSV

合并另一个 CSV，已有记录只补空字段（不覆盖），新记录追加。

```bash
python3 refresh.py merge companies --file extra_companies.csv
python3 refresh.py merge executives --file apollo_verified.csv
```

---

### refresh — 一键编排

按顺序执行：search → discover → email → enrich。

```bash
# 全量刷新
python3 refresh.py refresh --mode full --industry "surveying equipment"

# 只刷新公司
python3 refresh.py refresh --mode companies --industry fintech

# 只刷新高管
python3 refresh.py refresh --mode executives

# 定向：某行业
python3 refresh.py refresh --mode targeted --industry "AI/ML"
```

| mode | 执行步骤 |
|------|---------|
| `full` | search + discover + email + enrich |
| `companies` | search only |
| `executives` | discover + email + enrich |
| `targeted` | search(industry) + discover + email + enrich |

---

### status — 数据集状态

```bash
python3 refresh.py status
```

输出：公司/高管数量、品牌分布、Email/Phone/LinkedIn 覆盖率、上次刷新时间、改进建议。

---

## 典型工作流

### 场景 1：从零建立新行业数据集

```bash
# 1. 从 YC + Google 搜索公司
python3 refresh.py search --source yc --industry fintech --limit 50
python3 refresh.py search --query "fintech companies Series A USA" --limit 30

# 2. 抓取官网发现高管
python3 refresh.py discover

# 3. 推断邮箱
python3 refresh.py email

# 4. 补充联系方式
python3 refresh.py enrich

# 5. 查看结果
python3 refresh.py status
```

### 场景 2：定期增量刷新

```bash
# 合并最新导出数据
python3 refresh.py merge companies --file new_crunchbase.csv
python3 refresh.py merge executives --file new_apollo.csv

# 为新增记录推断邮箱和补充信息
python3 refresh.py email
python3 refresh.py enrich

python3 refresh.py status
```

### 场景 3：一键全量

```bash
python3 refresh.py refresh --mode full --industry "surveying equipment"
```

## SKILL.md 功能对照

| SKILL.md 功能 | refresh.py 命令 | 实现方式 |
|---|---|---|
| Tier 1 公司数据源（YC/Inc.5000） | `search --source yc` | YC Algolia API |
| Google 搜索公司 | `search --source google` | Google HTML 解析 |
| GitHub Awesome Lists | `search --source awesome` | GitHub Raw 解析 |
| 官网高管发现 | `discover` | 抓取 /about /team 页 |
| Hunter.io/Apollo 补充联系方式 | `enrich` | Google + RocketReach |
| 邮箱推断 | `email` | 姓名+域名 pattern |
| Crunchbase/LinkedIn 导入 | `import` | CSV 列名映射 |
| 数据合并去重 | `merge` | 按 name/company+name 去重 |
| 全量/增量/定向刷新 | `refresh --mode` | 编排 search→discover→email→enrich |
| 状态 + 覆盖率 | `status` | 本地统计 |
