---
name: example-func
description: 示例：Go 实现类 skill，统计项目代码行数
type: func
category: feature
status: active
---

# 代码行数统计

## 用途

递归统计指定目录下各语言的代码行数。

## 触发条件

用户需要了解项目规模时使用。

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| path | no | 目标目录，默认当前目录 |
| exclude | no | 排除的目录模式，如 `vendor,node_modules` |

## 输出

按语言分类的代码行数统计表。

## 示例

```
$ charlie-skill run example-func --path .
Language    Files    Lines
Go          12       1,234
Markdown    5        456
YAML        3        89
Total       20       1,779
```
