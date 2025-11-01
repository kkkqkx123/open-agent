# 工具检验模块使用指南

## 概述

工具检验模块（Tool Validation Module）是Modular Agent Framework中的一个专门组件，用于验证定义的工具是否可以被工具管理器正确加载。该模块专注于验证加载过程，不涉及工具功能本身的单元测试。

## 核心功能

### 1. 配置验证
- 验证工具配置文件格式是否正确
- 检查必需字段是否存在
- 验证参数Schema是否符合规范
- 确保工具类型（builtin、native、mcp）有效

### 2. 加载验证
- 验证工具是否能够成功加载
- 检查工具属性是否完整
- 确认Schema获取功能正常

### 3. 类型特定验证
- **Builtin工具**：验证函数路径格式、模块导入、可调用性
- **Native工具**：验证API配置、认证方法、URL格式
- **MCP工具**：验证MCP服务器配置、连接参数

## 架构设计

### 核心组件

```
src/infrastructure/tools/validation/
├── __init__.py                          # 模块导出
├── interfaces.py                        # 验证器接口定义
├── models.py                           # 数据模型（ValidationResult等）
├── manager.py                          # 工具检验管理器
├── validators/                         # 验证器实现
│   ├── __init__.py
│   ├── base_validator.py               # 基础验证器
│   ├── config_validator.py             # 配置验证器
│   ├── loading_validator.py            # 加载验证器
│   ├── builtin_validator.py            # Builtin工具验证器
│   ├── native_validator.py             # Native工具验证器
│   └── mcp_validator.py                # MCP工具验证器
├── reporters/                          # 报告生成器
│   ├── __init__.py
│   ├── base_reporter.py                # 基础报告器
│   ├── text_reporter.py                # 文本报告器
│   └── json_reporter.py                # JSON报告器
└── cli/                                # 命令行工具
    ├── __init__.py
    └── validation_cli.py               # 命令行入口
```

### 数据模型

- **ValidationResult**: 验证结果，包含工具名称、类型、状态和问题列表
- **ValidationStatus**: 验证状态枚举（SUCCESS、WARNING、ERROR）
- **ValidationIssue**: 验证问题，包含级别、消息、详细信息和建议

## 使用方法

### 1. 命令行使用

#### 验证所有工具
```bash
python -m src.infrastructure.tools.validation.cli.validation_cli
```

#### 验证单个工具
```bash
python -m src.infrastructure.tools.validation.cli.validation_cli --tool hash_convert
```

#### 使用JSON格式输出
```bash
python -m src.infrastructure.tools.validation.cli.validation_cli --format json
```

#### 详细输出模式
```bash
python -m src.infrastructure.tools.validation.cli.validation_cli --verbose
```

#### 指定配置目录
```bash
python -m src.infrastructure.tools.validation.cli.validation_cli --config-dir tools
```

### 2. 编程接口使用

#### 基本验证示例
```python
from src.infrastructure.container import DependencyContainer
from src.infrastructure.tools.validation import ToolValidationManager

def validate_single_tool():
    """验证单个工具"""
    # 创建依赖容器
    container = DependencyContainer()
    
    # 获取服务
    config_loader = container.get_config_loader()
    logger = container.get_logger()
    tool_manager = container.get_tool_manager()
    
    # 创建检验管理器
    validation_manager = ToolValidationManager(config_loader, logger, tool_manager)
    
    # 验证Hash转换工具
    results = validation_manager.validate_tool(
        "hash_convert", 
        "tools/hash_convert.yaml"
    )
    
    # 生成报告
    report = validation_manager.generate_report(
        {"hash_convert": results}, 
        format="text"
    )
    print(report)

def validate_all_tools():
    """验证所有工具"""
    container = DependencyContainer()
    config_loader = container.get_config_loader()
    logger = container.get_logger()
    tool_manager = container.get_tool_manager()
    
    # 创建检验管理器
    validation_manager = ToolValidationManager(config_loader, logger, tool_manager)
    
    # 验证所有工具
    all_results = validation_manager.validate_all_tools("tools")
    
    # 生成详细报告
    report = validation_manager.generate_report(all_results, format="text")
    print(report)
```

## 验证结果解读

### 状态说明
- **✓ (SUCCESS)**: 验证通过，工具配置和加载正常
- **⚠ (WARNING)**: 存在警告，但不影响基本功能
- **✗ (ERROR)**: 存在错误，工具无法正常工作

### 常见问题及解决方案

#### 1. 配置文件加载失败
- **问题**: `配置文件加载失败: Configuration file not found`
- **解决方案**: 检查配置文件路径是否正确，确保文件存在

#### 2. 缺少必需字段
- **问题**: `缺少必需字段: name`
- **解决方案**: 在工具配置文件中添加必需字段

#### 3. 函数路径错误
- **问题**: `无效的函数路径: invalid.module:function`
- **解决方案**: 检查函数路径格式，应为 `module.submodule:function_name`

#### 4. 工具加载失败
- **问题**: `工具加载失败: 工具不存在`
- **解决方案**: 检查工具是否正确注册，配置是否正确

## 集成与扩展

### 依赖注入集成
工具检验模块已集成到依赖注入系统中，可以通过以下方式获取服务：

```python
from src.infrastructure.tools.validation.interfaces import IToolValidator
from src.infrastructure.tools.validation.di_config import ToolValidationModule

# 注册工具检验服务
ToolValidationModule.register_services(container)
```

### 扩展新验证器
要添加新的工具类型验证器，需要：

1. 实现 `IToolValidator` 接口
2. 在 `ToolValidationManager` 中注册验证器
3. 在配置验证器中添加对新类型的处理

## 最佳实践

### 1. 开发阶段验证
在开发新工具时，使用工具检验模块验证配置是否正确：

```bash
python -m src.infrastructure.tools.validation.cli.validation_cli --tool your_new_tool
```

### 2. CI/CD 集成
在持续集成流程中添加工具验证步骤，确保所有工具配置正确：

```bash
# 验证所有工具
python -m src.infrastructure.tools.validation.cli.validation_cli --format json
```

### 3. 定期验证
定期运行工具验证，确保工具配置没有因代码变更而损坏。

## 优势

### 1. 提高开发效率
- 快速发现问题：在开发阶段发现配置错误
- 减少调试时间：提供详细的错误信息和修复建议
- 自动化验证：集成到开发流程中

### 2. 提高代码质量
- 标准化验证：统一的验证标准和流程
- 质量保证：确保所有工具都能正确加载

### 3. 易于维护
- 模块化设计：易于扩展新验证器
- 清晰接口：易于理解和维护
- 详细文档：完整的API文档和使用示例

## 总结

工具检验模块为Modular Agent Framework提供了一个强大、灵活的工具验证系统，具有以下特点：

1. **专注加载验证**：严格遵循需求，专注于工具加载过程的验证
2. **全面覆盖**：支持所有工具类型（Builtin、Native、MCP）的验证
3. **详细报告**：提供清晰的错误信息和修复建议
4. **易于使用**：简单的API和命令行工具
5. **易于扩展**：模块化设计支持新验证器和报告器

该模块将显著提高工具开发的可靠性和效率，确保所有工具都能在系统中正确加载和运行。