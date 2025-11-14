# 配置系统重构执行指南

## 执行前准备

### 1. 环境检查
```bash
# 检查Python版本
python --version  # 需要Python 3.13+

# 检查项目依赖
pip install -r requirements.txt

# 运行现有测试
pytest tests/ -v
```

### 2. 创建备份
```bash
# 创建配置目录的完整备份
cp -r src/infrastructure/config src/infrastructure/config_backup_$(date +%Y%m%d_%H%M%S)

# 或者使用git创建分支
git checkout -b config-refactoring
```

### 3. 验证当前功能
```bash
# 运行配置相关测试
pytest tests/test_config_*.py -v

# 检查配置加载功能
python -c "from src.infrastructure.config import create_config_system; print('配置系统正常')"
```

## 分阶段执行步骤

### 第一阶段：目录结构优化

#### 步骤1.1：创建新目录结构
```bash
cd src/infrastructure/config
mkdir -p {loader,processor,service,migration,utils}
```

#### 步骤1.2：执行文件移动脚本
创建并执行 `move_files.sh`：
```bash
#!/bin/bash
# 文件移动脚本

echo "开始移动文件..."

# 核心接口和基础类
mv core/interfaces.py interfaces.py
mv models/base.py base.py

# 加载器相关
mv core/loader.py loader/yaml_loader.py
mv utils/file_watcher.py loader/file_watcher.py

# 处理器相关
mv utils/inheritance.py processor/inheritance.py
mv core/merger.py processor/merger.py
mv utils/validator.py processor/validator.py
mv utils/env_resolver.py processor/env_resolver.py

# 服务相关
mv config_callback_manager.py service/callback_manager.py
mv error_recovery.py service/error_recovery.py
mv checkpoint_config_service.py service/checkpoint_service.py

# 迁移相关
mv config_migration.py migration/migrator.py

echo "文件移动完成！"
```

#### 步骤1.3：创建初始化文件

创建 `src/infrastructure/config/__init__.py`：
```python
"""配置系统主模块"""

from .config_system import ConfigSystem, IConfigSystem
from .config_factory import ConfigFactory
from .config_manager import ConfigManager

__all__ = ['ConfigSystem', 'IConfigSystem', 'ConfigFactory', 'ConfigManager']
```

创建各子模块的 `__init__.py` 文件：

`loader/__init__.py`：
```python
from .yaml_loader import YamlConfigLoader
from .file_watcher import FileWatcher

__all__ = ['YamlConfigLoader', 'FileWatcher']
```

`processor/__init__.py`：
```python
from .inheritance import ConfigInheritanceProcessor
from .merger import ConfigMerger
from .validator import ConfigValidator
from .env_resolver import EnvResolver

__all__ = ['ConfigInheritanceProcessor', 'ConfigMerger', 'ConfigValidator', 'EnvResolver']
```

`service/__init__.py`：
```python
from .callback_manager import ConfigCallbackService
from .error_recovery import ConfigErrorRecovery
from .checkpoint_service import CheckpointConfigService

__all__ = ['ConfigCallbackService', 'ConfigErrorRecovery', 'CheckpointConfigService']
```

#### 步骤1.4：更新导入路径

使用脚本批量更新导入路径：

```python
#!/usr/bin/env python3
# update_imports.py

import os
import re

def update_imports_in_file(filepath):
    """更新文件中的导入路径"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义导入路径映射
    import_mappings = {
        r'from \.core\.interfaces import': 'from .interfaces import',
        r'from \.core\.loader import': 'from .loader import',
        r'from \.core\.merger import': 'from .processor import',
        r'from \.utils\.validator import': 'from .processor import',
        r'from \.utils\.inheritance import': 'from .processor import',
        r'from \.utils\.env_resolver import': 'from .processor import',
        r'from \.config_callback_manager import': 'from .service import',
        r'from \.error_recovery import': 'from .service import',
        r'from \.checkpoint_config_service import': 'from .service import',
        r'from \.config_migration import': 'from .migration import',
    }
    
    # 应用映射
    for pattern, replacement in import_mappings.items():
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def update_all_imports(directory):
    """更新目录下所有Python文件的导入"""
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                print(f"更新: {filepath}")
                update_imports_in_file(filepath)

if __name__ == "__main__":
    update_all_imports("src/infrastructure/config")
```

#### 步骤1.5：验证第一阶段

