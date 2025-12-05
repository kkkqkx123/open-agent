# common_infra.py 接口迁移策略和优先级计划

## 🎯 迁移目标

将 `src/interfaces/common_infra.py` 中的所有接口迁移到基础设施层，实现更清晰的架构分层和依赖关系。

## 📊 迁移优先级矩阵

基于影响范围、复杂度和风险评估，制定以下优先级：

| 优先级 | 接口 | 影响范围 | 复杂度 | 风险级别 | 预计工期 |
|--------|------|----------|--------|----------|----------|
| P1 (最高) | ServiceLifetime | 中等 | 低 | 低 | 1天 |
| P2 (高) | IConfigInheritanceHandler | 低 | 中 | 低 | 2天 |
| P3 (中) | IStorage | 中等 | 中 | 中 | 3天 |
| P4 (低) | IConfigLoader | 高 | 高 | 高 | 5天 |
| P5 (最低) | IDependencyContainer | 高 | 高 | 高 | 7天 |

## 🚀 分阶段迁移计划

### 第一阶段：基础设施准备 (1天)

#### 目标
- 创建基础设施层接口目录结构
- 建立迁移框架
- 准备兼容性层

#### 任务清单
- [ ] 创建 `src/infrastructure/interfaces/` 目录
- [ ] 创建子目录结构 (`common/`, `config/`, `storage/`, `container/`)
- [ ] 创建 `__init__.py` 文件
- [ ] 建立向后兼容性导入机制

#### 验收标准
- 目录结构创建完成
- 兼容性层可以正常导入
- 无语法错误

### 第二阶段：ServiceLifetime 迁移 (1天)

#### 目标
迁移 `ServiceLifetime` 枚举到基础设施层

#### 任务清单
- [ ] 创建 `src/infrastructure/interfaces/common.py`
- [ ] 迁移 `ServiceLifetime` 枚举
- [ ] 更新所有导入语句
- [ ] 运行测试验证

#### 影响文件
```
src/services/container/bindings/*.py
src/services/container/core/container.py
src/services/container/core/base_service_bindings.py
```

#### 验收标准
- 所有测试通过
- 导入路径更新完成
- 功能无回归

### 第三阶段：IConfigInheritanceHandler 迁移 (2天)

#### 目标
迁移配置继承处理器接口

#### 任务清单
- [ ] 创建 `src/infrastructure/interfaces/config.py`
- [ ] 迁移 `IConfigInheritanceHandler` 接口
- [ ] 更新实现类的导入
- [ ] 更新相关测试
- [ ] 验证配置系统功能

#### 影响文件
```
src/core/common/utils/inheritance_handler.py
相关测试文件
```

#### 验收标准
- 配置继承功能正常
- 所有测试通过
- 无性能回归

### 第四阶段：IStorage 迁移 (3天)

#### 目标
迁移存储接口和相关实现

#### 任务清单
- [ ] 创建 `src/infrastructure/interfaces/storage.py`
- [ ] 迁移 `IStorage` 接口
- [ ] 迁移 `BaseStorage` 实现到基础设施层
- [ ] 更新所有存储相关导入
- [ ] 更新存储适配器
- [ ] 全面测试存储功能

#### 影响文件
```
src/core/common/storage.py
src/adapters/storage/adapters/base.py
src/services/storage/migration.py
相关测试文件
```

#### 验收标准
- 存储功能完全正常
- 所有存储测试通过
- 性能无回归

### 第五阶段：IConfigLoader 迁移 (5天)

#### 目标
迁移配置加载器接口和实现

#### 任务清单
- [ ] 更新 `src/infrastructure/interfaces/config.py`
- [ ] 迁移 `IConfigLoader` 接口
- [ ] 迁移 `ConfigLoader` 实现到基础设施层
- [ ] 处理与现有 LLM 配置加载器的关系
- [ ] 更新所有配置加载相关导入
- [ ] 全面测试配置系统

#### 影响文件
```
src/core/config/config_loader.py
src/core/workflow/config/node_config_loader.py
src/services/tools/validation/manager.py
src/adapters/tui/app.py
src/adapters/tui/config.py
src/adapters/cli/run_command.py
src/adapters/cli/commands.py
```

#### 验收标准
- 配置加载功能完全正常
- 所有配置测试通过
- TUI 和 CLI 功能正常

### 第六阶段：IDependencyContainer 迁移 (7天)

#### 目标
迁移依赖注入容器接口和实现

#### 任务清单
- [ ] 创建 `src/infrastructure/interfaces/container.py`
- [ ] 迁移 `IDependencyContainer` 接口
- [ ] 迁移 `DependencyContainer` 实现到基础设施层
- [ ] 更新所有容器相关导入
- [ ] 更新服务绑定配置
- [ ] 全面测试依赖注入系统
- [ ] 性能基准测试

