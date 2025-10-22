# TUI布局管理器优化方案

## 问题总结

当前TUI布局管理器在调整终端大小时存在以下核心问题：

1. **布局重建导致内容丢失** - 断点变化时完全重建布局
2. **区域尺寸调整不完整** - 只调整部分区域，缺乏整体协调
3. **断点切换不流畅** - 缺乏缓冲机制和平滑过渡
4. **状态同步不及时** - 与渲染控制器集成不完善

## 优化目标

1. **保持内容连续性** - 调整布局时不丢失用户输入和状态
2. **提供平滑过渡** - 断点切换时有视觉过渡效果
3. **智能尺寸分配** - 根据内容需求动态调整区域尺寸
4. **性能优化** - 减少不必要的布局重建

## 详细实现方案

### 1. 改进布局管理器核心逻辑

#### 1.1 渐进式布局调整

```python
class ImprovedLayoutManager(LayoutManager):
    def __init__(self, config: Optional[LayoutConfig] = None) -> None:
        super().__init__(config)
        # 新增属性
        self.layout_changed_callbacks: List[Callable[[str, str], None]] = []
        self.region_content_cache: Dict[LayoutRegion, Any] = {}
        self.last_resize_time: float = 0
        self.resize_debounce_delay: float = 0.1  # 100ms防抖延迟
    
    def resize_layout(self, terminal_size: Tuple[int, int]) -> None:
        """改进的布局调整方法"""
        import time
        current_time = time.time()
        
        # 防抖处理，避免频繁调整
        if current_time - self.last_resize_time < self.resize_debounce_delay:
            return
        
        self.last_resize_time = current_time
        old_breakpoint = self.current_breakpoint
        self.terminal_size = terminal_size
        new_breakpoint = self._determine_breakpoint(terminal_size)
        
        # 缓存当前内容
        self._cache_region_contents()
        
        if old_breakpoint != new_breakpoint:
            # 断点变化，使用渐进式过渡
            self.current_breakpoint = new_breakpoint
            self._gradual_layout_transition(old_breakpoint, new_breakpoint)
        else:
            # 相同断点，只调整尺寸
            self._adjust_region_sizes_gradual()
        
        # 恢复缓存的内容
        self._restore_region_contents()
        
        # 触发布局变化回调
        self._trigger_layout_changed_callbacks()
```

#### 1.2 智能断点检测

```python
def _determine_breakpoint(self, terminal_size: Tuple[int, int]) -> str:
    """改进的断点检测，添加缓冲机制"""
    width, height = terminal_size
    
    # 断点配置
    breakpoints = {
        "xlarge": (140, 50),
        "large": (120, 40),
        "medium": (100, 30),
        "small": (80, 24)
    }
    
    # 添加缓冲阈值（避免频繁切换）
    buffer_threshold = 5
    
    # 检查当前断点是否仍然有效（带缓冲）
    if self.current_breakpoint:
        current_threshold = breakpoints[self.current_breakpoint]
        if (width >= current_threshold[0] - buffer_threshold and 
            height >= current_threshold[1] - buffer_threshold):
            return self.current_breakpoint
    
    # 按优先级查找合适的断点
    for breakpoint_name, (min_width, min_height) in sorted(
        breakpoints.items(),
        key=lambda x: x[1][0],  # 按宽度排序
        reverse=True
    ):
        if width >= min_width and height >= min_height:
            return breakpoint_name
    
    return "small"
```

#### 1.3 渐进式布局过渡

