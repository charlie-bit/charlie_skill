# 架构说明

## 整体架构

纯 prompt/模板驱动，无代码依赖。

```
charlie_skill/
│
├── skills/              # Skill 定义（核心内容）
│   ├── _template/       # 新建 skill 的起点
│   └── {skill-name}/    # 每个 skill 一个目录，包含 SKILL.md
│
├── prompts/             # 用户引导模板
│   └── describe-*.md    # 引导用户描述功能/bug/扩展需求
│
├── docs/                # 项目文档
│   ├── features.md      # 当前功能清单
│   ├── roadmap.md       # 扩展路线图
│   └── architecture.md  # 本文件
│
└── .claude/skills/      # 项目级 Claude Code skill
```

## 数据流

1. **skill 发现**: Claude Code 扫描 `skills/*/SKILL.md`，通过 frontmatter 识别 skill 元信息
2. **skill 使用**: 用户通过 Claude Code 调用对应 skill，prompt 模板直接生效
3. **需求引导**: `prompts/describe-*.md` 提供结构化问答，帮助用户组织需求描述

## 关键设计决策

- **零代码依赖**: 不需要编译、安装、运行任何程序，降低贡献门槛
- **frontmatter 驱动**: SKILL.md 的 YAML frontmatter 是 skill 元数据的唯一来源
- **目录即命名**: skill 目录名就是 skill 的唯一标识
- **Claude Code 原生集成**: 直接利用 Claude Code 的 skill 加载机制，无需自建引擎
