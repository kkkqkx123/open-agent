# `src\infrastructure\config` 迁移实施指南

## 快速开始

### 前置准备
1. 备份当前的 `src\infrastructure\config` 目录
2. 确保新架构的 `src/core/config` 目录已存在
3. 创建目标目录：`src/adapters/config/` 和 `src/adapters/config/services/`

### 迁移命令示例
```bash
# 创建目标目录
mkdir -p src/adapters/config/services

# 备份配置系统
cp -r src/infrastructure/config backup/infrastructure_config_backup_$(date +%Y%m%d)
```

## 分阶段实施计划

### 第一阶段：核心功能迁移（预计时间：2-3天）

#### 步骤1.1：配置模型整合
```bash
# 合并模型文件到核心配置
# 将 infrastructure/config/models/ 下的模型合并到 core/config/models.py
```

**关键操作：**
- 将 `BaseConfig` 模型整合
- 合并 `LLMConfig`、`ToolConfig`、`GlobalConfig` 等模型
- 保持向后兼容的字段和方法

#### 步骤1.2：加载器迁移
```bash
# 整合文件配置加载器
# 将 infrastructure/config/loader/file_config_loader.py 整合到 core/config/yaml_loader.py
```

**关键操作：**
- 统一YAML加载接口
- 优化缓存机制
- 保持错误处理一致性

#### 步骤1.3：处理器迁移
```bash
# 整合配置处理器
# 将 infrastructure/config/processor/validator.py 整合到 core/config/config_processor.py
```

**关键操作：**
- 统一配置验证逻辑
- 整合继承处理功能
- 统一环境变量解析

### 第二阶段：适配器创建（预计时间：1-2天）

#### 步骤2.1：配置系统适配器
```bash
# 重构配置系统
# 将 infrastructure/config/config_system.py 重构为 adapters/config/config_system_adapter.py
```

**关键操作：**
- 创建适配器包装核心配置管理器
- 实现基础设施特定逻辑
- 提供向后兼容接口

#### 步骤2.2：服务适配器迁移
```bash
# 迁移配置服务
# 将 infrastructure/config/service/ 迁移到 adapters/config/services/
```

**关键操作：**
- 移动服务文件
- 更新导入路径
- 适配新架构接口

### 第三阶段：工具类整合和清理（预计时间：1天）

#### 步骤3.1：工具类整合
```bash
# 整合通用工具
# 将 infrastructure/config/utils/ 整合到 core/common/utils/
```

#### 步骤3.2：清理冗余文件
```bash
# 删除不再需要的文件
rm src/infrastructure/config/config_cache.py
rm src/infrastructure/config/config_loader.py
# 其他冗余文件...
```

## 关键配置文件更新

### 依赖注入配置更新
```python
# 更新 infrastructure/di/infrastructure_module.py
"config_system": "src.adapters.config.config_system_adapter.ConfigSystemAdapter",
"config_loader": "src.core.config.config_loader.ConfigLoader",
"config_validator": "src.core.config.config_processor.ConfigProcessor",
```

### 导入路径更新示例
```python
# 旧导入
from src.infrastructure.config.config_system import IConfigSystem
from src.infrastructure.config.models.llm_config import LLMConfig

# 新导入
from src.adapters.config.config_system_adapter import ConfigSystemAdapter
from src.core.config.models import LLMConfig
```

## 测试验证步骤

### 单元测试
```bash
# 运行核心配置测试
pytest tests/core/config/ -v

# 运行适配器测试
pytest tests/adapters/config/ -v
```

### 集成测试
```bash
# 运行配置系统集成测试
pytest tests/integration/config/ -v

# 运行LLM配置集成测试
pytest tests/integration/llm/config/ -v
```

### 回归测试
```bash
# 运行完整的配置相关测试
pytest tests/ -k "config" -v
```

## 问题排查指南

### 常见问题及解决方案

#### 问题1：导入路径错误
**症状**: `ModuleNotFoundError` 或导入错误
**解决**: 检查并更新所有导入路径到新位置

#### 问题2：功能缺失
**症状**: 某些配置功能无法正常工作
**解决**: 检查适配器实现是否完整，确保所有接口方法都已实现

#### 问题3：性能下降
**症状**: 配置加载变慢
**解决**: 检查缓存机制，优化配置处理逻辑

### 调试技巧
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查配置加载过程
from src.core.config.config_manager import ConfigManager
manager = ConfigManager()
config = manager.load_config("llms/openai/gpt-4.yaml")
```

## 回滚步骤

如果迁移出现问题，可按以下步骤回滚：

### 步骤1：恢复备份
```bash
# 恢复备份的配置系统
cp -r backup/infrastructure_config_backup_${DATE}/config src/infrastructure/
```

### 步骤2：恢复依赖配置
```bash
# 恢复原有的依赖注入配置
git checkout HEAD -- src/infrastructure/di/infrastructure_module.py
```

### 步骤3：验证恢复
```bash
# 运行测试验证恢复成功
pytest tests/ -k "config" -v
```

## 性能优化建议

### 配置缓存优化
```python
# 优化缓存配置
from src.core.config.config_manager import ConfigManager

manager = ConfigManager(
    use_cache=True,
    cache_size=1000,  # 增加缓存大小
    cache_ttl=3600   # 设置缓存过期时间
)
```

### 并发访问优化
```python
# 启用并发安全
from threading import Lock

class ThreadSafeConfigManager(ConfigManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = Lock()
```

## 总结

本实施指南提供了详细的迁移步骤和操作指南。建议按照阶段顺序实施，每个阶段完成后进行充分的测试验证。如果遇到问题，可以参考问题排查指南或执行回滚步骤。

**关键成功因素：**
1. 充分的测试覆盖
2. 逐步迁移策略
3. 完善的回滚计划
4. 详细的日志记录

**文档版本**: 1.0  
**创建时间**: 2025-11-18