# LLM 客户端基础设施文档

本文档包含各个 LLM 提供商的 API 文档信息和基础设施层实现细节。

## 文档结构

- [OpenAI API](./openai_api.md) - OpenAI API 文档和实现指南
- [Gemini API](./gemini_api.md) - Google Gemini API 文档和实现指南  
- [Anthropic API](./anthropic_api.md) - Anthropic Claude API 文档和实现指南
- [HTTP 客户端设计](./http_client_design.md) - HTTP 客户端架构设计
- [消息转换器](./message_converters.md) - 消息格式转换实现
- [配置管理](./config_management.md) - 配置发现和管理实现

## 实施计划

1. 搜集各提供商 API 文档
2. 设计统一的 HTTP 客户端接口
3. 实现消息转换器
4. 迁移配置管理功能
5. 更新核心层客户端实现