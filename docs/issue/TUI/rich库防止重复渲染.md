# Rich库防止重复渲染问题解决方案

## 问题描述

TUI应用在启动时出现重复渲染问题，且每次重新渲染时旧的UI没有完全删除，导致终端输出大量重复内容。

## 根本原因分析

1. **Rich库的默认行为**：Rich的Live类默认不在全屏模式下运行，导致每次更新时都会在终端中累积显示，而不是替换之前的显示内容
2. **频繁的UI更新**：主循环每50毫秒调用一次`update_ui()`，即使内容没有变化
3. **缺少内容变化检测**：每次调用都强制更新所有UI组件，即使内容没有实际变化

## 解决方案

### 1. 启用全屏模式

在`src/presentation/tui/app.py`中，为`Live`对象添加`screen=True`参数：

```python
# 启动Live显示
with Live(layout, console=self.console, refresh_per_second=self.config.behavior.refresh_rate, screen=True) as live:
```

### 2. 实现内容变化检测

在`src/presentation/tui/render_controller.py`中为所有UI更新方法添加内容变化检测：

- `_update_header()`
- `_update_sidebar()`
- `_update_main_content()`
- `_update_input_area()`
- `_update_langgraph_panel()`
- `_update_status_bar()`
- `_update_dialogs()`
- `_check_error_feedback_panel()`
- `_render_subview()`
- `_update_subview_header()`
- `show_welcome_message()`
- `_on_layout_changed()`

### 3. 优化更新频率

- 在主循环中添加最小更新间隔检查
- 在应用初始化时添加 `_min_update_interval` 和 `_last_update_time` 属性

### 4. 添加性能监控

添加了渲染性能统计功能，包括：
- 总更新次数
- 跳过的无用更新次数
- 平均更新间隔
- 渲染效率计算

## 效果

1. **减少重复渲染**：通过内容变化检测，只有在内容真正变化时才进行渲染
2. **提升性能**：大量减少了不必要的UI更新，显著提高了性能
3. **改善用户体验**：使用全屏模式确保只显示最新UI，避免了内容累积问题
4. **性能监控**：可以监控渲染效率，了解跳过多少无用更新

## 性能提升统计

修复后的TUI应用能够：
- 跳过大量无用的UI更新
- 减少CPU使用率
- 避免终端输出累积
- 提供流畅的用户体验