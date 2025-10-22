# TUI调试日志使用指南

## 概述

本指南介绍了如何使用新的TUI调试日志系统，该系统为TUI界面提供了专门的调试日志管理功能。

## TUI日志系统结构

TUI日志系统包含以下组件：

1. **TUILoggerManager** - TUI日志管理器，负责管理TUI日志记录器实例
2. **TUIDebugLogger** - TUI调试日志记录器，提供专门的调试功能
3. **日志记录方法** - 提供各种类型的日志记录方法

## 启用TUI调试模式

有多种方式可以启用TUI调试模式：

### 1. 环境变量方式

```bash
export TUI_DEBUG=1
python -m src.presentation.tui.app
```

### 2. 代码中启用

```python
from src.presentation.tui.app import TUIApp

app = TUIApp()
app.enable_tui_debug(True)  # 启用调试模式
```

## 日志类型

TUI调试日志系统支持以下类型的日志记录：

### 1. 组件事件日志
```python
tui_logger.debug_component_event("component_name", "event_type", **kwargs)
```

### 2. 输入处理日志
```python
tui_logger.debug_input_handling("input_type", "content", **kwargs)
```

### 3. UI状态变更日志
```python
tui_logger.debug_ui_state_change("component", old_state, new_state, **kwargs)
```

### 4. 工作流操作日志
```python
tui_logger.debug_workflow_operation("operation", **kwargs)
```

### 5. 会话操作日志
```python
tui_logger.debug_session_operation("operation", session_id, **kwargs)
```

### 6. 按键事件日志
```python
tui_logger.debug_key_event("key", handled, context, **kwargs)
```

### 7. 子界面导航日志
```python
tui_logger.debug_subview_navigation("from_view", "to_view", **kwargs)
```

### 8. 渲染操作日志
```python
tui_logger.debug_render_operation("component", "operation", **kwargs)
```

### 9. 错误处理日志
```python
tui_logger.debug_error_handling("error_type", "error_message", **kwargs)
```

## 在TUI应用中使用日志

在TUIApp类中，可以通过`self.tui_logger`访问日志记录器：

```python
def _handle_input_submit(self, input_text: str) -> None:
    # 记录输入处理
    self.tui_logger.debug_input_handling("user_input", input_text)
    
    # 添加用户消息到历史
    self.state_manager.add_user_message(input_text)
    
    # 添加到主内容组件
    self.main_content_component.add_user_message(input_text)
    
    # 处理用户输入
    self._process_user_input(input_text)
```

## 日志级别

TUI日志系统会根据调试模式自动调整日志级别：

- 当调试模式启用时，日志级别为DEBUG
- 当调试模式禁用时，只记录INFO及以上级别的日志

## 调试场景示例

### 1. 跟踪会话操作

```python
def _on_session_selected(self, session_id: str) -> None:
    self.tui_logger.debug_session_operation("session_selected", session_id)
    # ... 会话选择逻辑
```

### 2. 跟踪UI状态变化

```python
def _switch_to_subview(self, subview_name: str) -> bool:
    self.tui_logger.debug_subview_navigation(
        self.state_manager.current_subview or "main", 
        subview_name
    )
    # ... 子界面切换逻辑
```

### 3. 跟踪按键处理

```python
def _handle_global_key(self, key: str) -> bool:
    self.tui_logger.debug_key_event(key, True, "global_handler")
    # ... 按键处理逻辑
```

## 日志输出

TUI调试日志将输出到配置的全局日志处理器，通常包括控制台和文件输出。日志会带有"TUI"前缀以区分其他日志。

## 最佳实践

1. 在关键操作点添加日志记录，特别是用户交互和状态变更
2. 使用描述性的组件名称和事件类型
3. 在调试模式下记录详细的上下文信息
4. 避免在日志中记录敏感信息
5. 使用合适的日志级别