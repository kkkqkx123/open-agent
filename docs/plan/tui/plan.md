# TUI 布局优化方案

## 1. 背景与目标

- 当前版本在不同终端尺寸下存在区域缺失、布局切换迟滞、尺寸计算不准确等问题，导致交互体验不稳定。
- **目标：**  
  在不破坏现有组件体系的前提下，重新梳理响应式布局策略，确保核心功能区域（如输入栏）始终可用，尺寸计算符合视觉预期，并为后续扩展提供灵活的配置接口。

## 2. 核心问题概述

- **中等断点布局异常：**  
  输入栏被移除，且引入未注册、无内容更新逻辑的 `info` 区域，造成界面空缺。
  
- **布局重绘触发机制滞后：**  
  `resize_layout` 仅在宽高变化超过阈值时重建布局，导致跨断点调整（如 95→103）无法及时响应。

- **大屏布局逻辑不一致：**  
  `langgraph` 区域虽在配置和组件中存在，但在大屏布局中未创建，形成“逻辑存在但视图缺失”的矛盾。

- **尺寸计算方向混淆：**  
  宽高语义错乱，例如用 `available_height` 计算宽度；`get_region_size` 错误判断布局方向，返回值与实际渲染严重偏离。

- **缺乏尺寸约束机制：**  
  侧边栏宽度依赖高度（`available_height // 3`），在窄而高的终端中过度挤压主区域，影响可用性。

---

## 3. 优化措施

### 3.1 布局结构调整

| 断点类型 | 布局结构 | 说明 |
|--------|---------|------|
| **小屏** | `header → main → input → status` | 保持现状，隐藏侧边栏与 LangGraph 覆盖层 |
| **中等** | `header → (main + sidebar) → input → status` | 使用 `Layout("content").split_row(...)` 创建左右分区，**保留输入栏** |
|          |                                                | 若需底部工具区，应在 `main` 内部使用 `split_column` 实现，避免替换 `input` 区域 |
| **大屏及以上** | `sidebar \| main \| langgraph`（三列） | 显式挂载 `langgraph` 区域，其可见性由配置控制 |

> ✅ **关键改进：**
> - 所有断点均保证 `LayoutRegion.INPUT` 存在；
> - 移除未使用的 `info` 区域；
> - 大屏布局中 `langgraph` 占据右侧固定列，支持动态显隐。

---

### 3.2 断点与尺寸触发策略

调整 `resize_layout` 的触发逻辑如下：

```python
if size_changed:
    current_breakpoint = determine_breakpoint(new_width, new_height)
    if current_breakpoint != self._last_breakpoint:
        rebuild_full_layout()  # 断点变更 → 强制重建
    else:
        width_delta = abs(new_width - self._last_width)
        height_delta = abs(new_height - self._last_height)
        if width_delta >= 6 or height_delta >= 3:
            _adjust_region_sizes_gradual()  # 微调尺寸
```

- **新增节流机制：**
  - 默认启用 30ms 防抖（throttle），防止高频 resize 导致性能下降；
  - 可通过 `LayoutConfig.resize_throttle_ms` 自定义。

---

### 3.3 LangGraph 区域策略

- **统一挂载机制：**  
  在 `_create_full_layout` 中始终创建 `langgraph` 区域节点，无论当前是否可见。

- **显隐控制方式：**  
  - 当 `RegionConfig(langgraph).visible == False` 时，向该区域填充一个空 `Panel("", ...)` 占位；
  - 恢复显示时无需重建整个布局树，只需替换内容。

- **运行时 API 支持：**
  ```python
  layout_manager.set_region_visible("LANGGRAPH", True)
  layout_manager.trigger_rerender()
  ```

> ✅ 优势：避免因显隐切换引发布局抖动或状态丢失。

---

### 3.4 尺寸计算重构

#### 方向感知设计
- 在布局创建时记录每个子区域的父级方向：
  - 方案一：扩展 `RegionConfig` 添加 `direction: Literal["row", "column"]`
  - 方案二：在 `LayoutManager` 内维护 `region_id → direction` 映射表

#### `_calculate_optimal_sizes` 改进
- 侧边栏/`langgraph` 宽度基于终端总宽度比例计算：
  ```python
  sidebar_width = clamp(int(total_width * 0.22), min_w=20, max_w=40)
  ```
