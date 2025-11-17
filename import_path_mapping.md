# 导入路径映射表

## Tools模块导入路径映射

### 旧路径 → 新路径

#### 核心接口和基类
- `src.domain.tools.interfaces` → `src.core.tools.interfaces`
- `src.domain.tools.base` → `src.core.tools.base`
- `src.domain.tools.factory` → `src.core.tools.factory`
- `src.infrastructure.tools.interfaces` → `src.core.tools.interfaces` (合并)
- `src.infrastructure.tools.manager` → `src.core.tools.manager`
- `src.infrastructure.tools.config` → `src.core.tools.config`
- `src.infrastructure.tools.loaders` → `src.core.tools.loaders`

#### 工具类型
- `src.domain.tools.types.builtin_tool` → `src.core.tools.types.native_tool` (重命名)
- `src.domain.tools.types.native_tool` → `src.core.tools.types.rest_tool` (重命名)
- `src.domain.tools.types.mcp_tool` → `src.core.tools.types.mcp_tool`
- `src.domain.tools.types.builtin.*` → `src.core.tools.types.native.*`
- `src.domain.tools.types.native.*` → `src.core.tools.types.rest.*`

#### 工具实现
- `src.domain.tools.types.builtin.calculator` → `src.core.tools.types.native.calculator`
- `src.domain.tools.types.builtin.hash_convert` → `src.core.tools.types.native.hash_convert`
- `src.domain.tools.types.builtin.sequentialthinking` → `src.core.tools.types.native.sequentialthinking`
- `src.domain.tools.types.builtin.time_tool` → `src.core.tools.types.native.time_tool`
- `src.domain.tools.types.native.duckduckgo_search` → `src.core.tools.types.rest.duckduckgo_search`
- `src.domain.tools.types.native.fetch` → `src.core.tools.types.rest.fetch`

#### 工具服务
- `src.infrastructure.tools.validation` → `src.services.tools.validation`
- `src.infrastructure.tools.utils` → `src.core.tools.utils`

## LLM模块导入路径映射

### 核心接口和基类
- `src.infrastructure.llm.interfaces` → `src.core.llm.interfaces`
- `src.infrastructure.llm.models` → `src.core.llm.models`
- `src.infrastructure.llm.exceptions` → `src.core.llm.exceptions`
- `src.infrastructure.llm.factory` → `src.core.llm.factory`
- `src.infrastructure.llm.config` → `src.core.llm.config`
- `src.infrastructure.llm.config_manager` → `src.core.llm.config_manager`
- `src.infrastructure.llm.token_counter` → `src.core.llm.token_counter`

#### LLM客户端
- `src.infrastructure.llm.clients.*` → `src.core.llm.clients.*`

#### LLM缓存
- `src.infrastructure.llm.cache.*` → `src.core.llm.cache.*`

#### LLM工具
- `src.infrastructure.llm.utils.*` → `src.core.llm.utils.*`

#### LLM包装器
- `src.infrastructure.llm.wrappers.*` → `src.core.llm.wrappers.*`

#### LLM服务
- `src.infrastructure.llm.fallback_system` → `src.services.llm.fallback_system`
- `src.infrastructure.llm.enhanced_fallback_manager` → `src.services.llm.enhanced_fallback_manager`
- `src.infrastructure.llm.task_group_manager` → `src.services.llm.task_group_manager`
- `src.infrastructure.llm.polling_pool` → `src.services.llm.polling_pool`
- `src.infrastructure.llm.concurrency_controller` → `src.services.llm.concurrency_controller`
- `src.infrastructure.llm.error_handler` → `src.services.llm.error_handler`
- `src.infrastructure.llm.hooks` → `src.services.llm.hooks`
- `src.infrastructure.llm.memory` → `src.services.llm.memory`
- `src.infrastructure.llm.pool` → `src.services.llm.pool`
- `src.infrastructure.llm.retry` → `src.services.llm.retry`
- `src.infrastructure.llm.token_calculators` → `src.services.llm.token_calculators`
- `src.infrastructure.llm.token_parsers` → `src.services.llm.token_parsers`
- `src.infrastructure.llm.validation` → `src.services.llm.validation`
- `src.infrastructure.llm.plugins` → `src.services.llm.plugins`
- `src.infrastructure.llm.frontend_interface` → `src.services.llm.frontend_interface`
- `src.infrastructure.llm.di_config` → `src.services.llm.di_config`

## 通用模块导入路径映射

### 配置系统
- `src.infrastructure.config.*` → `src.core.config.*`

### 异常处理
- `src.infrastructure.exceptions` → `src.core.common.exceptions`

### 日志系统
- `src.infrastructure.logger.*` → `src.core.common.logger`

### 异步工具
- `src.infrastructure.async_utils.*` → `src.core.common.async_utils`

## 更新策略

1. **批量替换**: 使用IDE的批量替换功能，按照映射表进行替换
2. **验证导入**: 替换后验证所有导入是否正确
3. **测试运行**: 确保所有模块能够正常导入和运行
4. **逐步验证**: 从核心模块开始，逐步验证整个系统

## 注意事项

1. **相对导入**: 保持相对导入的正确性
2. **循环依赖**: 避免引入新的循环依赖
3. **类型注解**: 更新类型注解中的导入路径
4. **配置文件**: 更新配置文件中的类路径引用
5. **文档字符串**: 更新文档中的示例代码