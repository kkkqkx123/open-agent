# Windows环境下ESC和Alt按键处理机制

## 问题背景

在Windows终端环境中，Alt键组合的处理与其他操作系统（如Unix/Linux）存在显著差异。这种差异导致了TUI应用程序中Alt快捷键和ESC键处理的混淆问题。windows中esc和alt都会被解析为escape，且code一样。区别仅在于前者会立刻返回，后者会等待输入数字，若没有数字则不会返回。故可以使用超时机制区分单独的esc和alt(暂时使用100ms)。
这种处理下按完esc马上按数字等价于alt+数字，但这并非不可接受。需要优化可以减少超时时长

## 问题分析

### Windows终端的特殊行为

在Windows终端中，当用户按下Alt+数字键时，系统会将其分解为两个独立的按键事件：
1. 首先发送ESC键（`\x1b`）
2. 然后发送对应的数字字符

例如，按下Alt+1会产生以下两个事件：
- `KEY_ESCAPE` (ESC键)
- `'1'` (数字1字符)

这种行为与Unix/Linux系统不同，在Unix/Linux系统中Alt+数字键通常会产生带有高位的字符（如Alt+1产生ASCII码为129的字符）。

### 原始实现的问题

原始实现使用了一个超时线程来处理ESC键，这种方式存在以下问题：
1. 线程管理复杂，容易出现竞态条件
2. ESC键可能被错误地消费，导致无法正常工作
3. 在某些情况下，ESC键和Alt键组合的处理会相互干扰

### 修复过程中的问题

在第一次修复中，我们尝试通过调用`self._process_key("escape")`来处理超时的ESC键，但这导致了问题：
- 当ESC键超时后，再次调用`_process_key("escape")`会重新进入ESC键处理逻辑
- 这会重新设置`_pending_alt_key`标志，导致无限循环或重复处理

### 返回主界面逻辑的问题

在TUI应用程序中，ESC键的处理逻辑存在状态同步问题：
- `_handle_escape_key`方法会同时调用`self.subview_controller.return_to_main_view()`和`self.state_manager.current_subview = None`
- 这导致了状态管理器和子界面控制器之间的状态不一致
- 在下一个UI更新周期中，`update_ui`方法会尝试同步状态，可能导致状态冲突

### 日志记录不足的问题

原始实现中，ESC键和Alt键的处理以及界面切换无法在日志中体现，这使得调试和问题排查变得困难。

## 解决方案

### 核心思路

采用基于主事件循环的超时检查机制，而不是使用单独的超时线程。同时确保ESC键超时后能正确调用处理器，而不是再次进入处理循环。

### 实现细节

#### 1. 状态管理

在事件引擎中添加以下状态变量：
```python
# 用于处理Windows终端中Alt+数字键的特殊逻辑
self._pending_escape: bool = False  # 标记是否正在等待可能的Alt键组合
self._alt_key_timeout: float = 0.1  # 100ms超时
self._last_escape_time: float = 0.0  # ESC键按下的时间
```

#### 2. ESC键处理

当检测到ESC键时：
1. 记录当前时间戳
2. 设置_pending_escape标志
3. 立即返回，等待下一个按键事件

```python
if key_str == "escape":
    self.tui_logger.debug_key_event(key_str, False, "key_pressed")
    # 记录ESC键按下的时间
    import time
    current_time = time.time()
    self._last_escape_time = current_time
    self._pending_escape = True
```

#### 3. Alt键组合处理

当_pending_escape存在时，检查下一个按键是否为数字：
```python
# 处理Windows终端中Alt+数字键的特殊逻辑
if self._pending_escape:
    self._pending_escape = False
    
    # 检查当前按键是否是数字
    if key_str.startswith("char:") and len(key_str) == 6 and key_str[5].isdigit():
        # 构造Alt键组合
        alt_key = f"alt_{key_str[5]}"
        self.tui_logger.debug_key_event(alt_key, False, "alt_key_detected")
        # 检查是否有对应的Alt键处理器
        if alt_key in self.key_handlers:
            if self.key_handlers[alt_key](alt_key):
                self.tui_logger.debug_key_event(alt_key, True, "alt_key_handled")
                return
        # 如果没有处理器，将两个按键分别处理
        # 先处理之前的ESC键
        if "escape" in self.key_handlers:
            self.key_handlers["escape"]("escape")
        elif self.global_key_handler:
            self.global_key_handler("escape")
        # 再处理当前的数字键
        if self.input_component_handler:
            result = self.input_component_handler(key_str)
            if result is not None and self.input_result_handler:
                self.input_result_handler(result)
        return
    else:
        # 不是数字键，先处理之前缓存的ESC键
        self.tui_logger.debug_key_event("escape", True, "escape_key_processed")
        if "escape" in self.key_handlers:
            self.key_handlers["escape"]("escape")
        elif self.global_key_handler:
            self.global_key_handler("escape")
        # 继续处理当前按键
```