```python
def _gradual_layout_transition(self, old_breakpoint: str, new_breakpoint: str) -> None:
    """渐进式布局过渡"""
    # 创建新布局结构
    old_layout = self.layout
    self.layout = self._create_layout_structure(new_breakpoint)
    
    # 渐进式调整区域尺寸
    self._transition_region_sizes(old_breakpoint, new_breakpoint)
    
    # 渐进式调整区域可见性
    self._transition_region_visibility(old_breakpoint, new_breakpoint)

def _transition_region_sizes(self, old_breakpoint: str, new_breakpoint: str) -> None:
    """渐进式调整区域尺寸"""
    # 根据新旧断点计算过渡尺寸
    transition_sizes = self._calculate_transition_sizes(old_breakpoint, new_breakpoint)
    
    for region_name, target_size in transition_sizes.items():
        if self._has_region(region_name):
            # 使用动画效果调整尺寸
            self._animate_region_resize(region_name, target_size)

def _transition_region_visibility(self, old_breakpoint: str, new_breakpoint: str) -> None:
    """渐进式调整区域可见性"""
    old_visibility = self._get_breakpoint_visibility(old_breakpoint)
    new_visibility = self._get_breakpoint_visibility(new_breakpoint)
    
    for region in LayoutRegion:
        old_visible = old_visibility.get(region, False)
        new_visible = new_visibility.get(region, False)
        
        if old_visible != new_visible:
            # 添加淡入淡出效果
            self._animate_region_visibility(region, new_visible)
```

### 2. 内容缓存和恢复机制

```python
def _cache_region_contents(self) -> None:
    """缓存区域内容"""
    if not self.layout:
        return
    
    for region in LayoutRegion:
        region_name = region.value
        if self._has_region(region_name):
            try:
                # 获取当前区域内容
                region_layout = self.layout[region_name]
                if hasattr(region_layout, 'renderable'):
                    self.region_content_cache[region] = region_layout.renderable
            except (KeyError, AttributeError):
                continue

def _restore_region_contents(self) -> None:
    """恢复区域内容"""
    if not self.layout:
        return
    
    for region, content in self.region_content_cache.items():
        region_name = region.value
        if self._has_region(region_name) and content:
            try:
                self.layout[region_name].update(content)
            except (KeyError, AttributeError):
                continue
    
    # 清空缓存
    self.region_content_cache.clear()
```

### 3. 智能区域尺寸计算

```python
def _calculate_optimal_sizes(self) -> Dict[str, int]:
    """计算各区域最优尺寸"""
    width, height = self.terminal_size
    
    # 固定尺寸区域
    header_size = 3
    input_size = 3
    status_size = 1
    
    # 可用空间计算
    available_height = height - header_size - input_size - status_size
    
    if self.current_breakpoint in ["small", "medium"]:
        # 紧凑布局
        if self.current_breakpoint == "small":
            # 小屏幕：隐藏侧边栏
            return {
                "header": header_size,
                "main": available_height,
                "input": input_size,
                "status": status_size
            }
        else:
            # 中等屏幕：底部显示侧边栏
            sidebar_size = min(15, available_height // 3)
            main_size = available_height - sidebar_size
            return {
                "header": header_size,
                "main": main_size,
                "sidebar": sidebar_size,
                "input": input_size,
                "status": status_size
            }
    else:
        # 完整布局
        sidebar_size = min(25, width // 4)
        main_width = width - sidebar_size
        
        # 检查是否需要显示LangGraph面板
        if self.config.regions[LayoutRegion.LANGGRAPH].visible:
            langgraph_size = min(30, main_width // 3)
            main_width -= langgraph_size
        else:
            langgraph_size = 0
        
        return {
            "header": header_size,
            "sidebar": sidebar_size,
            "main": available_height,
            "langgraph": langgraph_size if langgraph_size > 0 else None,
            "input": input_size,
            "status": status_size
        }
```

### 4. 回调机制集成

```python
def register_layout_changed_callback(self, callback: Callable[[str, str], None]) -> None:
    """注册布局变化回调"""
    self.layout_changed_callbacks.append(callback)

def unregister_layout_changed_callback(self, callback: Callable[[str, str], None]) -> bool:
    """取消注册布局变化回调"""
    try:
        self.layout_changed_callbacks.remove(callback)
        return True
    except ValueError:
        return False

def _trigger_layout_changed_callbacks(self) -> None:
    """触发布局变化回调"""
    for callback in self.layout_changed_callbacks:
        try:
            callback(self.current_breakpoint, self.terminal_size)
        except Exception as e:
            import logging
            logging.warning(f"布局变化回调执行失败: {e}")
```

