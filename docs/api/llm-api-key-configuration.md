# LLM API密钥配置指南

## 概述

模块化代理框架支持通过环境变量配置LLM API密钥，确保敏感信息的安全性。本指南将详细介绍如何配置各种LLM提供商的API密钥。

## 支持的LLM提供商

框架当前支持以下LLM提供商：
- OpenAI
- Gemini
- Anthropic

## 配置方式

### 1. 环境变量配置（推荐）

#### 方法一：使用.env文件
1. 复制 `.env.example` 文件为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入您的实际API密钥：
   ```env
   # OpenAI API密钥
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # Gemini API密钥
   GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # Anthropic API密钥
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

#### 方法二：直接设置环境变量
在Linux/Mac系统中：
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GEMINI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

在Windows系统中：
```cmd
set OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
set GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
set ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. 配置文件引用

在LLM配置文件中（如 `configs/llms/provider/openai/openai-gpt4.yaml`），使用环境变量引用语法：

```yaml
model_type: openai
model_name: gpt-4
provider: openai
base_url: "https://api.openai.com/v1"
api_key: "${OPENAI_API_KEY}"  # 环境变量引用
```

## 安全性说明

1. **敏感信息保护**：所有API密钥都必须通过环境变量引用，禁止在配置文件中硬编码。
2. **.gitignore配置**：`.env` 文件已被添加到 `.gitignore` 中，不会被提交到版本控制系统。
3. **日志脱敏**：在日志中，API密钥会自动显示为 `***`，防止泄露。

## 配置示例

### OpenAI配置示例
```yaml
# configs/llms/provider/openai/openai-gpt4.yaml
model_type: openai
model_name: gpt-4
provider: openai
base_url: "https://api.openai.com/v1"
api_key: "${OPENAI_API_KEY}"
```

### Gemini配置示例
```yaml
# configs/llms/provider/gemini/gemini-pro.yaml
model_type: gemini
model_name: gemini-pro
provider: gemini
base_url: "https://generativelanguage.googleapis.com/v1"
api_key: "${GEMINI_API_KEY}"
```

### Anthropic配置示例
```yaml
# configs/llms/provider/anthropic/claude-sonnet.yaml
model_type: anthropic
model_name: claude-3-sonnet-20240229
provider: anthropic
base_url: "https://api.anthropic.com"
api_key: "${ANTHROPIC_API_KEY}"
```

## 验证配置

配置完成后，可以通过以下方式验证配置是否正确：

1. 运行环境检查命令：
   ```bash
   python -m src.infrastructure.env_check_command
   ```

2. 查看配置加载日志，确认API密钥已正确解析。

## 故障排除

### 常见问题

1. **API密钥未设置**
   - 错误信息：`Environment variable not found: OPENAI_API_KEY`
   - 解决方案：确保已正确设置环境变量或创建 `.env` 文件

2. **API密钥格式错误**
   - 错误信息：`401 Unauthorized`
   - 解决方案：检查API密钥是否正确，是否有额外的空格或字符

3. **权限不足**
   - 错误信息：`403 Forbidden`
   - 解决方案：检查API密钥是否有足够的权限访问所请求的资源

### 调试建议

1. 使用 `printenv` 命令（Linux/Mac）或 `echo %VAR_NAME%`（Windows）检查环境变量是否正确设置
2. 检查 `.env` 文件编码是否为UTF-8
3. 确认 `.env` 文件位于项目根目录

## 最佳实践

1. 始终使用 `.env` 文件管理环境变量，便于在不同环境间切换
2. 定期轮换API密钥，提高安全性
3. 为不同的环境（开发、测试、生产）使用不同的API密钥
4. 不要将 `.env` 文件提交到版本控制系统
5. 使用具有最小必要权限的API密钥