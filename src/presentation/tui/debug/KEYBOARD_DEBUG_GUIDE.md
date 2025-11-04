# 键盘调试工具使用指南

本文档介绍如何使用新的键盘调试工具，包括SequenceMonitor和增强配置系统。

## 功能概述

新的键盘调试系统包含以下功能：

1. **SequenceMonitor** - 按键序列监控工具
2. **增强键盘配置** - 支持更多键盘相关配置选项
3. **调试示例** - 演示如何使用调试功能

## SequenceMonitor 使用

### 基本功能

SequenceMonitor 可以：
- 记录所有按键序列
- 统计按键使用频率
- 分析按键模式
- 导出/导入监控数据

### 在 EventEngine 中使用

```python
from src.presentation.tui.event_engine import EventEngine
from src.presentation.tui.config import TUIConfig, KeyboardConfig

# 创建配置
config = TUIConfig()
config.keyboard.debug_key_sequences = True  # 启用序列监控

# 创建事件引擎
engine = EventEngine(config.to_dict())

# 启动引擎
engine.start()

# 获取统计信息
stats = engine.get_statistics()
print(f"总按键数: {stats['total_keys']}")
print(f"序列数: {stats['sequence_stats']['total_sequences']}")

# 停止引擎（会自动保存数据）
engine.stop()
```

### 直接使用 SequenceMonitor

```python
from src.presentation.tui.debug.sequence_monitor import SequenceMonitor

# 创建监控器
monitor = SequenceMonitor()

# 添加按键序列
monitor.add_sequence("\\x1b[A", "UP")
monitor.add_sequence("\\x1b[B", "DOWN")

# 获取统计信息
stats = monitor.get_stats()
print(f"总序列数: {stats['total_sequences']}")

# 获取常用序列
common = monitor.get_common_sequences(limit=5)
for seq, count in common:
    print(f"{seq}: {count} 次")

# 保存到文件
monitor.save_to_file("sequences.json")

# 从文件加载
monitor.load_from_file("sequences.json")

# 打印最近序列
monitor.print_recent_sequences(limit=10)
```

## 键盘配置选项

### KeyboardConfig 配置项

```python
from src.presentation.tui.config import KeyboardConfig

config = KeyboardConfig(
    enhanced_key_support=True,          # 启用增强按键支持
    debug_key_sequences=True,           # 启用按键序列调试
    kitty_keyboard_protocol=False,     # Kitty键盘协议支持
    key_mappings={                     # 自定义按键映射
        'ctrl+q': 'quit',
        'ctrl+s': 'save',
        'f1': 'help'
    }
)
```

### 配置说明

- **enhanced_key_support**: 启用增强按键识别和处理
- **debug_key_sequences**: 启用按键序列监控和调试
- **kitty_keyboard_protocol**: 启用Kitty终端键盘协议支持
- **key_mappings**: 自定义按键映射字典

## 调试示例

### 运行完整调试演示

```bash
cd src/presentation/tui/debug
python keyboard_debug_example.py
```

功能：
- Ctrl+D: 显示调试信息
- Ctrl+S: 保存按键序列
- Ctrl+Q: 退出

### 创建简单调试脚本

```bash
python keyboard_debug_example.py --simple
python simple_keyboard_debug.py
```

### 在应用中使用调试功能

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_engine import EventEngine
from config import TUIConfig

def main():
    # 创建调试配置
    config = TUIConfig()
    config.keyboard.debug_key_sequences = True
    
    # 创建事件引擎
    engine = EventEngine(config.to_dict())
    
    try:
        engine.start()
        
        # 你的应用逻辑
        while engine.running:
            # 处理业务逻辑
            stats = engine.get_statistics()
            if stats['total_keys'] > 100:
                print("已处理超过100个按键！")
                
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()

if __name__ == "__main__":
    main()
```

## 调试输出格式

### 基本统计信息

```
总按键数: 150
序列检测: 25
Alt组合: 10
错误数: 0
```

### 序列统计信息

```
序列统计:
  总序列数: 45
  唯一序列数: 15
  最近序列数: 20
```

### 常用序列

```
最常用序列:
  ENTER: 25 次
  UP: 20 次
  DOWN: 18 次
  CTRL+C: 15 次
  TAB: 12 次
```

## 最佳实践

### 1. 开发阶段

- 启用 `debug_key_sequences` 来监控按键使用模式
- 使用 `enhanced_key_support` 获得更好的按键识别
- 定期查看统计信息以优化用户交互

### 2. 生产环境

- 关闭调试功能以提高性能
- 保留必要的按键映射配置
- 考虑使用配置文件管理不同环境的设置

### 3. 性能优化

- 序列监控会增加内存使用，定期清理数据
- 大量按键时考虑限制监控数据的保存
- 使用合适的日志级别避免过多输出

### 4. 调试技巧

- 使用 `engine.get_statistics()` 获取实时统计
- 保存序列数据到文件进行离线分析
- 结合其他调试工具使用

## 故障排除

### 常见问题

1. **序列监控不工作**
   - 确保 `debug_key_sequences=True`
   - 检查 EventEngine 是否正确启动

2. **按键识别不准确**
   - 启用 `enhanced_key_support`
   - 检查终端兼容性

3. **性能问题**
   - 关闭不必要的调试功能
   - 定期清理监控数据

### 调试命令

```python
# 检查配置
print(config.keyboard.to_dict())

# 查看引擎状态
print(f"Engine running: {engine.running}")
print(f"Sequence monitor: {engine.sequence_monitor is not None}")

# 获取详细统计
stats = engine.get_statistics()
import json
print(json.dumps(stats, indent=2, ensure_ascii=False))
```

## 扩展功能

### 自定义序列分析

```python
def analyze_sequences(monitor):
    """自定义序列分析"""
    stats = monitor.get_stats()
    sequences = stats['recent_sequences']
    
    # 分析特定模式
    navigation_keys = ['UP', 'DOWN', 'LEFT', 'RIGHT']
    nav_count = sum(1 for seq in sequences if seq['key'] in navigation_keys)
    
    print(f"导航键使用比例: {nav_count/len(sequences)*100:.1f}%")

# 使用自定义分析
analyze_sequences(engine.sequence_monitor)
```

### 集成到日志系统

```python
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 在调试输出中添加日志
if engine.debug_enabled:
    logger.debug(f"Key stats: {engine.get_statistics()}")
```

这个调试系统为TUI应用提供了强大的按键监控和分析能力，帮助开发者更好地理解和优化用户交互。