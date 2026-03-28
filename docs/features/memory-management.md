# Memory Management

Agentao 提供完整的 memory 管理功能，支持保存、搜索、过滤、删除和清空记忆。

## 功能概览

### CLI 命令

所有 memory 管理都可以通过 `/memory` 命令及其子命令完成：

```bash
# 列出所有记忆
/memory
/memory list

# 搜索记忆（按关键词）
/memory search <query>

# 按标签过滤
/memory tag <tag_name>

# 删除指定记忆
/memory delete <key>

# 清空所有记忆（需要确认）
/memory clear
```

### LLM 工具

AI 助手可以自动使用以下工具管理 memory：

- `save_memory` - 保存/更新记忆
- `search_memory` - 搜索记忆
- `delete_memory` - 删除指定记忆
- `clear_all_memories` - 清空所有记忆
- `filter_memory_by_tag` - 按标签过滤

## 使用示例

### 1. 保存记忆

用户可以让 AI 保存信息：

```
You: 请记住，我喜欢用 Python 3.11+，标签为 preference 和 python
Assistant: [调用 save_memory 工具]
```

或者通过 CLI 命令（需要先保存）：
```bash
/memory list  # 查看已保存的记忆
```

### 2. 搜索记忆

```bash
# 使用 CLI 搜索
/memory search python

# 输出：
Found 1 memory(ies) matching 'python':
  • user_preference: Use Python 3.11+
    Tags: preference, python
    Saved: 2024-12-28T10:30:00.123456
```

或者询问 AI：
```
You: 我之前保存过什么关于 python 的信息？
Assistant: [调用 search_memory 工具]
```

### 3. 按标签过滤

```bash
# 查看所有带 "important" 标签的记忆
/memory tag important
```

### 4. 删除记忆

```bash
# 删除指定的记忆
/memory delete project_name

# 输出：
Successfully deleted memory: project_name
```

或者让 AI 处理：
```
You: 删除 project_name 这条记忆
Assistant: [调用 delete_memory 工具]
```

### 5. 清空所有记忆

```bash
# 会要求确认
/memory clear

# 确认提示：
⚠️  Are you sure you want to delete ALL memories? This cannot be undone. [y/N]:
```

## 记忆数据结构

每条记忆包含以下字段：

```json
{
  "key": "unique_identifier",
  "value": "The actual information to remember",
  "tags": ["tag1", "tag2"],
  "timestamp": "2024-12-28T10:30:00.123456"
}
```

- **key**: 唯一标识符，用于更新或删除
- **value**: 实际内容
- **tags**: 标签数组，用于分类和过滤
- **timestamp**: ISO 格式的保存时间

## 存储位置

记忆存储在 `.agentao_memory.json` 文件中（已添加到 `.gitignore`），格式：

```json
{
  "memories": [
    {
      "key": "project_name",
      "value": "Agentao",
      "tags": ["project", "important"],
      "timestamp": "2024-12-28T10:30:00.123456"
    }
  ]
}
```

## 最佳实践

### 1. 使用描述性的 key
```python
# ✅ 好
save_memory(key="user_python_version", value="3.11+")

# ❌ 不好
save_memory(key="temp1", value="3.11+")
```

### 2. 合理使用标签
```python
# 使用标签分类
save_memory(
    key="api_endpoint",
    value="https://api.example.com",
    tags=["config", "api", "production"]
)
```

### 3. 定期清理
```bash
# 搜索不需要的记忆
/memory search old

# 删除过时的记忆
/memory delete old_config
```

## 工作流示例

### 项目配置管理

```
1. 保存项目信息
   You: 请记住这个项目叫 Agentao，是一个 Python CLI 工具
   AI: [保存到 memory]

2. 保存开发偏好
   You: 记住我们使用 uv 管理依赖
   AI: [保存到 memory]

3. 稍后查询
   You: 这个项目用什么管理依赖？
   AI: [搜索 memory] 根据记忆，你们使用 uv 管理依赖。
```

### 用户偏好追踪

```
1. 保存偏好
   /memory list  # 查看当前偏好

2. 按标签查看
   /memory tag preference  # 只看偏好相关

3. 更新偏好（使用相同的 key）
   You: 更新偏好，我现在用 Python 3.12
   AI: [调用 save_memory 自动更新]
```

## 注意事项

1. **自动更新**: 使用相同的 key 保存会自动更新现有记忆
2. **不可恢复**: 删除和清空操作不可恢复，请谨慎使用
3. **大小写敏感**: key 是大小写敏感的，但搜索不是
4. **并发安全**: 目前不支持多进程并发写入

## API 参考

### SaveMemoryTool

```python
save_memory(
    key: str,        # 必需：唯一标识符
    value: str,      # 必需：要保存的内容
    tags: list = []  # 可选：标签列表
) -> str
```

### SearchMemoryTool

```python
search_memory(
    query: str  # 搜索关键词（匹配 key 和 tags）
) -> str
```

### FilterMemoryByTagTool

```python
filter_memory_by_tag(
    tag: str  # 要过滤的标签名
) -> str
```

### DeleteMemoryTool

```python
delete_memory(
    key: str  # 要删除的记忆的 key
) -> str
```

### ClearMemoryTool

```python
clear_all_memories() -> str  # 清空所有记忆
```

## 故障排除

### 记忆文件损坏

如果 `.agentao_memory.json` 文件损坏：

```bash
# 删除文件，会自动重新创建
rm .agentao_memory.json

# 重启 Agentao
./run.sh
```

### 搜索没有结果

- 检查关键词拼写
- 尝试使用标签搜索: `/memory tag <tag>`
- 列出所有记忆检查: `/memory list`

### 无法删除记忆

- 确保 key 完全匹配（大小写敏感）
- 先列出所有记忆查看准确的 key: `/memory list`
