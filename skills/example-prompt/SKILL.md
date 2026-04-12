---
name: example-prompt
description: 示例：纯 prompt 类 skill，引导用户生成 API 文档
type: prompt
category: feature
status: active
---

# API 文档生成器

## 用途

根据用户描述的 API 端点信息，生成标准格式的 API 文档。

## 触发条件

用户需要为 API 编写文档时使用。

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| endpoint | yes | API 路径，如 `/api/v1/users` |
| method | yes | HTTP 方法 |
| description | yes | 接口功能描述 |

## Prompt 模板

```
请为以下 API 生成文档：

- 端点: {{endpoint}}
- 方法: {{method}}
- 描述: {{description}}

要求：
1. 包含请求参数说明
2. 包含响应格式
3. 包含错误码列表
4. 包含调用示例
```

## 示例

```
输入: endpoint=/api/v1/users, method=GET, description=获取用户列表
输出: 标准 API 文档 markdown
```
