# 文件移动列表

## 1. 移动 tools 相关代码 (从 src/domain/tools 到 src/core/tools)

```bash
# 核心文件
mv src/domain/tools/base.py src/core/tools/
mv src/domain/tools/factory.py src/core/tools/
mv src/domain/tools/interfaces.py src/core/tools/

# 工具类型
mv src/domain/tools/types/builtin_tool.py src/core/tools/types/
mv src/domain/tools/types/mcp_tool.py src/core/tools/types/
mv src/domain/tools/types/native_tool.py src/core/tools/types/

# 内置工具
mv src/domain/tools/types/builtin/calculator.py src/core/tools/types/builtin/
mv src/domain/tools/types/builtin/hash_convert.py src/core/tools/types/builtin/
mv src/domain/tools/types/builtin/sequentialthinking.py src/core/tools/types/builtin/
mv src/domain/tools/types/builtin/time_tool.py src/core/tools/types/builtin/

# 原生工具
mv src/domain/tools/types/native/duckduckgo_search.py src/core/tools/types/native/
mv src/domain/tools/types/native/fetch.py src/core/tools/types/native/
```

## 2. 移动 tools 相关代码 (从 src/infrastructure/tools 到 src/core/tools)

```bash
# 核心文件
mv src/infrastructure/tools/config.py src/core/tools/
mv src/infrastructure/tools/executor.py src/core/tools/
mv src/infrastructure/tools/formatter.py src/core/tools/
mv src/infrastructure/tools/loaders.py src/core/tools/
mv src/infrastructure/tools/manager.py src/core/tools/

# 工具验证 (移动到 services/tools)
mv src/infrastructure/tools/validation src/services/tools/

# 工具工具
mv src/infrastructure/tools/utils/schema_generator.py src/core/tools/utils/
mv src/infrastructure/tools/utils/validator.py src/core/tools/utils/
```

## 3. 移动 llm 相关代码 (从 src/infrastructure/llm 到 src/core/llm)

```bash
# 核心文件
mv src/infrastructure/llm/interfaces.py src/core/llm/
mv src/infrastructure/llm/models.py src/core/llm/
mv src/infrastructure/llm/exceptions.py src/core/llm/
mv src/infrastructure/llm/factory.py src/core/llm/
mv src/infrastructure/llm/config.py src/core/llm/
mv src/infrastructure/llm/config_manager.py src/core/llm/
mv src/infrastructure/llm/token_counter.py src/core/llm/

# 客户端
mv src/infrastructure/llm/clients/* src/core/llm/clients/

# 缓存
mv src/infrastructure/llm/cache/* src/core/llm/cache/

# 工具
mv src/infrastructure/llm/utils/* src/core/llm/utils/

# 包装器
mv src/infrastructure/llm/wrappers src/core/llm/

# 降级系统 (移动到 services/llm)
mv src/infrastructure/llm/fallback_system src/services/llm/
mv src/infrastructure/llm/enhanced_fallback_manager.py src/services/llm/
mv src/infrastructure/llm/fallback_client.py src/services/llm/

# 任务组和轮询池 (移动到 services/llm)
mv src/infrastructure/llm/task_group_manager.py src/services/llm/
mv src/infrastructure/llm/polling_pool.py src/services/llm/

# 其他组件
mv src/infrastructure/llm/concurrency_controller.py src/services/llm/
mv src/infrastructure/llm/error_handler.py src/services/llm/
mv src/infrastructure/llm/hooks.py src/services/llm/

# 内存管理
mv src/infrastructure/llm/memory src/services/llm/

# 连接池
mv src/infrastructure/llm/pool src/services/llm/

# 重试机制
mv src/infrastructure/llm/retry src/services/llm/

# Token计算器
mv src/infrastructure/llm/token_calculators src/services/llm/

# Token解析器
mv src/infrastructure/llm/token_parsers src/services/llm/

# 验证
mv src/infrastructure/llm/validation src/services/llm/

# 插件
mv src/infrastructure/llm/plugins src/services/llm/

# 前端接口
mv src/infrastructure/llm/frontend_interface.py src/services/llm/

# DI配置
mv src/infrastructure/llm/di_config.py src/services/llm/
```

## 4. 创建必要的目录结构

```bash
# 创建缺失的目录
mkdir -p src/core/tools/types/builtin
mkdir -p src/core/tools/types/native
mkdir -p src/core/llm/clients/openai
mkdir -p src/services/llm/fallback_system
mkdir -p src/services/llm/memory
mkdir -p src/services/llm/pool
mkdir -p src/services/llm/retry
mkdir -p src/services/llm/token_calculators
mkdir -p src/services/llm/token_parsers
mkdir -p src/services/llm/validation
mkdir -p src/services/llm/plugins
mkdir -p src/services/tools/validation/cli
mkdir -p src/services/tools/validation/reporters
mkdir -p src/services/tools/validation/validators
```

## 5. 创建缺失的__init__.py文件

```bash
# 为新创建的目录添加__init__.py文件
touch src/core/tools/types/builtin/__init__.py
touch src/core/tools/types/native/__init__.py
touch src/core/llm/clients/openai/__init__.py
touch src/core/llm/wrappers/__init__.py
touch src/services/llm/fallback_system/__init__.py
touch src/services/llm/memory/__init__.py
touch src/services/llm/pool/__init__.py
touch src/services/llm/retry/__init__.py
touch src/services/llm/token_calculators/__init__.py
touch src/services/llm/token_parsers/__init__.py
touch src/services/llm/validation/__init__.py
touch src/services/llm/plugins/__init__.py
touch src/services/tools/validation/__init__.py
touch src/services/tools/validation/cli/__init__.py
touch src/services/tools/validation/reporters/__init__.py
touch src/services/tools/validation/validators/__init__.py
```

## 注意事项

1. **执行顺序**：请按照上述顺序执行，先移动核心文件，再移动子目录
2. **冲突处理**：如果目标位置已有同名文件，请先检查内容，决定是覆盖还是合并
3. **导入路径**：移动完成后，需要更新所有文件中的导入路径
4. **备份**：建议在执行前先备份整个项目

## Windows PowerShell 替代命令

如果您在Windows环境下使用PowerShell，请使用以下命令替代：

```powershell
# 移动文件
Move-Item -Path "src\domain\tools\base.py" -Destination "src\core\tools\"
Move-Item -Path "src\domain\tools\factory.py" -Destination "src\core\tools\"
Move-Item -Path "src\domain\tools\interfaces.py" -Destination "src\core\tools\"

# 移动目录
Move-Item -Path "src\domain\tools\types\builtin_tool.py" -Destination "src\core\tools\types\"
Move-Item -Path "src\domain\tools\types\mcp_tool.py" -Destination "src\core\tools\types\"
Move-Item -Path "src\domain\tools\types\native_tool.py" -Destination "src\core\tools\types\"

# 创建目录
New-Item -Path "src\core\tools\types\builtin" -ItemType Directory -Force
New-Item -Path "src\core\tools\types\native" -ItemType Directory -Force

# 创建文件
New-Item -Path "src\core\tools\types\builtin\__init__.py" -ItemType File -Force
New-Item -Path "src\core\tools\types\native\__init__.py" -ItemType File -Force
```

完成文件移动后，请告诉我，我将帮助您更新导入路径和重构降级系统。