```bash
# 检查语法错误
python -m py_compile src/infrastructure/config/__init__.py
python -m py_compile src/infrastructure/config/loader/__init__.py
python -m py_compile src/infrastructure/config/processor/__init__.py
python -m py_compile src/infrastructure/config/service/__init__.py

# 运行测试
pytest tests/test_config_refactoring.py -v

# 验证配置加载
python -c "
from src.infrastructure.config import ConfigFactory
config_system = ConfigFactory.create_config_system()
print('第一阶段验证通过')
"
```

### 第二阶段：接口抽象化

#### 步骤2.1：创建核心接口

创建 `src/infrastructure/config/interfaces.py`：
```python
"""配置系统核心接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

class IConfigLoader(ABC):
    """配置加载器接口"""
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载所有配置"""
        pass

class IConfigProcessor(ABC):
    """配置处理器接口"""
    
    @abstractmethod
    def process(self, config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理配置"""
        pass

class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any], config_type: str) -> bool:
        """验证配置"""
        pass

class IConfigSystem(ABC):
    """配置系统接口"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any], config_type: str) -> bool:
        """验证配置"""
        pass
```

#### 步骤2.2：重构配置系统

重构 `src/infrastructure/config/config_system.py`：
```python
"""配置系统核心实现"""

from typing import Dict, Any, List, Optional
from .interfaces import IConfigSystem, IConfigLoader, IConfigProcessor, IConfigValidator

class ConfigSystem(IConfigSystem):
    """配置系统实现"""
    
    def __init__(
        self,
        loader: IConfigLoader,
        processors: List[IConfigProcessor],
        validator: IConfigValidator
    ):
        self._loader = loader
        self._processors = processors
        self._validator = validator
        self._cache = {}
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        # 检查缓存
        if config_path in self._cache:
            return self._cache[config_path]
        
        # 加载配置
        config = self._loader.load(config_path)
        
        # 处理配置（继承、合并等）
        for processor in self._processors:
            config = processor.process(config)
        
        # 缓存配置
        self._cache[config_path] = config
        return config
    
    def validate_config(self, config: Dict[str, Any], config_type: str) -> bool:
        """验证配置"""
        return self._validator.validate(config, config_type)
```

#### 步骤2.3：创建配置工厂

创建 `src/infrastructure/config/config_factory.py`：
```python
"""配置工厂，负责创建配置系统组件"""

from .interfaces import IConfigSystem, IConfigLoader, IConfigProcessor, IConfigValidator
from .loader.yaml_loader import YamlConfigLoader
from .processor.inheritance import ConfigInheritanceProcessor
from .processor.merger import ConfigMerger
from .processor.validator import ConfigValidator
from .processor.env_resolver import EnvResolver
from .config_system import ConfigSystem

class ConfigFactory:
    """配置工厂"""
    
    @staticmethod
    def create_config_system(base_path: str = "configs") -> IConfigSystem:
        """创建配置系统"""
        # 创建组件
        loader = YamlConfigLoader(base_path)
        processors = [
            ConfigInheritanceProcessor(),
            ConfigMerger(),
            EnvResolver()
        ]
        validator = ConfigValidator()
        
        # 创建配置系统
        return ConfigSystem(loader, processors, validator)
    
    @staticmethod
    def create_minimal_config_system(base_path: str = "configs") -> IConfigSystem:
        """创建最小配置系统（仅核心功能）"""
        loader = YamlConfigLoader(base_path)
        validator = ConfigValidator()
        
        return ConfigSystem(loader, [], validator)
```

#### 步骤2.4：验证第二阶段

```bash
# 测试配置系统创建
python -c "
from src.infrastructure.config import ConfigFactory
config_system = ConfigFactory.create_config_system()
print('配置系统创建成功')
"

# 测试配置加载
python -c "
from src.infrastructure.config import ConfigFactory
config_system = ConfigFactory.create_config_system()
config = config_system.load_config('global.yaml')
print('配置加载成功:', config)
"

# 运行测试
pytest tests/test_config_system.py -v
```

### 第三阶段：功能模块化

#### 步骤3.1：重构配置加载器

重构 `src/infrastructure/config/loader/yaml_loader.py`：
```python
"""YAML配置加载器"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from ..interfaces import IConfigLoader
from ..exceptions import ConfigurationError

class YamlConfigLoader(IConfigLoader):
    """YAML配置加载器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self._cache = {}
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        # 检查缓存
        if config_path in self._cache:
            return self._cache[config_path]
        
        # 构建完整路径
        full_path = self.base_path / config_path
        
        # 检查文件存在
        if not full_path.exists():
            raise ConfigurationError(f"配置文件不存在: {full_path}")
        
        try:
            # 读取YAML文件
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 缓存配置
            self._cache[config_path] = config
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"YAML解析错误 {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"加载配置失败 {config_path}: {e}")
    
    def reload(self) -> None:
        """重新加载所有配置"""
        self._cache.clear()
```

