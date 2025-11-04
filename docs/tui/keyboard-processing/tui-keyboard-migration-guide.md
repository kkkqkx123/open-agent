# TUI键盘处理改进 - 迁移指南

## 迁移概述

本指南提供逐步将现有TUI键盘处理系统升级为现代化实现的详细步骤，保持完全向后兼容。

## 迁移原则

1. **渐进式迁移**：分阶段实施，避免一次性大规模修改
2. **向后兼容**：现有代码无需修改即可继续工作
3. **测试驱动**：每个阶段都有完整的测试覆盖
4. **风险最小**：可随时回滚到原始版本

## 迁移阶段

### 阶段一：基础组件添加（低风险）

**目标**：添加新的Key类和KeyParser，不影响现有功能

#### 步骤1.1：添加Key类
```bash
# 创建新文件
src/presentation/tui/key.py
```

#### 步骤1.2：添加KeyParser类
```bash
# 创建新文件
src/presentation/tui/key_parser.py
```

#### 步骤1.3：添加调试工具
```bash
# 创建新文件
src/presentation/tui/debug/sequence_monitor.py
```

#### 步骤1.4：添加单元测试
```bash
# 创建测试文件
tests/test_key.py
tests/test_key_parser.py
tests/test_sequence_monitor.py
```

#### 验证步骤
```bash
# 运行测试
python -m pytest tests/test_key.py -v
python -m pytest tests/test_key_parser.py -v
python -m pytest tests/test_sequence_monitor.py -v

# 验证现有功能不受影响
python -m pytest tests/test_event_engine.py -v
```

### 阶段二：引擎增强（中风险）

**目标**：增强EventEngine，支持Key对象但保持向后兼容

#### 步骤2.1：备份现有EventEngine
```bash
cp src/presentation/tui/event_engine.py src/presentation/tui/event_engine_backup.py
```

#### 步骤2.2：修改EventEngine
```python
# 在现有EventEngine中添加增强功能
# 主要修改：
# 1. 导入Key和KeyParser
# 2. 添加_parse_key_input方法
# 3. 修改_process_key方法
# 4. 添加调试支持
```

#### 步骤2.3：添加配置选项
```python
# 在TUIConfig中添加：
enhanced_keyboard_support: bool = True
debug_key_sequences: bool = False
```

#### 验证步骤
```bash
# 运行所有测试
python -m pytest tests/ -v

# 手动测试基本功能
python main.py  # 启动应用，测试基本按键
```

### 阶段三：应用集成（中风险）

**目标**：在应用层使用新的Key对象功能

#### 步骤3.1：修改TUIApp
```python
# 在TUIApp中添加调试命令
# 添加按键序列监控功能
```

#### 步骤3.2：添加调试命令
```python
# 在应用中添加快捷键：
# Ctrl+Alt+D: 切换调试模式
# Ctrl+Alt+S: 显示按键统计
```

#### 步骤3.3：添加配置选项
```yaml
# 在配置文件中添加：
tui:
  enhanced_keyboard_support: true
  debug_key_sequences: false
  enable_kitty_protocol: true
```

### 阶段四：功能验证（低风险）

**目标**：全面验证新功能，确保稳定性

#### 步骤4.1：协议测试
```bash
# 测试Kitty协议支持
# 在支持Kitty协议的终端中测试
kitty python main.py

# 测试传统Escape序列
# 在标准终端中测试
python main.py
```

#### 步骤4.2：性能测试
```bash
# 测试按键响应时间
# 测试内存使用情况
# 测试CPU使用率
```

#### 步骤4.3：兼容性测试
```bash
# 测试不同终端
# - Windows Terminal
# - PowerShell
# - CMD
# - Git Bash
# - WSL
```

## 迁移检查清单

### 代码检查
- [ ] Key类实现完整
- [ ] KeyParser实现完整
- [ ] EventEngine增强完整
- [ ] 调试工具实现完整
- [ ] 单元测试覆盖完整
- [ ] 向后兼容性验证

