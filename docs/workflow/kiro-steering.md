# Steering（引导配置）

## 什么是 Steering？
Steering 通过存放在 `.kiro/steering/` 目录下的 markdown 文件，为 Kiro 提供对你项目的持久知识。无需每次聊天重复解释代码规范，Steering 文件能让 Kiro 持续遵循你设定的模式、库和标准。

## 主要优势
- 代码生成一致性：每个组件、API 端点或测试都遵循团队既定规范和约定。
- 减少重复说明：不必在每次对话中重复介绍项目标准，Kiro 会记住偏好。
- 团队统一：新成员和资深开发都基于同样的标准协作。
- 项目知识可扩展：文档随代码库成长，捕捉决策和模式，适应项目演进。

## 默认 Steering 文件
Kiro 自动创建三个基础文件，奠定核心项目上下文，默认包含于每次交互：

### 产品概述 (product.md)
定义产品目标、用户群、核心功能和业务目标，帮助 Kiro 理解技术决策背后的“为什么”，给出符合产品目标的方案。

### 技术栈 (tech.md)
记录选用的框架、库、开发工具及技术限制，Kiro 会优先使用既定技术栈。

### 项目结构 (structure.md)
描述文件组织、命名规范、导入方式和架构决策，确保生成的代码能无缝融入现有代码库。

## 创建自定义 Steering 文件
扩展 Kiro 的理解，定制专属指引：
1. 在 Kiro 面板中进入 Steering 部分。
2. 点击 + 新建一个 .md 文件。
3. 命名描述性文件名（例如 api-standards.md）。
4. 使用标准 markdown 语法书写指引。
5. 用自然语言描述需求，点击 Refine 按钮由 Kiro 格式化内容。

## 包含模式（Inclusion Modes）
在文件顶部添加 YAML 格式 front matter（用三条短横线包裹），配置加载时机：

### 始终包含（默认）
```yaml
---
inclusion: always
---
```
自动加载到所有 Kiro 交互中，适用于项目核心标准、技术偏好、安全策略和通用编码规范。

### 条件包含
```yaml
---
inclusion: fileMatch
fileMatchPattern: "components/**/*.tsx"
---
```
仅处理匹配指定模式的文件时自动包含，保持上下文相关。

#### 常见模式示例
- "*.tsx" — React 组件和 JSX 文件
- "app/api/**/*" — API 路由和后端逻辑
- "**/*.test.*" — 测试文件及工具
- "src/components/**/*" — 组件相关指引
- "*.md" — 文档文件

适用于组件规范、API 设计、测试策略或特定文件类型的部署流程等领域标准。

### 手动包含
```yaml
---
inclusion: manual
---
```
不自动加载，需在聊天中用 `#steering-file-name` 引用生效（示例：#troubleshooting-guide 或 #performance-optimization）。

适合专门的工作流、故障排查、迁移流程或偶尔需要的重上下文文档。

## 文件引用
通过链接项目实际文件保持 Steering 内容最新，格式：`#[[file:<relative_file_name>]]`

### 示例
- API 规范：#[[file:api/openapi.yaml]]
- 组件模式：#[[file:components/ui/button.tsx]]
- 配置模板：#[[file:.env.example]]

## 最佳实践
- 保持文件聚焦：每个文件专注一个领域（如 API 设计、测试或部署流程）。
- 使用清晰文件名：api-rest-conventions.md（REST API 标准）、testing-unit-patterns.md（单元测试方案）等。
- 包含上下文说明：解释制定标准的原因，而非仅罗列内容。
- 提供示例：用代码片段和前后对比展示标准。
- 安全第一：不包含 API 密钥、密码等敏感信息。
- 定期维护：迭代计划和架构调整时复查，重构后测试文件引用有效性，视同代码变更需经审查。

## 常见 Steering 文件策略
- API 标准 (api-standards.md)：定义 REST 规范、错误响应格式、认证流程、版本管理，包含接口命名、HTTP 状态码用法及请求/响应示例。
- 测试方案 (testing-standards.md)：建立单元测试模式、集成测试策略、模拟方式和覆盖率目标，记录首选测试库、断言风格和测试文件组织。
- 代码风格 (code-conventions.md)：规定命名规范、文件组织、导入顺序和架构决策，包含示例代码结构、组件模式及应避免的反模式。
- 安全指南 (security-policies.md)：记录认证要求、数据验证规则、输入清理标准和漏洞预防措施，包含应用相关的安全编码实践。
- 部署流程 (deployment-workflow.md)：描述构建流程、环境配置、部署步骤和回滚策略，包含 CI/CD 管道细节及环境特殊需求。

> 自定义 Steering 文件存储于 .kiro/steering/，创建后立即在所有 Kiro 交互中生效。