#### 步骤3.2：重构配置处理器

创建 `src/infrastructure/config/processor/base_processor.py`：
```python
"""配置处理器基类"""

from abc import ABC
from typing import Dict, Any, Optional

class BaseConfigProcessor(ABC):
    """配置处理器基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def process(self, config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理配置"""
        raise NotImplementedError
```

创建 `src/infrastructure/config/processor/inheritance.py`：
```python
"""配置继承处理器"""

from typing import Dict, Any, Optional
from .base_processor import BaseConfigProcessor

class ConfigInheritanceProcessor(BaseConfigProcessor):
    """配置继承处理器"""
    
    def __init__(self):
        super().__init__("inheritance")
    
    def process(self, config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理配置继承"""
        if 'inherits_from' not in config:
            return config
        
        # 处理继承逻辑
        # ... 实现继承处理逻辑
        
        return config
```

#### 步骤3.3：重构配置服务

重构 `src/infrastructure/config/service/callback_manager.py`：
```python
"""配置回调管理器"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class CallbackPriority(Enum):
    """回调优先级"""
    LOW = 0
    NORMAL = 50
    HIGH = 100

@dataclass
class ConfigCallback:
    """配置回调"""
    id: str
    callback: Callable
    priority: CallbackPriority
    enabled: bool = True

class ConfigCallbackService:
    """配置回调服务"""
    
    def __init__(self):
        self._callbacks: Dict[str, ConfigCallback] = {}
        self._execution_history: List[Dict[str, Any]] = []
    
    def register_callback(self, callback_id: str, callback: Callable, priority: CallbackPriority = CallbackPriority.NORMAL):
        """注册回调"""
        self._callbacks[callback_id] = ConfigCallback(
            id=callback_id,
            callback=callback,
            priority=priority
        )
    
    def trigger_callbacks(self, config_path: str, old_config: Optional[Dict[str, Any]], new_config: Dict[str, Any]):
        """触发回调"""
        # 按优先级排序
        sorted_callbacks = sorted(
            self._callbacks.values(),
            key=lambda x: x.priority.value,
            reverse=True
        )
        
        # 执行回调
        for callback in sorted_callbacks:
            if callback.enabled:
                try:
                    callback.callback(config_path, old_config, new_config)
                except Exception as e:
                    # 记录执行错误
                    self._record_execution_error(callback.id, str(e))
    
    def _record_execution_error(self, callback_id: str, error: str):
        """记录执行错误"""
        self._execution_history.append({
            'callback_id': callback_id,
            'error': error,
            'timestamp': __import__('time').time()
        })
```

#### 步骤3.4：验证第三阶段

```bash
# 测试配置处理器
python -c "
from src.infrastructure.config.processor import ConfigInheritanceProcessor
processor = ConfigInheritanceProcessor()
config = {'name': 'test', 'inherits_from': 'parent'}
result = processor.process(config)
print('继承处理器工作正常')
"

# 测试配置服务
python -c "
from src.infrastructure.config.service import ConfigCallbackService
service = ConfigCallbackService()
service.register_callback('test', lambda: print('回调执行'))
print('回调服务创建成功')
"

# 运行完整测试
pytest tests/ -v
```

### 第四阶段：测试和文档

#### 步骤4.1：创建测试文件

创建 `tests/test_config_system.py`：
```python
"""配置系统重构测试"""

import pytest
import tempfile
import os
from pathlib import Path

from src.infrastructure.config import ConfigFactory
from src.infrastructure.config.interfaces import IConfigSystem

class TestConfigSystem:
    """配置系统测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "configs"
        self.config_path.mkdir(exist_ok=True)
        
        # 创建测试配置文件
        self._create_test_configs()
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_configs(self):
        """创建测试配置文件"""
        # 创建全局配置
        global_config = """
log_level: INFO
env: test
debug: false
"""
        (self.config_path / "global.yaml").write_text(global_config)
        
        # 创建测试配置
        test_config = """
name: test_config
value: 42
"""
        (self.config_path / "test.yaml").write_text(test_config)
    
    def test_create_config_system(self):
        """测试创建配置系统"""
        config_system = ConfigFactory.create_config_system(str(self.config_path))
        assert isinstance(config_system, IConfigSystem)
    
    def test_load_config(self):
        """测试加载配置"""
        config_system = ConfigFactory.create_config_system(str(self.config_path))
        config = config_system.load_config("test.yaml")
        
        assert config is not None
        assert config["name"] == "test_config"
        assert config["value"] == 42
    
    def test_validate_config(self):
        """测试验证配置"""
        config_system = ConfigFactory.create_config_system(str(self.config_path))
        test_config = {"name": "test", "value": 123}
        
        result = config_system.validate_config(test_config, "test")
        assert result is True
    
    def test_load_nonexistent_config(self):
        """测试加载不存在的配置"""
        config_system = ConfigFactory.create_config_system(str(self.config_path))
        
        with pytest.raises(Exception):
            config_system.load_config("nonexistent.yaml")
```