### 功能检查
- [ ] 基本按键功能正常
- [ ] 组合键功能正常
- [ ] 功能键功能正常
- [ ] Kitty协议支持正常
- [ ] 传统Escape序列支持正常
- [ ] 调试功能正常

### 性能检查
- [ ] 按键响应时间 < 50ms
- [ ] 内存使用无异常增长
- [ ] CPU使用率正常
- [ ] 无内存泄漏

### 兼容性检查
- [ ] Windows Terminal正常
- [ ] PowerShell正常
- [ ] CMD正常
- [ ] Git Bash正常
- [ ] WSL正常

## 回滚方案

### 紧急回滚
```bash
# 如果需要紧急回滚，只需恢复备份文件
cp src/presentation/tui/event_engine_backup.py src/presentation/tui/event_engine.py

# 移除新文件（可选）
rm src/presentation/tui/key.py
rm src/presentation/tui/key_parser.py
rm src/presentation/tui/debug/sequence_monitor.py
```

### 配置回滚
```yaml
# 在配置文件中禁用增强功能
tui:
  enhanced_keyboard_support: false
  debug_key_sequences: false
```

## 最佳实践

### 1. 渐进式采用
```python
# 新代码可以逐步采用Key对象
def handle_key_new(key: Union[str, Key]) -> bool:
    if isinstance(key, Key):
        # 使用新功能
        if key.matches("enter", ctrl=True):
            return True
    else:
        # 保持兼容
        if key == "enter":
            return True
    return False
```

### 2. 调试使用
```python
# 在开发阶段启用调试
config = TUIConfig(
    enhanced_keyboard_support=True,
    debug_key_sequences=True  # 开发时启用
)

# 生产环境关闭调试
config = TUIConfig(
    enhanced_keyboard_support=True,
    debug_key_sequences=False  # 生产时关闭
)
```

### 3. 错误处理
```python
# 增强错误处理
def safe_key_handler(key: Union[str, Key]) -> bool:
    try:
        if isinstance(key, Key):
            return handle_key_with_object(key)
        else:
            return handle_key_with_string(key)
    except Exception as e:
        logger.error(f"按键处理错误: {e}")
        return False
```

## 常见问题

### Q1: 迁移后按键不响应？
**A**: 检查配置是否启用了增强支持：
```yaml
enhanced_keyboard_support: true
```

### Q2: 调试信息太多？
**A**: 关闭调试模式：
```yaml
debug_key_sequences: false
```

### Q3: Kitty协议不工作？
**A**: 确保终端支持Kitty协议，检查配置：
```yaml
enable_kitty_protocol: true
```

### Q4: 性能下降？
**A**: 检查序列缓冲区大小，适当调整：
```yaml
max_sequence_length: 16  # 减小缓冲区
```

### Q5: 如何验证迁移成功？
**A**: 使用调试命令：
```
Ctrl+Alt+D: 启用调试
Ctrl+Alt+S: 显示统计
```

## 迁移完成标准

### 功能标准
- ✅ 所有现有功能正常工作
- ✅ 新Key对象功能可用
- ✅ Kitty协议支持正常
- ✅ 调试工具可用

### 性能标准
- ✅ 按键响应时间 < 50ms
- ✅ 内存使用无异常
- ✅ CPU使用率正常

### 质量标准
- ✅ 单元测试通过率 100%
- ✅ 集成测试通过率 100%
- ✅ 代码覆盖率 > 80%

### 文档标准
- ✅ 代码注释完整
- ✅ 使用文档更新
- ✅ 迁移指南完整

## 后续优化

迁移完成后，可以考虑以下优化：

1. **性能优化**：进一步优化解析算法
2. **协议扩展**：支持更多终端协议
3. **功能增强**：添加更多调试功能
4. **文档完善**：编写更详细的使用指南

通过遵循这个迁移指南，可以安全、高效地将TUI键盘处理系统升级为现代化实现。