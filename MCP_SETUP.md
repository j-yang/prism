# OpenCode MCP Server 配置指南

## ✅ 当前配置状态

### 1. MCP Server 配置文件

**位置:** `~/.config/opencode/config.json`

**内容:**
```json
{
  "mcpServers": {
    "prism": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jimmyyang/projects/prism",
        "run",
        "prism-mcp"
      ],
      "env": {}
    }
  }
}
```

✅ 配置正确

### 2. 重启OpenCode

```bash
# 退出所有OpenCode实例
pkill -9 opencode

# 重新启动
opencode
```

### 3. 验证连接

在OpenCode中输入：
```
/mcp
```

应该能看到PRISM的tools。

## 可用的MCP Tools

- `extract_mock_shell` - 提取mock shell数据
- `validate_meta_definitions` - 验证metadata格式
- `save_meta_definitions` - 保存metadata到Excel
- `update_meta_definitions` - 更新metadata
- `get_als_fields` - 查询ALS字段
- `list_deliverables` - 列出deliverables
- `load_meta_to_db` - 加载到数据库

## 使用方法

### 方法1: 使用Agent Skill (推荐)

```
Generate metadata for this mock shell: examples/some_study/shell.docx
```

### 方法2: 手动调用Tools

```
Use extract_mock_shell tool on examples/some_study/shell.docx
```
