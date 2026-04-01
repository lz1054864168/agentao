# 修复 DeepSeek 模型 max_tokens 限制问题

## 问题描述

使用 DeepSeek 模型（如 `deepseek-chat`）时，API 请求失败并返回以下错误：

```
openai.BadRequestError: Error code: 400 - {'error': {'message': 'Invalid max_tokens value, the valid range of max_tokens is [1, 8192]', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

## 根本原因

代码中 `max_tokens` 默认值为 `65536`，这对 Claude 模型有效，但 DeepSeek API 限制 `max_tokens` 必须在 `[1, 8192]` 范围内。

| 模型 | Max Tokens 设置 | API 允许范围 | 结果 |
|------|----------------|-------------|------|
| `claude-sonnet-4-5-20250929` | 65536 | 支持大值 | ✓ 正常工作 |
| `deepseek-chat` | 65536 | [1, 8192] | ✗ 报错 |

## 修复方案

在 `agentao/llm/client.py` 中添加了 `_get_max_tokens_for_model()` 方法，根据模型类型自动调整 `max_tokens` 值。

### 修改的文件

- `agentao/llm/client.py`

### 新增方法

```python
def _get_max_tokens_for_model(self, requested_max_tokens: Optional[int]) -> Optional[int]:
    """Return max_tokens value adjusted for the specific model/provider.

    Different models have different max_tokens limits. This method ensures
    the value stays within the allowed range for the current model.

    Args:
        requested_max_tokens: The requested max_tokens value (may be None)

    Returns:
        Adjusted max_tokens value or None to use model default
    """
    # Use env var or default if not specified
    max_tokens = requested_max_tokens if requested_max_tokens else self.max_tokens

    # DeepSeek models have a limit of 8192 for max_tokens
    if self.model and "deepseek" in self.model.lower():
        return min(max_tokens, 8192) if max_tokens else 8192

    # Default: no adjustment (Claude and most others support large values)
    return max_tokens
```

### 修改的方法

1. **`chat()` 方法**：在发送请求前调用 `_get_max_tokens_for_model()` 调整值
2. **`chat_stream()` 方法**：同样在发送请求前调用 `_get_max_tokens_for_model()` 调整值

## 影响范围

- 修复后，使用 DeepSeek 模型时 `max_tokens` 会自动从 `65536` 降低到 `8192`
- 对 Claude 等其他模型无影响，保持原有的大值支持
- 用户仍可通过 `LLM_MAX_TOKENS` 环境变量手动指定默认值

## 配置建议

如果主要使用 DeepSeek 模型，可以在 `.env` 中设置：

```bash
LLM_MAX_TOKENS=8192
```

## 测试

修复后，使用 `deepseek-chat` 模型可以正常发送请求并接收响应。
