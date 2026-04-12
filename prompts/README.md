# Prompt 引导模板

引导用户清晰描述需求的模板集合。

## 使用方式

直接阅读对应模板，按照问题清单逐步填写，最终生成结构化的需求描述。

## 可用模板

| 文件 | 场景 |
|------|------|
| `describe-company-filter.md` | 公司筛选需求引导（配合 company-filter skill） |
| `describe-feature.md` | 描述新功能需求 |
| `describe-bug.md` | 描述 bug |
| `describe-extension.md` | 描述扩展方向 |

## 模板格式

每个 `.md` 文件包含：
1. 引导说明 — 告诉用户这个模板的目的
2. 问题清单 — 逐步引导用户提供关键信息
3. 输出模板 — 将用户回答组织成结构化描述

## 编写新模板

1. 在 `prompts/` 下创建 `describe-{场景}.md`
2. 按上述格式编写
3. 更新本 README 的可用模板表格
