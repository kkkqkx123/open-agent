# 扁平化架构迁移策略和实施步骤

## 1. 迁移策略概述

### 1.1 迁移目标

1. **简化架构**：将四层架构简化为两层（Core + Services）
2. **功能内聚**：将相关功能集中到同一模块
3. **保持兼容**：确保所有现有功能正常工作
4. **平滑过渡**：最小化迁移过程中的业务中断

### 1.2 迁移原则

1. **渐进式迁移**：分阶段进行，降低风险
2. **向后兼容**：提供兼容层，支持旧代码
3. **充分测试**：每个阶段都要进行全面测试
4. **快速回滚**：准备快速回滚机制

### 1.3 迁移范围

- **核心模块**：tools、llm、config
- **配置文件**：重组配置结构
- **依赖关系**：更新模块间依赖
- **启动流程**：调整应用程序启动逻辑

## 2. 详细实施步骤

### 2.1 第一阶段：准备阶段（第1周）

#### 2.1.1 创建新目录结构

```bash
# 创建新的核心目录
mkdir -p src/core/tools/{types,utils}
mkdir -p src/core/llm/{clients,cache,utils}
mkdir -p src/core/config
mkdir -p src/core/common
mkdir -p src/services/{tools,llm,workflow}
mkdir -p src/adapters/{api,cli,tui}

# 创建新的配置目录
mkdir -p configs/tool-sets
mkdir -p configs/tools
mkdir -p configs/llms
```

#### 2.1.2 复制现有代码

```bash
# 复制tools相关代码
cp -r src/domain/tools/* src/core/tools/
cp -r src/infrastructure/tools/* src/core/tools/

# 复制llm相关代码
cp -r src/infrastructure/llm/* src/core/llm/

# 复制配置相关代码
cp -r src/infrastructure/config/* src/core/config/

# 复制通用组件
cp src/infrastructure/exceptions.py src/core/common/
cp src/infrastructure/logger/* src/core/common/
```

#### 2.1.3 创建兼容层

```python
# src/compatibility/__init__.py
"""
向后兼容层，提供旧接口的适配
"""

# tools模块兼容
from src.core.tools.interfaces import *
from src.core.tools.manager import ToolManager
from src.core.tools.factory import ToolFactory

# llm模块兼容
from src.core.llm.interfaces import *
from src.core.llm.factory import LLMFactory

# 创建兼容别名
IToolRegistry = IToolManager  # 兼容旧接口
```

#### 2.1.4 更新导入路径映射

```python
# src/compatibility/import_mapper.py
"""
导入路径映射，用于平滑过渡
"""

import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec

class CompatibilityImporter(MetaPathFinder):
    """兼容性导入器，自动重定向旧的导入路径"""
    
    def find_spec(self, fullname, path, target=None):
        # 旧的导入路径映射
        path_mappings = {
            'src.domain.tools': 'src.core.tools',
            'src.infrastructure.tools': 'src.core.tools',
            'src.infrastructure.llm': 'src.core.llm',
            'src.infrastructure.config': 'src.core.config',
        }
        
        for old_path, new_path in path_mappings.items():
            if fullname.startswith(old_path):
                new_fullname = fullname.replace(old_path, new_path, 1)
                return ModuleSpec(new_fullname, None)
        
        return None

# 注册兼容性导入器
sys.meta_path.insert(0, CompatibilityImporter())
```

### 2.2 第二阶段：重构阶段（第2-3周）

#### 2.2.1 合并tools模块

```python
# src/core/tools/interfaces.py
"""
统一的tools接口定义
"""

# 合并原有的Domain和Infrastructure接口
class ITool(ABC):
    """工具接口 - 合并原有定义"""
    
class IToolManager(ABC):
    """工具管理器接口 - 合并原有定义"""
    
class IToolFactory(ABC):
    """工具工厂接口 - 合并原有定义"""

# src/core/tools/manager.py
"""
统一的工具管理器实现
"""

class ToolManager(IToolManager):
    """工具管理器 - 合并原有功能"""
    
    def __init__(self, config_loader=None, logger=None):
        # 整合原有的初始化逻辑
        self.config_loader = config_loader
        self.logger = logger
        self._tools = {}
        self._tool_sets = {}
        
    def load_tools(self) -> List[ITool]:
        """加载工具 - 整合原有逻辑"""
        # 合并Domain和Infrastructure的加载逻辑
        pass
```

#### 2.2.2 重构llm模块

