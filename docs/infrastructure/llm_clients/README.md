# LLM 客户端基础设施文档

本文档包含各个 LLM 提供商的 API 文档信息、参数参考和基础设施层实现细节。

## 文档结构

### API 文档和实现指南
- [OpenAI API](./openai_api.md) - OpenAI API 文档和实现指南
- [Gemini API](./gemini_api.md) - Google Gemini API 文档和实现指南
- [Anthropic API](./anthropic_api.md) - Anthropic Claude API 文档和实现指南

### 参数完整参考
- [OpenAI API 参数](./openai_api_parameters.md) - OpenAI Chat Completions & Responses API 参数完整参考
- [OpenAI Responses API](./openai_responses_api.md) - OpenAI 新一代 Responses API (GPT-5) 详细文档
- [Gemini API 参数](./gemini_api_parameters.md) - Google Gemini API 参数完整参考
- [Anthropic API 参数](./anthropic_api_parameters.md) - Anthropic Claude Messages API 参数完整参考
- [API 参数对比](./api_parameters_comparison.md) - 四大 LLM API 端点参数对比和统一抽象设计

### 架构设计和实现
- [HTTP 客户端设计](./http_client_design.md) - HTTP 客户端架构设计
- [消息转换器](./message_converters.md) - 消息格式转换实现
- [配置管理](./config_management.md) - 配置发现和管理实现

## 实施计划

1. ✅ 搜集各提供商 API 文档
2. ✅ 分析和整理 API 参数
3. ✅ 创建参数对比和统一抽象设计
4. ✅ 添加 OpenAI Responses API 详细文档
5. 🔄 设计统一的 HTTP 客户端接口
6. ⏳ 实现消息转换器
7. ⏳ 迁移配置管理功能
8. ⏳ 更新核心层客户端实现

## 核心发现

### 参数统一性
- **通用参数**：`model`, `max_tokens`, `stream` 等在四个端点都有对应
- **格式差异**：消息格式、系统提示、工具定义等存在显著差异
- **API 演进**：OpenAI 提供了两代 API（Chat Completions 和 Responses），各有优势
- **独有功能**：各平台都有独特的参数和功能（如 Responses API 的链式思考，Gemini 的 `thinking_config`）

### 基础设施层设计要点
1. **统一抽象**：创建通用的配置和响应格式
2. **参数转换**：实现平台特定的参数转换器
3. **API 适配**：同时支持传统和新一代 API
4. **多模态支持**：统一处理图像、音频等多模态输入
5. **工具使用**：抽象工具定义和调用流程
6. **流式处理**：统一流式响应处理机制
7. **推理控制**：支持不同平台的推理参数

### 迁移策略
1. **渐进式迁移**：分阶段实施，降低风险
2. **向后兼容**：使用适配器保持兼容性
3. **API 选择**：根据需求选择合适的 API 端点
4. **测试驱动**：每个组件都要有完整测试
5. **文档同步**：及时更新架构文档

## 下一步行动

1. **实现 HTTP 客户端基类**
2. **创建参数转换器（支持 4 个端点）**
3. **实现消息格式转换**
4. **添加工具使用支持**
5. **集成测试和验证**
6. **API 端点路由和选择逻辑**