- 主区域宽度 = 总宽 - 左右栏占用；高度 = 总高 - header/status 固定高度

#### `get_region_size` 修正
- 根据父节点方向决定返回维度：
  ```python
  if parent_is_row:
      return (calculated_width, full_height)
  elif parent_is_column:
      return (full_width, calculated_height)
  ```
- 回退机制：若未设置 `Layout.size`，则按比例估算并结合最小/最大限制。

---

### 3.5 配置与可定制性

在 `LayoutConfig` 中新增以下可配置项：

| 配置项 | 类型 | 描述 |
|-------|------|------|
| `resize_threshold: Tuple[int, int]` | `(width, height)` 变化阈值，用于渐进调整 |
| `resize_throttle_ms: int` | resize 事件节流时间，默认 30ms |
| `sidebar_width_range: Tuple[int, int]` | 侧边栏最小/最大宽度（字符数） |
| `langgraph_width_range: Tuple[int, int]` | LangGraph 区域宽度范围 |
| `visibility_by_breakpoint: Dict[str, List[RegionName]]` | 按断点定义各区域显隐规则 |

> 📚 **文档同步：**
> 更新 `docs/user-guide/tui/input-guide.md` 并添加完整配置示例，说明如何自定义布局行为。

---

### 3.6 测试与验证

#### 单元测试
- ✅ 断言 `_create_layout_structure(breakpoint)` 在四个断点下：
  - 必需区域（`INPUT`, `MAIN`, `STATUS`）始终存在；
  - `LANGGRAPH` 节点存在，即使不可见；
- ✅ 验证 `_calculate_optimal_sizes()` 输出满足：
  - 宽度在 `[min, max]` 范围内；
  - 随终端尺寸增大单调非减；
  - 各区域之和不超过总空间。

#### 集成测试
- 使用 `test_layout_optimization.py` 模拟终端 resize 流程：
  - 从 `80x24 → 100x30 → 120x40`，校验断点切换及时性；
  - 触发多次 `set_region_visible("LANGGRAPH")`，验证内容恢复正确；
- 新增回归测试用例，防止未来修改导致区域消失或状态丢失。

#### 手动验证
- 运行 `LayoutTester.test_responsive_layouts()`，采集以下尺寸截图：
  - `80×24`（小屏）
  - `100×30`（中等）
  - `120×40`（大屏）
  - `140×50`（超大）
  - `160×60`（极限宽高比）
- 检查项目：
  - 输入栏是否始终可见；
  - 各区域无重叠或溢出；
  - `langgraph` 显示/隐藏切换流畅。

---

### 3.7 风险控制与回退

- **影响范围评估：**
  - 主要改动集中于 `src/presentation/tui/layout.py` 中的 `LayoutManager`；
  - 需重点审查与 `RenderController` 和 `SubviewController` 的区域命名一致性。

- **安全措施：**
  - 提交前备份原始 `layout.py` 文件【已备份为layout.py.bak】；
  - 提供一键回滚脚本，在生产环境异常时快速恢复旧版布局；
  - 建议先在内部测试终端部署 A/B 对比版本，监控以下指标：
    - 重绘频率（FPS）
    - CPU 占用率
    - 用户操作延迟（如输入响应时间）

---

## 4. 预期收益

| 收益维度 | 具体体现 |
|--------|----------|
| **用户体验提升** | 输入栏在所有尺寸下可用，消除阻塞性缺陷 |
| **响应式稳定性增强** | 断点切换更及时，布局过渡自然 |
| **功能完整性保障** | `langgraph` 区域与配置一致，支持可视化拓展 |
| **开发调试效率提高** | 尺寸计算可信，便于自动化测试与问题定位 |
| **可维护性与扩展性** | 配置驱动 + 测试覆盖，为新增区域（如 debug panel）打下基础 |

---

> **下一步建议：**
> 1. 拆分此方案为多个 PR（如：布局结构 → 触发策略 → 尺寸计算）；
> 2. 编写迁移指南，指导用户升级后可能需要调整的配置项；
> 3. 在 CI 中加入多尺寸终端模拟测试流程。
