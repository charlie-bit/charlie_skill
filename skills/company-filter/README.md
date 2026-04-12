# Company Filter

从本地数据集按条件筛选目标公司，可附带 C/VP/D 层高管联系名单。

## 快速开始

```bash
cd skills/company-filter

# 查看所有公司 + 高管
python3 query.py all

# 按品牌过滤
python3 query.py all --brand Trimble

# 只看 C 层有邮箱的
python3 query.py all --role C --email-only

# 导出 CSV
python3 query.py all --csv > output.csv
```

## 目录结构

```
company-filter/
├── SKILL.md          # Skill 完整定义（筛选条件、数据源、流程）
├── README.md         # 本文件
├── query.py          # 离线查询脚本（无外部依赖）
└── data/
    ├── companies.csv     # 公司主数据集
    ├── executives.csv    # 高管联系信息
    └── exclusions.csv    # 排除名单（自动生成）
```

## query.py 指令参考

### 子命令

| 子命令 | 说明 |
|--------|------|
| `companies` | 查询公司数据 |
| `executives` | 查询高管数据 |
| `all` | 合并视图：公司 + 高管（最常用） |
| `exclusions` | 管理排除名单 |

### 通用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--brand` | 按品牌过滤 | `--brand Trimble` |
| `--region` | 按地区关键词过滤 | `--region TX` |
| `--role` | 按高管层级过滤 | `--role C` / `--role VP` / `--role D` |
| `--confidence` | 按数据可信度过滤 | `--confidence high` |
| `--email-only` | 只显示有邮箱的记录 | |
| `--exclude` | 应用排除名单过滤 | |
| `--csv` | 输出 CSV 格式（可重定向到文件） | |
| `--company` | 按公司名模糊匹配（executives/all） | `--company "AllTerra"` |

### 查询示例

```bash
# 所有 Leica 公司的 C 层高管
python3 query.py all --brand Leica --role C

# 高可信度联系人
python3 query.py executives --confidence high

# 德州地区所有高管
python3 query.py all --region TX

# 某公司高管详情
python3 query.py executives --company "G4 Geomatic"

# 有邮箱的 VP 及以上（排除已有客户）
python3 query.py all --role C --email-only --exclude
python3 query.py all --role VP --email-only --exclude

# 导出 Trimble 全量数据为 CSV
python3 query.py all --brand Trimble --csv > trimble_leads.csv
```

### 排除名单管理

```bash
# 查看当前排除名单
python3 query.py exclusions

# 添加（已有客户，永久排除）
python3 query.py exclusions --add "Stripe" --reason customer

# 添加（已拒绝，有到期日）
python3 query.py exclusions --add "Plaid" --reason rejected --expires 2026-10-01 --notes "Q4 revisit"

# 移除
python3 query.py exclusions --remove "Plaid"

# 查询时自动过滤排除名单
python3 query.py all --exclude
```

排除原因说明：

| reason | 含义 | 默认排除期 |
|--------|------|----------|
| `customer` | 已签约客户 | 永久 |
| `in_pipeline` | 正在跟进 | 永久（手动移除） |
| `rejected` | 明确拒绝 | 建议设 expires |
| `dnd` | Do Not Contact | 永久 |

## CSV 字段说明

### companies.csv

| 字段 | 说明 |
|------|------|
| name | 公司名 |
| brand | 代理品牌（Trimble / Leica） |
| region | 总部所在地 |
| website | 官网 |
| description | 一句话简介 |
| source | 数据来源 |
| updated_at | 更新时间 |

### executives.csv

| 字段 | 说明 |
|------|------|
| company_name | 所属公司 |
| brand | 代理品牌 |
| headquarters | 公司总部 |
| executive_name | 高管姓名 |
| title | 职位 |
| role_level | C / VP / D |
| linkedin_url | LinkedIn 链接 |
| email_work | 工作邮箱 |
| phone | 电话 |
| confidence | 数据可信度（high / medium / low） |
| updated_at | 更新时间 |

## 数据刷新

数据集由 `company-filter-refresh` skill 维护：

```bash
# 在 Claude Code 中执行
运行 company-filter-refresh              # 全量刷新
运行 company-filter-refresh --executives  # 只刷新高管
```

建议频率：公司数据每月一次，高管数据每 14 天一次。

## 与其他 Skill 的协作

```
company-filter   → 筛选公司 + 高管
       ↓
gmail-manager    → 检查往来 → 发送 outreach → 跟进追踪
       ↓
email-templates  → 提供邮件模板（cold-outreach / followup / demo 等）
```