#### 步骤4.2：创建使用示例

创建 `examples/config_usage_example.py`：
```python
"""配置系统使用示例"""

from src.infrastructure.config import ConfigFactory
from src.infrastructure.config.interfaces import IConfigSystem

def basic_usage_example():
    """基本使用示例"""
    # 创建配置系统
    config_system = ConfigFactory.create_config_system()
    
    # 加载全局配置
    global_config = config_system.load_config("global.yaml")
    print(f"日志级别: {global_config.get('log_level')}")
    print(f"运行环境: {global_config.get('env')}")
    
    # 加载LLM配置
    llm_config = config_system.load_config("llms/gpt-4.yaml")
    print(f"模型名称: {llm_config.get('model_name')}")
    print(f"提供商: {llm_config.get('provider')}")

def validation_example():
    """验证示例"""
    config_system = ConfigFactory.create_config_system()
    
    # 创建测试配置
    test_config = {
        "model_name": "gpt-4",
        "provider": "openai",
        "temperature": 0.7
    }
    
    # 验证配置
    is_valid = config_system.validate_config(test_config, "llm")
    print(f"配置验证结果: {is_valid}")

if __name__ == "__main__":
    basic_usage_example()
    validation_example()
```

#### 步骤4.3：验证第四阶段

```bash
# 运行所有测试
pytest tests/test_config_system.py -v

# 运行示例
python examples/config_usage_example.py

# 检查测试覆盖率
pytest tests/ --cov=src.infrastructure.config --cov-report=html
```

## 回滚方案

如果重构过程中出现问题，可以快速回滚：

```bash
# 方法1：使用备份
rm -rf src/infrastructure/config
cp -r src/infrastructure/config_backup_<timestamp> src/infrastructure/config

# 方法2：使用git
git checkout main
git branch -D config-refactoring

# 方法3：手动回滚
# 按照重构步骤的逆序执行
```

## 常见问题解决

### 1. 导入错误
```python
# 问题：ModuleNotFoundError
# 解决：检查__init__.py文件是否正确创建
# 检查导入路径是否正确
```

### 2. 循环依赖
```python
# 问题：ImportError: cannot import name 'X'
# 解决：使用延迟导入
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .module import ClassName
```

### 3. 测试失败
```python
# 问题：测试用例失败
# 解决：检查测试环境设置
# 检查配置文件路径
# 验证测试数据是否正确
```

## 执行检查清单

### 阶段1完成检查
- [ ] 新目录结构创建完成
- [ ] 所有文件正确移动
- [ ] 导入路径更新完成
- [ ] 测试通过
- [ ] 功能验证正常

### 阶段2完成检查
- [ ] 接口定义完成
- [ ] 配置系统重构完成
- [ ] 配置工厂创建完成
- [ ] 测试通过
- [ ] 功能验证正常

### 阶段3完成检查
- [ ] 配置加载器重构完成
- [ ] 配置处理器重构完成
- [ ] 配置服务重构完成
- [ ] 测试通过
- [ ] 功能验证正常

### 阶段4完成检查
- [ ] 测试文件创建完成
- [ ] 示例代码创建完成
- [ ] 文档更新完成
- [ ] 所有测试通过
- [ ] 覆盖率达标

## 后续优化建议

1. **性能优化**：根据测试结果进行性能调优
2. **功能扩展**：添加新的配置处理功能
3. **工具集成**：集成更多开发工具
4. **监控增强**：增强配置系统的监控能力

## 联系和支持

如果在执行过程中遇到问题：
1. 检查本指南的常见问题解决部分
2. 查看相关测试用例
3. 参考原始实现代码
4. 寻求团队成员帮助

这个执行指南提供了详细的步骤和验证方法，确保重构过程的可控性和成功率。