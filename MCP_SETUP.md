# PRISM MCP Server 配置完成

## ✅ 配置状态

**OpenCode配置文件：** `~/.config/opencode/config.json`

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
      ]
    }
  }
}
```

## ✅ 可用的MCP Tools (8个)

| Tool | 功能 | 需要LLM |
|------|------|---------|
| `list_deliverables` | 列出mock shell中的deliverables | ❌ |
| `lookup_als_field` | 查询ALS字段 | ❌ |
| `get_bronze_schema` | 获取Bronze层表结构 | ❌ |
| `get_meta_variables` | 获取meta.silver_dictionary变量 | ❌ |
| `generate_meta` | 生成元数据 | ✅ DeepSeek |
| `load_meta` | 加载元数据到DuckDB | ❌ |
| `generate_silver` | 生成Silver层Polars代码 | ✅ DeepSeek |
| `generate_gold` | 生成Gold层统计代码 | ✅ DeepSeek |

## ✅ 测试结果

```
✅ list_deliverables - 找到34个deliverables
✅ lookup_als_field - 查询功能正常
✅ 所有工具测试通过
```

## 🚀 如何使用

### 1. 重启OpenCode

如果OpenCode正在运行，需要重启以加载新的MCP Server：

```bash
# 退出当前OpenCode会话
exit

# 重新启动
opencode
```

### 2. 在OpenCode中使用

**示例1：列出deliverables**
```
User: 帮我列出examples/some_study的deliverables

OpenCode: [调用 list_deliverables tool]
         Found 34 deliverables:
         - 14.1.1 CAR-T Treatment Summary
         - 14.1.2.1 Baseline Characteristics (IIM Cohort)
         ...
```

**示例2：查询ALS字段**
```
User: 查询ALS里DM域的age相关字段

OpenCode: [调用 lookup_als_field tool]
         Found 5 matching fields:
         - DM.AGE
         - DM.AGEU
         ...
```

**示例3：生成meta**
```
User: 生成some_study的meta

OpenCode: [调用 generate_meta tool]
         生成了45个变量
         输出：examples/some_study/generated_meta.xlsx
         
         需要加载到数据库吗？
```

### 3. 验证MCP已加载

在OpenCode中输入：
```
/mcp
```

应该能看到：
```
MCP Servers:
  ✓ prism (connected)
    Tools: generate_meta, load_meta, generate_silver, ...
```

## 📋 前提条件

- ✅ uv已安装
- ✅ 项目依赖已安装 (uv sync)
- ✅ DEEPSEEK_API_KEY已设置（在.env中）
- ✅ Python 3.12+
- ✅ OpenCode已安装

## 🔧 配置说明

**为什么用uv运行？**
- 确保使用正确的虚拟环境
- 自动管理依赖
- 开发时最方便

**生产环境可选方案：**
1. **PyPI发布后**：`"command": "prism-mcp"` （不需要uv）
2. **Docker**：`"command": "docker", "args": ["run", "-i", "prism-mcp"]`

## 🎯 下一步

1. **重启OpenCode** - 加载新的MCP Server
2. **测试对话** - 在OpenCode中试用PRISM tools
3. **提供反馈** - 根据使用体验调整

## 📚 相关文档

- [MCP_GUIDE.md](MCP_GUIDE.md) - MCP使用指南
- [README.md](README.md) - 项目概览
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