#### 影响文件
```
src/services/container/core/container.py
src/services/workflow/workflow_service_factory.py
src/services/container/bindings/*.py
src/services/container/core/test_container.py
```

#### 验收标准
- 依赖注入功能完全正常
- 所有服务绑定正常
- 性能无回归
- 所有测试通过

## 📁 目标目录结构

```
src/infrastructure/interfaces/
├── __init__.py
├── common/
│   ├── __init__.py
│   └── enums.py          # ServiceLifetime
├── config/
│   ├── __init__.py
│   └── interfaces.py     # IConfigLoader, IConfigInheritanceHandler
├── storage/
│   ├── __init__.py
│   └── interfaces.py     # IStorage
└── container/
    ├── __init__.py
    └── interfaces.py     # IDependencyContainer
```

## 🔄 向后兼容性策略

### 兼容性层设计
在 `src/interfaces/common_infra.py` 中保留兼容性导入：

```python
# 向后兼容性导入 - 将在后续版本中废弃
import warnings

def _deprecation_warning():
    warnings.warn(
        "Import from src.interfaces.common_infra is deprecated. "
        "Please import from src.infrastructure.interfaces instead.",
        DeprecationWarning,
        stacklevel=3
    )

# ServiceLifetime
from src.infrastructure.interfaces.common.enums import ServiceLifetime

# IConfigLoader
from src.infrastructure.interfaces.config.interfaces import IConfigLoader

# IConfigInheritanceHandler
from src.infrastructure.interfaces.config.interfaces import IConfigInheritanceHandler

# IStorage
from src.infrastructure.interfaces.storage.interfaces import IStorage

# IDependencyContainer
from src.infrastructure.interfaces.container.interfaces import IDependencyContainer
```

### 废弃时间表
- **v1.0**: 发布兼容性层，开始废弃警告
- **v1.1**: 加强废弃警告
- **v1.2**: 移除兼容性层

## 🧪 测试策略

### 测试层级
1. **单元测试**: 验证每个接口的基本功能
2. **集成测试**: 验证接口与实现的集成
3. **系统测试**: 验证整个系统的功能
4. **性能测试**: 验证迁移后性能无回归

### 测试计划
- 每个阶段完成后运行相关测试
- 全部迁移完成后运行完整测试套件
- 进行性能基准测试

## 🚨 风险缓解措施

### 技术风险
1. **循环依赖**: 仔细设计导入路径，使用 TYPE_CHECKING
2. **性能回归**: 进行性能基准测试
3. **功能回归**: 全面测试覆盖

### 项目风险
1. **时间延期**: 分阶段实施，可灵活调整
2. **资源不足**: 优先保证核心功能
3. **沟通问题**: 及时更新文档和团队

## 📊 成功指标

### 技术指标
- [ ] 所有测试通过 (100%)
- [ ] 性能无回归 (<5%)
- [ ] 代码覆盖率保持 (>90%)
- [ ] 无循环依赖

### 架构指标
- [ ] 依赖关系清晰
- [ ] 分层架构明确
- [ ] 接口职责单一
- [ ] 可维护性提升

## 📅 时间表

| 阶段 | 任务 | 预计时间 | 开始日期 | 结束日期 |
|------|------|----------|----------|----------|
| 1 | 基础设施准备 | 1天 | Week 1 Day 1 | Week 1 Day 1 |
| 2 | ServiceLifetime 迁移 | 1天 | Week 1 Day 2 | Week 1 Day 2 |
| 3 | IConfigInheritanceHandler 迁移 | 2天 | Week 1 Day 3 | Week 1 Day 4 |
| 4 | IStorage 迁移 | 3天 | Week 1 Day 5 | Week 2 Day 2 |
| 5 | IConfigLoader 迁移 | 5天 | Week 2 Day 3 | Week 3 Day 2 |
| 6 | IDependencyContainer 迁移 | 7天 | Week 3 Day 3 | Week 4 Day 3 |
| 7 | 测试和优化 | 2天 | Week 4 Day 4 | Week 4 Day 5 |

**总计**: 21天 (约4周)

## 🎯 关键里程碑

1. **Week 1 结束**: 完成低风险接口迁移
2. **Week 2 结束**: 完成中等风险接口迁移
3. **Week 3 结束**: 完成所有接口迁移
4. **Week 4 结束**: 完成测试和优化

## 📝 总结

这个迁移策略基于详细的风险评估和影响分析，采用分阶段、低风险的方式实施。通过优先处理简单接口，逐步积累经验，确保复杂接口的迁移成功。同时，向后兼容性策略确保了迁移过程的平滑过渡。

关键成功因素：
1. 严格按照优先级顺序执行
2. 每个阶段都进行充分测试
3. 保持向后兼容性
4. 及时沟通和文档更新