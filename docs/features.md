# 当前功能清单

## 已有 Skills

| Skill | 分类 | 说明 | 状态 |
|-------|------|------|------|
| company-filter | business | 从本地数据集筛选目标公司，附带高管名单，内置排除名单过滤 | active |
| company-filter-refresh | business | 批量拉取公开数据源，更新公司和高管数据集 | active |
| gmail-manager | business | Gmail 收件箱管理、outreach 发送、跟进追踪，通过 Gmail MCP 驱动 | active |
| email-templates | business | Sales outreach 邮件模板库，9 类场景，支持变量填充 | active |
| example-prompt | feature | 示例：API 文档生成器 | active |

---

## Skill 详情

### company-filter — 公司筛选

**用途**: Sales 按条件从本地数据集筛选目标公司，不触发 WebSearch，token 消耗极低。

**运行方式**:
1. 用自然语言描述筛选条件（或参考 `prompts/describe-company-filter.md`）
2. Skill 读取本地 `data/companies.csv`，按条件过滤
3. 输出结构化表格，可选导出 CSV

**离线查询脚本**（无需 Claude，无外部依赖）:
```bash
cd skills/company-filter
python3 query.py all                        # 所有公司 + 高管
python3 query.py all --brand Trimble        # 按品牌
python3 query.py all --role C --email-only  # C 层有邮箱
python3 query.py all --csv > output.csv     # 导出 CSV
python3 query.py exclusions --add "X" --reason customer  # 排除名单
```
详见 `skills/company-filter/README.md`。

**核心筛选维度**: 行业、地区、公司规模

**可选筛选维度**: 营收、融资阶段、成立时间、技术栈、商业模式

**高管扩展（`--with-executives`）**: 附带 C/VP/D 层高管，可按层级和职能过滤（CEO/CTO/VP Sales 等）

**Token 消耗**: 极低（两次本地文件读取）

**示例**:
```
从本地数据集找：AI/ML 行业，美国加州，51-200 人，Series A 或 B
--with-executives --exec-level C --exec-role CTO,VP Sales
```

**输出**: 公司列表 + 每家公司对应高管（姓名、职位、LinkedIn、邮箱）

---

### company-filter-refresh — 数据集刷新

**用途**: 批量从公开数据源拉取公司和高管数据，更新本地数据集。集中消耗 token，一次刷新，多次复用。

**运行方式**:
1. 在 Claude Code 中使用（WebSearch/WebFetch 拉取数据）
2. 或离线脚本操作（导入外部 CSV、推断邮箱、合并数据）

**离线脚本**（无需 Claude，无外部依赖）:
```bash
cd skills/company-filter-refresh

python3 refresh.py status                          # 数据集状态 + 覆盖率
python3 refresh.py import companies --file x.csv   # 导入公司（Crunchbase/YC 等导出）
python3 refresh.py import executives --file x.csv  # 导入高管（LinkedIn/Apollo 等导出）
python3 refresh.py email                           # 批量推断缺失邮箱
python3 refresh.py merge executives --file x.csv   # 合并补充数据
```
详见 `skills/company-filter-refresh/README.md`。

**支持的外部数据源**: Crunchbase、LinkedIn Sales Navigator、Apollo.io、ZoomInfo、RocketReach、Hunter.io、YC Companies、Inc.5000

**建议频率**: 公司数据每月一次，高管数据每 14 天一次

---

## 两个 Skill 的协作关系

```
[定期] company-filter-refresh  →  更新 data/companies.csv
                                          ↓
[每次查询] company-filter       →  读取本地文件，近零 token 输出结果
```

**Token 对比**:

| 方案 | 每次查询 token | 月度总消耗（30 次查询）|
|------|--------------|----------------------|
| 每次 WebSearch | ~5K | ~150K |
| 月刷新 + 本地过滤 | ~0.5K | ~55K（50K 刷新 + 15K 查询）|
| 周刷新 + 本地过滤 | ~0.5K | ~55K（40K 刷新 + 15K 查询）|

---

## Prompt 引导

| 模板 | 场景 |
|------|------|
| `describe-company-filter.md` | 公司筛选需求引导（配合 company-filter skill） |
| `describe-feature.md` | 描述新功能需求 |
| `describe-bug.md` | 描述 bug |
| `describe-extension.md` | 描述扩展方向 |