#### 4. 超时检查

在主事件循环中定期检查ESC键是否超时：
```python
def _check_escape_timeout(self) -> None:
    """检查ESC键是否超时，如果超时则处理为单独的ESC键"""
    import time
    if self._pending_escape:
        current_time = time.time()
        if current_time - self._last_escape_time > self._alt_key_timeout:
            # 超时，处理为单独的ESC键
            self.tui_logger.debug_key_event("escape", True, "timeout_handler")
            self._pending_escape = False
            # 直接调用ESC键处理器，而不是再次进入_process_key
            if "escape" in self.key_handlers:
                self.key_handlers["escape"]("escape")
            elif self.global_key_handler:
                self.global_key_handler("escape")
```

主事件循环中调用超时检查：
```python
# 主事件循环
while self.running:
    try:
        # 处理队列中的输入
        try:
            while not self.input_queue.empty():
                key_str = self.input_queue.get_nowait()
                self._process_key(key_str)
        except queue.Empty:
            pass
        
        # 检查ESC键超时
        self._check_escape_timeout()
        
        # 短暂休眠以减少CPU使用率
        time.sleep(0.05)
```

## 处理流程

### 1. Alt+数字键处理流程

1. 用户按下Alt+1
2. Windows终端发送ESC键事件
3. 事件引擎记录ESC键时间并设置_pending_escape标志
4. Windows终端发送数字'1'事件
5. 事件引擎检测到_pending_escape存在且当前按键为数字
6. 组合成alt_1事件并处理

### 2. 单独ESC键处理流程

1. 用户按下ESC键
2. 事件引擎记录ESC键时间并设置_pending_escape标志
3. 在100ms内没有收到数字键
4. 超时检查发现超时
5. 直接调用ESC键处理器，触发返回主界面功能

### 3. ESC键后按数字键处理流程

1. 用户按下ESC键
2. 事件引擎记录ESC键时间并设置_pending_escape标志
3. 用户等待几秒后按下数字键'1'
4. 超时检查发现已超时，清除_pending_escape标志
5. 直接调用ESC键处理器处理之前的ESC键
6. 数字键'1'作为单独事件处理

## 修复的关键点

### 问题1：ESC键与Alt键处理逻辑混淆
- **解决方案**：通过使用_pending_escape标志而不是_pending_alt_key，正确区分了ESC键和Alt键组合的处理逻辑

### 问题2：ESC键超时处理导致的无限循环
- **解决方案**：修改超时处理逻辑，当ESC键超时时，直接调用ESC键处理器而不是再次进入`_process_key`方法

### 问题3：ESC键返回主界面时的状态同步问题
- **解决方案**：在`_handle_escape_key`方法中，只调用`self.subview_controller.return_to_main_view()`，不再手动同步状态管理器的状态，让`update_ui`方法自动同步

### 问题4：日志记录不足
- **解决方案**：在事件引擎和TUI应用中增强日志记录，详细记录ESC键和Alt键的处理过程以及界面切换事件

## 测试验证

创建了测试脚本`test_alt_esc_simple.py`来验证修复后的功能：
- Alt+数字键组合能正确识别和处理
- 单独的ESC键能正常工作并触发返回主界面功能
- ESC键后等待几秒再按数字键能正确分别处理

## 日志记录增强

通过增强日志记录功能，现在可以在TUI日志文件中查看到以下信息：
1. ESC键和Alt键的按键事件
2. ESC键和Alt键的处理过程
3. 界面切换事件
4. 超时处理事件

这使得调试和问题排查变得更加容易。

## 总结

通过采用基于主事件循环的超时检查机制，并确保ESC键超时后直接调用处理器而不是再次进入处理循环，我们成功解决了Windows环境下ESC键和Alt键组合处理的混淆问题。这种实现方式具有以下优点：

1. **稳定性**：避免了多线程带来的竞态条件
2. **准确性**：能够准确区分Alt键组合和单独的按键
3. **兼容性**：在不同操作系统和终端环境下都能正常工作
4. **可维护性**：代码结构清晰，易于理解和维护
5. **功能完整性**：确保ESC键能正确触发返回主界面的功能
6. **避免循环**：防止ESC键超时处理导致的无限循环问题
7. **正确区分**：通过使用_pending_escape标志而不是_pending_alt_key，正确区分了ESC键和Alt键组合的处理逻辑
8. **状态同步**：修复了ESC键返回主界面时的状态同步问题，确保子界面控制器和状态管理器之间的状态一致性
9. **日志记录**：增强了日志记录功能，便于调试和问题排查