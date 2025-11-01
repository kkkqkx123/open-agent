# Windows环境下ESC和Alt按键处理机制

## 问题背景

在Windows终端环境中，Alt键组合的处理与其他操作系统（如Unix/Linux）存在显著差异。这种差异导致了TUI应用程序中Alt快捷键和ESC键处理的混淆问题。

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

## 解决方案

### 核心思路

采用基于主事件循环的超时检查机制，而不是使用单独的超时线程。这种方法更加稳定和可靠。

### 实现细节

#### 1. 状态管理

在事件引擎中添加以下状态变量：
```python
# 用于处理Windows终端中Alt+数字键的特殊逻辑
self._pending_alt_key: Optional[str] = None  # 缓存ESC键
self._alt_key_timeout: float = 0.1  # 100ms超时
self._last_escape_time: float = 0.0  # ESC键按下的时间
```

#### 2. ESC键处理

当检测到ESC键时：
1. 记录当前时间戳
2. 设置_pending_alt_key标志
3. 立即返回，等待下一个按键事件

```python
if key_str == "escape":
    # 记录ESC键按下的时间
    import time
    current_time = time.time()
    self._last_escape_time = current_time
    
    # 在Windows终端中，Alt+数字键会先发送ESC键
    # 我们需要等待下一个按键来判断是否是Alt键组合
    self._pending_alt_key = key_str
    return
```

#### 3. Alt键组合处理

当_pending_alt_key存在时，检查下一个按键是否为数字：
```python
# 处理Windows终端中Alt+数字键的特殊逻辑
if self._pending_alt_key:
    pending_alt_key = self._pending_alt_key
    self._pending_alt_key = None
    
    # 检查当前按键是否是数字
    if key_str.startswith("char:") and len(key_str) == 6 and key_str[5].isdigit():
        # 构造Alt键组合
        alt_key = f"alt_{key_str[5]}"
        # 检查是否有对应的Alt键处理器
        if alt_key in self.key_handlers:
            if self.key_handlers[alt_key](alt_key):
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
    if self._pending_alt_key:
        current_time = time.time()
        if current_time - self._last_escape_time > self._alt_key_timeout:
            # 超时，处理为单独的ESC键
            self._pending_alt_key = None
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
3. 事件引擎记录ESC键时间并设置_pending_alt_key标志
4. Windows终端发送数字'1'事件
5. 事件引擎检测到_pending_alt_key存在且当前按键为数字
6. 组合成alt_1事件并处理

### 2. 单独ESC键处理流程

1. 用户按下ESC键
2. 事件引擎记录ESC键时间并设置_pending_alt_key标志
3. 在100ms内没有收到数字键
4. 超时检查发现超时
5. 将ESC键作为单独事件处理

### 3. ESC键后按数字键处理流程

1. 用户按下ESC键
2. 事件引擎记录ESC键时间并设置_pending_alt_key标志
3. 用户等待几秒后按下数字键'1'
4. 超时检查发现已超时，清除_pending_alt_key标志
5. 数字键'1'作为单独事件处理

## 测试验证

创建了测试脚本`test_windows_alt_esc.py`来验证修复后的功能：
- Alt+数字键组合能正确识别和处理
- 单独的ESC键能正常工作
- ESC键后等待几秒再按数字键能正确分别处理

## 总结

通过采用基于主事件循环的超时检查机制，我们成功解决了Windows环境下ESC键和Alt键组合处理的混淆问题。这种实现方式具有以下优点：

1. **稳定性**：避免了多线程带来的竞态条件
2. **准确性**：能够准确区分Alt键组合和单独的按键
3. **兼容性**：在不同操作系统和终端环境下都能正常工作
4. **可维护性**：代码结构清晰，易于理解和维护