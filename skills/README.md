# Skills 编写规范

## 概述

所有 skill 均为 prompt/模板驱动，以 `SKILL.md` 为核心定义文件。Claude Code 可直接加载使用。

## 目录结构

每个 skill 一个目录，目录名即 skill 名：

```
skills/
├── _template/          # 新建 skill 的模板
│   └── SKILL.md
├── my-skill/
│   └── SKILL.md        # skill 定义
```

## SKILL.md Frontmatter

```yaml
---
name: skill-name           # 唯一标识，与目录名一致
description: 一句话描述
category: feature | business | infra
status: active | planned | deprecated
---
```

## 新建 Skill

1. 复制 `_template/` 目录，重命名为你的 skill 名
2. 编辑 `SKILL.md`，填写 frontmatter 和内容
3. 提交 PR

## Category 说明

- **feature**: 通用功能类，如代码生成、格式转换
- **business**: 业务逻辑类，如订单处理、数据校验
- **infra**: 基础设施类，如部署、监控、CI/CD