```python
# src/core/llm/interfaces.py
"""
统一的LLM接口定义
"""

class ILLMClient(ABC):
    """LLM客户端接口 - 保持原有定义"""
    
class ILLMFactory(ABC):
    """LLM工厂接口 - 保持原有定义"""

# src/core/llm/factory.py
"""
统一的LLM工厂实现
"""

class LLMFactory(ILLMFactory):
    """LLM工厂 - 整合原有功能"""
    
    def __init__(self, config=None):
        # 整合原有的初始化逻辑
        self.config = config or LLMModuleConfig()
        self._client_cache = {}
        self._client_types = {}
        
        # 注册默认客户端类型
        self._register_default_clients()
```

#### 2.2.3 更新依赖注入

```python
# src/core/di_config.py
"""
更新后的依赖注入配置
"""

def register_core_services(container):
    """注册核心服务"""
    
    # 注册tools服务
    container.register_singleton(IToolManager, ToolManager)
    container.register_singleton(IToolFactory, ToolFactory)
    
    # 注册llm服务
    container.register_singleton(ILLMFactory, LLMFactory)
    
    # 注册配置服务
    container.register_singleton(IConfigLoader, ConfigLoader)

def register_services(container):
    """注册所有服务"""
    register_core_services(container)
    # 注册其他服务...
```

### 2.3 第三阶段：配置迁移（第4周）

#### 2.3.1 重组配置文件

```bash
# 迁移工具配置
mv configs/tools/* configs/tools/  # 保持原有位置

# 创建新的工具集基础配置
cp configs/tool-sets/_group.yaml configs/tool-sets/_base.yaml
# 更新_base.yaml内容

# 重组LLM配置
mv configs/llms/_group.yaml configs/llms/_base.yaml
# 更新_base.yaml内容
```

#### 2.3.2 更新配置加载逻辑

```python
# src/core/config/loader.py
"""
更新后的配置加载器
"""

class ConfigLoader:
    """配置加载器 - 支持新的配置结构"""
    
    def load_tool_set_config(self, name: str) -> ToolSetConfig:
        """加载工具集配置"""
        # 1. 加载基础配置
        base_config = self._load_config("tool-sets/_base.yaml")
        
        # 2. 加载指定配置
        config = self._load_config(f"tool-sets/{name}.yaml")
        
        # 3. 处理继承关系
        if 'inherits_from' in config:
            config = self._process_inheritance(config, base_config)
        
        return ToolSetConfig.from_dict(config)
```

#### 2.3.3 验证配置正确性

```python
# scripts/validate_config_migration.py
"""
配置迁移验证脚本
"""

def validate_tool_configs():
    """验证工具配置"""
    tools_dir = Path("configs/tools")
    for config_file in tools_dir.glob("*.yaml"):
        try:
            config = load_tool_config(config_file)
            validate_tool_config(config)
            print(f"✓ {config_file.name}")
        except Exception as e:
            print(f"✗ {config_file.name}: {e}")

def validate_tool_set_configs():
    """验证工具集配置"""
    tool_sets_dir = Path("configs/tool-sets")
    for config_file in tool_sets_dir.glob("*.yaml"):
        if config_file.name.startswith("_"):
            continue  # 跳过基础配置
        try:
            config = load_tool_set_config(config_file.stem)
            validate_tool_set_config(config)
            print(f"✓ {config_file.name}")
        except Exception as e:
            print(f"✗ {config_file.name}: {e}")

if __name__ == "__main__":
    print("验证工具配置...")
    validate_tool_configs()
    print("\n验证工具集配置...")
    validate_tool_set_configs()
```

### 2.4 第四阶段：测试阶段（第5周）

#### 2.4.1 单元测试

```python
# tests/test_core_tools.py
"""
核心tools模块测试
"""

class TestToolManager:
    """工具管理器测试"""
    
    def test_load_tools(self):
        """测试工具加载"""
        manager = ToolManager()
        tools = manager.load_tools()
        assert len(tools) > 0
        assert all(isinstance(tool, ITool) for tool in tools)
    
    def test_get_tool(self):
        """测试获取工具"""
        manager = ToolManager()
        manager.load_tools()
        tool = manager.get_tool("calculator")
        assert tool.name == "calculator"
    
    def test_tool_set_loading(self):
        """测试工具集加载"""
        manager = ToolManager()
        tool_set = manager.get_tool_set("basic")
        assert len(tool_set) > 0

# tests/test_core_llm.py
"""
核心LLM模块测试
"""

class TestLLMFactory:
    """LLM工厂测试"""
    
    def test_create_client(self):
        """测试创建客户端"""
        factory = LLMFactory()
        config = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        client = factory.create_client(config)
        assert isinstance(client, ILLMClient)
    
    def test_client_caching(self):
        """测试客户端缓存"""
        factory = LLMFactory()
        config = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        client1 = factory.create_client(config)
        client2 = factory.get_cached_client("test-model")
        assert client1 is client2
```

