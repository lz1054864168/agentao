# Memory Management Quick Start

快速上手 Agentao 的 memory 管理功能。

## 5 分钟快速开始

### 1. 保存你的第一条记忆

**方式 A: 让 AI 帮你保存**

```
You: 请记住这个项目叫 Agentao，用 Python 写的，标签为 project 和 python
AI: [调用 save_memory 工具]
    Saved memory: project_name
```

**方式 B: 通过 API 直接保存**（仅供参考）
AI 会自动调用这个工具：
```python
save_memory(
    key="project_name",
    value="Agentao - Python CLI tool",
    tags=["project", "python"]
)
```

### 2. 查看所有记忆

```bash
/memory
```

输出：
```
Saved Memories (1 total):
  • project_name: Agentao - Python CLI tool
    Tags: project, python
    Saved: 2024-12-28T10:30:00.123456
```

### 3. 搜索记忆

**通过 CLI:**
```bash
/memory search python
```

**或者问 AI:**
```
You: 我之前保存了什么关于 python 的？
AI: [调用 search_memory 工具]
    找到 1 条记忆...
```

### 4. 按标签过滤

```bash
/memory tag project
```

### 5. 删除记忆

```bash
/memory delete project_name
```

或者：
```
You: 删除 project_name 这条记忆
AI: [调用 delete_memory]
```

## 常用场景

### 场景 1: 项目信息管理

```
# 保存项目信息
You: 记住这个项目用 uv 管理依赖
AI: ✓ 已保存

# 稍后查询
You: 这个项目怎么管理依赖的？
AI: [搜索记忆] 根据之前保存的信息，使用 uv 管理依赖。
```

### 场景 2: 用户偏好

```
# 保存偏好
You: 记住我喜欢用 spaces 而不是 tabs，标签 preference

# 查看所有偏好
/memory tag preference
```

### 场景 3: 临时笔记

```
# 保存临时信息
You: 记住 API endpoint 是 https://api.example.com，标签 temp

# 用完后删除
/memory delete api_endpoint
```

## 命令速查

```bash
# 查看
/memory              # 列出所有
/memory list         # 同上

# 搜索/过滤
/memory search <关键词>  # 搜索
/memory tag <标签名>     # 按标签过滤

# 管理
/memory delete <key>     # 删除单个
/memory clear            # 清空所有（需确认）
```

## 最佳实践

### ✅ 好的做法

1. **使用描述性的 key**
   ```
   ✓ user_python_version
   ✗ temp1
   ```

2. **合理使用标签**
   ```
   tags=["config", "production", "important"]
   ```

3. **区分临时和永久**
   ```
   临时信息: tags=["temp"]
   重要信息: tags=["important", "permanent"]
   ```

### ❌ 避免的做法

1. **不要用重复的 key**
   - 相同 key 会覆盖旧值

2. **不要保存敏感信息**
   - 密码、API key 等不要保存到 memory

3. **不要保存太长的内容**
   - memory 适合短文本，长内容考虑文件

## 下一步

- 📖 查看完整文档: [memory-management.md](./memory-management.md)
- 🧪 查看测试代码: [test_memory_management.py](../../tests/test_memory_management.py)
- 📝 查看更新日志: [2024-12-28-memory-management.md](../updates/2024-12-28-memory-management.md)

## 疑难解答

### Q: 记忆没有保存？

A: 检查 `.agentao_memory.json` 文件是否存在并可写。

### Q: 搜索找不到记忆？

A:
- 确认关键词拼写
- 尝试用标签: `/memory tag <tag>`
- 列出所有: `/memory list`

### Q: 如何备份记忆？

A:
```bash
# 复制 memory 文件
cp .agentao_memory.json memory_backup.json

# 恢复
cp memory_backup.json .agentao_memory.json
```

### Q: memory 文件可以手动编辑吗？

A: 可以，但要确保 JSON 格式正确：
```json
{
  "memories": [
    {
      "key": "example",
      "value": "Example value",
      "tags": ["tag1"],
      "timestamp": "2024-12-28T10:30:00.123456"
    }
  ]
}
```