### 5. 渲染控制器集成改进

在渲染控制器中添加布局变化处理：

```python
class ImprovedRenderController(RenderController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 注册布局变化回调
        self.layout_manager.register_layout_changed_callback(self._on_layout_changed)
    
    def _on_layout_changed(self, breakpoint: str, terminal_size: Tuple[int, int]) -> None:
        """布局变化回调处理"""
        # 立即更新UI以响应布局变化
        if self.live:
            self.live.refresh()
        
        # 根据新布局调整组件显示
        self._adjust_components_to_layout(breakpoint, terminal_size)
    
    def _adjust_components_to_layout(self, breakpoint: str, terminal_size: Tuple[int, int]) -> None:
        """根据布局调整组件"""
        # 根据断点调整组件显示策略
        if breakpoint == "small":
            # 小屏幕优化
            self._optimize_for_small_screen()
        elif breakpoint == "medium":
            # 中等屏幕优化
            self._optimize_for_medium_screen()
        else:
            # 大屏幕优化
            self._optimize_for_large_screen()
```

## 实施计划

### 阶段一：核心功能修复（高优先级）
1. 实现内容缓存和恢复机制
2. 改进断点检测逻辑
3. 修复区域尺寸计算

### 阶段二：用户体验优化（中优先级）
1. 添加防抖机制
2. 实现渐进式布局过渡
3. 完善回调机制

### 阶段三：高级功能（低优先级）
1. 添加动画效果
2. 实现自适应内容显示
3. 性能优化和缓存策略

## 测试策略

### 单元测试
```python
def test_resize_with_content_preservation():
    """测试调整大小时内容保持"""
    manager = ImprovedLayoutManager()
    manager.create_layout((100, 30))
    
    # 设置测试内容
    test_content = "测试内容"
    manager.update_region_content(LayoutRegion.MAIN, test_content)
    
    # 调整尺寸
    manager.resize_layout((120, 40))
    
    # 验证内容保持
    assert manager.region_contents[LayoutRegion.MAIN] == test_content

def test_breakpoint_transition_smoothness():
    """测试断点切换平滑性"""
    manager = ImprovedLayoutManager()
    
    # 模拟连续尺寸变化
    sizes = [(85, 25), (95, 28), (105, 32), (115, 38)]
    breakpoint_changes = []
    
    for size in sizes:
        old_breakpoint = manager.current_breakpoint
        manager.resize_layout(size)
        new_breakpoint = manager.current_breakpoint
        if old_breakpoint != new_breakpoint:
            breakpoint_changes.append((old_breakpoint, new_breakpoint))
    
    # 验证断点切换次数合理
    assert len(breakpoint_changes) <= 2  # 最多切换2次
```

### 集成测试
```python
def test_layout_integration_with_render_controller():
    """测试布局管理器与渲染控制器的集成"""
    layout_manager = ImprovedLayoutManager()
    render_controller = ImprovedRenderController(layout_manager, components, subviews, config)
    
    # 模拟终端尺寸变化
    layout_manager.resize_layout((120, 40))
    
    # 验证UI正确更新
    assert render_controller.layout_manager.current_breakpoint == "large"
```

## 性能考虑

1. **防抖机制**：避免频繁布局调整
2. **内容缓存**：减少重复渲染
3. **增量更新**：只更新变化的部分
4. **懒加载**：按需创建布局元素

## 向后兼容性

所有改进都保持与现有API的兼容性，不会破坏现有功能。

---
**文档版本：** V1.0  
**创建时间：** 2025-10-22  
**负责人：** TUI开发团队