#### 2.4.2 集成测试

```python
# tests/test_integration.py
"""
集成测试
"""

class TestToolLLMIntegration:
    """工具和LLM集成测试"""
    
    def test_tool_execution_with_llm(self):
        """测试LLM调用工具"""
        # 创建LLM客户端
        llm_factory = LLMFactory()
        llm_config = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        llm_client = llm_factory.create_client(llm_config)
        
        # 创建工具管理器
        tool_manager = ToolManager()
        tools = tool_manager.load_tools()
        
        # 测试工具调用
        messages = [
            HumanMessage("计算 2 + 3")
        ]
        response = llm_client.generate(messages, tools=tools)
        
        assert response.content is not None
```

#### 2.4.3 性能测试

```python
# tests/test_performance.py
"""
性能测试
"""

class TestPerformance:
    """性能测试"""
    
    def test_tool_loading_performance(self):
        """测试工具加载性能"""
        start_time = time.time()
        manager = ToolManager()
        tools = manager.load_tools()
        end_time = time.time()
        
        load_time = end_time - start_time
        assert load_time < 1.0  # 加载时间应小于1秒
        assert len(tools) > 0
    
    def test_llm_client_creation_performance(self):
        """测试LLM客户端创建性能"""
        factory = LLMFactory()
        config = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        
        start_time = time.time()
        client = factory.create_client(config)
        end_time = time.time()
        
        creation_time = end_time - start_time
        assert creation_time < 0.1  # 创建时间应小于0.1秒
```

### 2.5 第五阶段：切换阶段（第6周）

#### 2.5.1 更新启动脚本

```python
# src/bootstrap.py
"""
更新后的应用程序启动入口
"""

def bootstrap_application():
    """启动应用程序"""
    
    # 1. 初始化依赖注入容器
    container = DIContainer()
    
    # 2. 注册核心服务
    register_core_services(container)
    
    # 3. 注册服务层
    register_services(container)
    
    # 4. 注册适配器
    register_adapters(container)
    
    # 5. 加载配置
    config_loader = container.resolve(IConfigLoader)
    app_config = config_loader.load_app_config()
    
    # 6. 启动应用程序
    app = Application(container, app_config)
    app.start()

if __name__ == "__main__":
    bootstrap_application()
```

#### 2.5.2 监控和日志

```python
# src/core/monitoring/migration_monitor.py
"""
迁移监控
"""

class MigrationMonitor:
    """迁移监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.errors = []
    
    def record_metric(self, name: str, value: float):
        """记录指标"""
        self.metrics[name] = value
    
    def record_error(self, error: Exception):
        """记录错误"""
        self.errors.append({
            "timestamp": datetime.now(),
            "error": str(error),
            "type": type(error).__name__
        })
    
    def get_summary(self) -> dict:
        """获取监控摘要"""
        return {
            "metrics": self.metrics,
            "error_count": len(self.errors),
            "errors": self.errors[-10:]  # 最近10个错误
        }

# 在关键位置添加监控
monitor = MigrationMonitor()

try:
    # 执行关键操作
    manager = ToolManager()
    tools = manager.load_tools()
    monitor.record_metric("tool_load_time", time.time() - start_time)
    monitor.record_metric("tool_count", len(tools))
except Exception as e:
    monitor.record_error(e)
    raise
```

#### 2.5.3 回滚机制

```python
# scripts/rollback.py
"""
快速回滚脚本
"""

def rollback_migration():
    """回滚迁移"""
    
    print("开始回滚迁移...")
    
    # 1. 恢复原始目录结构
    if Path("src/domain_backup").exists():
        shutil.move("src/domain", "src/domain_new")
        shutil.move("src/domain_backup", "src/domain")
    
    if Path("src/infrastructure_backup").exists():
        shutil.move("src/infrastructure", "src/infrastructure_new")
        shutil.move("src/infrastructure_backup", "src/infrastructure")
    
    # 2. 恢复配置文件
    if Path("configs_backup").exists():
        shutil.move("configs", "configs_new")
        shutil.move("configs_backup", "configs")
    
    # 3. 恢复启动脚本
    if Path("src/bootstrap_backup.py").exists():
        shutil.move("src/bootstrap.py", "src/bootstrap_new.py")
        shutil.move("src/bootstrap_backup.py", "src/bootstrap.py")
    
    print("回滚完成！")

if __name__ == "__main__":
    rollback_migration()
```

## 3. 风险控制措施

### 3.1 数据备份

