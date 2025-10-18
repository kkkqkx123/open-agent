# 基础架构与环境配置

本文档介绍了Modular Agent Framework的基础架构与环境配置模块的功能和使用方法。

## 概述

基础架构模块提供了以下核心功能：

1. **依赖注入容器** - 管理服务的注册、获取和生命周期
2. **配置加载服务** - 加载YAML配置文件，支持环境变量替换和热重载
3. **环境检查工具** - 检查Python版本、依赖包和系统资源
4. **架构分层检查** - 验证代码架构的分层规则和依赖关系

## 快速开始

### 1. 运行演示

```bash
python demo_infrastructure.py
```

这个脚本将演示所有基础架构组件的功能。

### 2. 环境检查

```bash
# 使用表格格式显示检查结果
python -m src.infrastructure.env_check_command

# 使用JSON格式输出到文件
python -m src.infrastructure.env_check_command --format json --output env_check.json
```

## 核心组件

### 依赖注入容器

依赖注入容器支持以下功能：

- 服务注册和获取
- 多环境绑定
- 生命周期管理（单例、瞬态、作用域）
- 自动依赖注入
- 循环依赖检测

```python
from src.infrastructure import DependencyContainer

# 创建容器
container = DependencyContainer()

# 注册服务
container.register(IService, ServiceImplementation)

# 获取服务
service = container.get(IService)

# 多环境支持
container.register(IService, DevService, "development")
container.register(IService, ProdService, "production")
container.set_environment("development")
service = container.get(IService)  # 获取DevService
```

### 配置加载服务

配置加载器支持：

- YAML文件加载
- 环境变量替换（`${VAR}` 和 `${VAR:default}`）
- 配置热重载
- 配置缓存
- 文件监听

```python
from src.infrastructure import YamlConfigLoader

# 创建加载器
loader = YamlConfigLoader("configs")

# 加载配置
config = loader.load("global.yaml")

# 环境变量替换
config = {
    "api_key": "${API_KEY}",
    "timeout": "${TIMEOUT:30}"
}
resolved = loader.resolve_env_vars(config)

# 热重载监听
def on_config_change(path, config):
    print(f"配置 {path} 已更新")

loader.watch_for_changes(on_config_change)
```

### 环境检查工具

环境检查器可以检查：

- Python版本
- 必需包
- 配置文件
- 系统资源（内存、磁盘空间）

```python
from src.infrastructure import EnvironmentChecker

# 创建检查器
checker = EnvironmentChecker()

# 执行检查
results = checker.check_dependencies()

# 生成报告
report = checker.generate_report()
print(f"通过: {report['summary']['pass']}")
print(f"错误: {report['summary']['error']}")
```

### 架构分层检查

架构检查器验证：

- 分层规则（领域层、基础设施层、应用层、表现层）
- 依赖关系
- 循环依赖

```python
from src.infrastructure import ArchitectureChecker

# 创建检查器
checker = ArchitectureChecker("src")

# 检查架构
results = checker.check_architecture()

# 生成依赖图
graph = checker.generate_dependency_graph()
```

## 配置文件结构

```
configs/
├── global.yaml              # 全局配置
├── llms/
│   └── _group.yaml          # LLM组配置
├── agents/
│   └── _group.yaml          # Agent组配置
└── tool-sets/
    └── _group.yaml          # 工具集组配置
```

### 全局配置示例

```yaml
log_level: "INFO"
log_outputs:
  - type: "console"
    level: "INFO"
    format: "text"
  - type: "file"
    level: "DEBUG"
    format: "json"
    path: "logs/agent.log"

secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
  - "\\w+@\\w+\\.\\w+"

env: "development"
debug: true
hot_reload: true
```

## 测试

### 运行单元测试

```bash
pytest tests/unit/infrastructure/
```

### 运行集成测试

```bash
pytest tests/integration/
```

### 运行所有测试

```bash
pytest
```

### 生成覆盖率报告

```bash
pytest --cov=src --cov-report=html
```

## 测试容器

测试容器为集成测试提供了隔离的测试环境：

```python
from src.infrastructure import TestContainer

# 使用测试容器
with TestContainer() as container:
    # 设置测试配置
    container.setup_basic_configs()
    
    # 获取服务
    config_loader = container.get_config_loader()
    config = config_loader.load("global.yaml")
    
    # 测试完成后自动清理
```

## 性能指标

基础架构模块满足以下性能要求：

- 配置加载时间 < 100ms（冷启动）
- 配置加载时间 < 10ms（缓存后）
- 依赖注入服务获取 < 1ms
- 日志记录延迟 < 5ms

## 故障排除

### 常见问题

1. **配置文件未找到**
   - 确保配置文件路径正确
   - 检查文件权限

2. **环境变量未设置**
   - 使用默认值语法：`${VAR:default}`
   - 检查环境变量名称

3. **架构违规**
   - 检查导入语句是否符合分层规则
   - 使用架构检查器验证

4. **循环依赖**
   - 检查服务之间的依赖关系
   - 考虑重构以避免循环依赖

## 扩展指南

### 添加新的配置类型

1. 在`configs/`目录下创建新的配置文件
2. 更新配置加载器以支持新类型
3. 添加相应的验证规则

### 自定义架构规则

1. 修改`ArchitectureChecker`中的`_define_layer_rules`方法
2. 添加新的层级或规则
3. 更新测试用例

### 扩展环境检查

1. 在`EnvironmentChecker`中添加新的检查方法
2. 更新`check_dependencies`方法
3. 添加相应的测试用例

## 下一步

基础架构模块完成后，可以继续实现：

1. 配置系统模块
2. 日志与指标模块
3. 模型集成模块
4. 工具系统模块

## 参考资料

- [依赖注入模式](https://en.wikipedia.org/wiki/Dependency_injection)
- [YAML配置格式](https://yaml.org/)
- [Python包管理](https://docs.python.org/3/library/)
- [架构分层模式](https://en.wikipedia.org/wiki/Layered_architecture)