```bash
#!/bin/bash
# scripts/backup_before_migration.sh

echo "创建迁移前备份..."

# 备份源代码
tar -czf src_backup_$(date +%Y%m%d_%H%M%S).tar.gz src/

# 备份配置文件
tar -czf configs_backup_$(date +%Y%m%d_%H%M%S).tar.gz configs/

# 备份数据库（如果有）
# pg_dump modular_agent > db_backup_$(date +%Y%m%d_%H%M%S).sql

echo "备份完成！"
```

### 3.2 健康检查

```python
# scripts/health_check.py
"""
系统健康检查
"""

def check_system_health():
    """检查系统健康状态"""
    
    checks = []
    
    # 检查核心模块
    try:
        from src.core.tools import ToolManager
        from src.core.llm import LLMFactory
        checks.append(("core_modules", True, "核心模块加载正常"))
    except Exception as e:
        checks.append(("core_modules", False, f"核心模块加载失败: {e}"))
    
    # 检查配置加载
    try:
        from src.core.config import ConfigLoader
        loader = ConfigLoader()
        config = loader.load_app_config()
        checks.append(("config_loading", True, "配置加载正常"))
    except Exception as e:
        checks.append(("config_loading", False, f"配置加载失败: {e}"))
    
    # 检查工具加载
    try:
        manager = ToolManager()
        tools = manager.load_tools()
        checks.append(("tool_loading", True, f"工具加载正常，共{len(tools)}个工具"))
    except Exception as e:
        checks.append(("tool_loading", False, f"工具加载失败: {e}"))
    
    # 输出检查结果
    print("系统健康检查结果:")
    for name, status, message in checks:
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {name}: {message}")
    
    # 返回整体状态
    all_passed = all(status for _, status, _ in checks)
    return all_passed

if __name__ == "__main__":
    healthy = check_system_health()
    exit(0 if healthy else 1)
```

### 3.3 监控告警

```python
# src/core/monitoring/alerting.py
"""
监控告警系统
"""

class AlertingSystem:
    """告警系统"""
    
    def __init__(self):
        self.alerts = []
        self.thresholds = {
            "error_rate": 0.05,  # 错误率阈值5%
            "response_time": 1.0,  # 响应时间阈值1秒
            "memory_usage": 0.8,  # 内存使用率阈值80%
        }
    
    def check_metrics(self, metrics: dict):
        """检查指标并触发告警"""
        
        # 检查错误率
        if "error_rate" in metrics:
            if metrics["error_rate"] > self.thresholds["error_rate"]:
                self.trigger_alert("error_rate", metrics["error_rate"])
        
        # 检查响应时间
        if "response_time" in metrics:
            if metrics["response_time"] > self.thresholds["response_time"]:
                self.trigger_alert("response_time", metrics["response_time"])
        
        # 检查内存使用率
        if "memory_usage" in metrics:
            if metrics["memory_usage"] > self.thresholds["memory_usage"]:
                self.trigger_alert("memory_usage", metrics["memory_usage"])
    
    def trigger_alert(self, metric_name: str, value: float):
        """触发告警"""
        alert = {
            "timestamp": datetime.now(),
            "metric": metric_name,
            "value": value,
            "threshold": self.thresholds[metric_name],
            "severity": "high" if value > self.thresholds[metric_name] * 1.5 else "medium"
        }
        
        self.alerts.append(alert)
        
        # 发送告警通知
        self.send_notification(alert)
    
    def send_notification(self, alert: dict):
        """发送告警通知"""
        # 实现告警通知逻辑（邮件、短信、Slack等）
        print(f"告警: {alert['metric']} = {alert['value']} (阈值: {alert['threshold']})")
```

## 4. 验收标准

### 4.1 功能验收

1. **所有现有功能正常工作**
   - 工具加载和执行
   - LLM客户端创建和调用
   - 配置加载和处理
   - 工作流执行

2. **性能不降低**
   - 工具加载时间不超过原系统的110%
   - LLM客户端创建时间不超过原系统的110%
   - 内存使用不超过原系统的120%

3. **配置兼容性**
   - 所有现有配置文件可以正常加载
   - 新的配置结构工作正常
   - 配置继承机制正确工作

### 4.2 质量验收

1. **代码质量**
   - 所有单元测试通过
   - 代码覆盖率不低于80%
   - 静态代码分析无严重问题

2. **文档完整性**
   - API文档更新完成
   - 迁移文档完整
   - 用户指南更新

3. **监控和日志**
   - 关键指标监控正常
   - 错误日志完整
   - 告警机制工作正常

## 5. 总结

这个迁移策略通过分阶段实施、充分测试、风险控制等措施，确保了扁平化架构的安全迁移。整个过程中保持了向后兼容性，最小化了业务中断风险，同时实现了架构简化的目标。

迁移完成后，系统将具有更简单的结构、更高的开发效率和更好的可维护性，为后续的功能扩展和优化奠定了良好的基础。