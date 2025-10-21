# TUI应用程序重构方案

## 当前问题分析

当前 `src/presentation/tui/app.py` 文件包含 1000+ 行代码，承担了过多职责：

1. **应用初始化** - 组件、配置、依赖注入初始化
2. **事件循环管理** - 键盘输入处理、线程管理
3. **UI渲染逻辑** - 主界面、子界面、对话框渲染
4. **状态管理** - 应用状态、会话状态、UI状态
5. **会话管理** - 创建、加载、保存会话
6. **消息处理** - 用户、助手、系统消息处理
7. **命令处理** - 各种命令的执行逻辑
8. **回调处理** - 各种回调函数的实现

## 重构目标

1. 将单一文件拆分为多个专注的模块
2. 保持目录结构深度不超过2级
3. 提高代码可维护性和可测试性
4. 保持app.py作为顶层协调器的角色

## 新的文件结构

```
src/presentation/tui/
├── app.py                    # 顶层协调器 (约200行)
├── event_engine.py           # 事件处理引擎
├── state_manager.py          # 状态管理器
├── render_controller.py      # 渲染控制器
├── command_processor.py      # 命令处理器
├── callback_manager.py       # 回调管理器
├── subview_controller.py     # 子界面控制器
└── session_handler.py        # 会话处理器
```

## 职责分离详细方案

### 1. EventEngine (事件处理引擎)

**文件**: `event_engine.py`
**职责**: 处理键盘输入、事件分发、线程管理
**提取的代码范围**: 行183-286 (事件循环), 行373-415 (键盘处理)

```python
class EventEngine:
    def __init__(self, terminal, config):
        self.terminal = terminal
        self.config = config
        self.running = False
        self.input_queue = queue.Queue()
        
    def start_event_loop(self):
        """启动事件循环"""
        # 提取原_run_event_loop逻辑
        
    def handle_key(self, key: str) -> bool:
        """处理键盘输入"""
        # 提取原handle_key逻辑
        
    def stop(self):
        """停止事件循环"""
```

### 2. StateManager (状态管理器)

**文件**: `state_manager.py`
**职责**: 管理应用状态、会话状态、UI状态
**提取的代码范围**: 行522-586 (状态更新), 行688-717 (会话管理)

```python
class StateManager:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.session_id = None
        self.current_state = None
        self.current_workflow = None
        self.message_history = []
        self.input_buffer = ""
        
    def create_session(self, workflow_config, agent_config=None):
        """创建新会话"""
        
    def load_session(self, session_id):
        """加载会话"""
        
    def save_session(self):
        """保存会话"""
        
    def update_component_states(self):
        """更新组件状态"""
```

### 3. RenderController (渲染控制器)

**文件**: `render_controller.py`
**职责**: 管理UI组件的渲染和更新
**提取的代码范围**: 行433-497 (UI渲染), 行609-636 (区域更新)

```python
class RenderController:
    def __init__(self, layout_manager, components, subviews):
        self.layout_manager = layout_manager
        self.components = components
        self.subviews = subviews
        
    def update_ui(self, current_subview=None, show_dialog=None):
        """更新UI显示"""
        
    def render_main_view(self):
        """渲染主界面"""
        
    def render_subview(self, subview_name):
        """渲染子界面"""
        
    def render_dialog(self, dialog_type):
        """渲染对话框"""
```

### 4. CommandProcessor (命令处理器)

**文件**: `command_processor.py`
**职责**: 解析和执行命令
**提取的代码范围**: 行788-843 (命令处理)

```python
class CommandProcessor:
    def __init__(self, app):
        self.app = app
        
    def process_command(self, command: str, args: List[str]):
        """处理命令"""
        
    def _handle_help(self):
        """处理help命令"""
        
    def _handle_clear(self):
        """处理clear命令"""
        
    # 其他命令处理方法...
```

### 5. CallbackManager (回调管理器)

**文件**: `callback_manager.py`
**职责**: 统一管理各种回调函数
**提取的代码范围**: 行969-1051 (回调处理)

```python
class CallbackManager:
    def __init__(self):
        self.callbacks = {}
        
    def register_callback(self, event_type, callback):
        """注册回调函数"""
        
    def trigger_callback(self, event_type, *args, **kwargs):
        """触发回调函数"""
        
    # 具体回调实现方法...
```

### 6. SubviewController (子界面控制器)

**文件**: `subview_controller.py`
**职责**: 管理子界面的切换和状态
**提取的代码范围**: 行417-431 (子界面获取), 行1052-1067 (子界面切换)

```python
class SubviewController:
    def __init__(self, subviews):
        self.subviews = subviews
        self.current_subview = None
        
    def switch_to_subview(self, subview_name):
        """切换到指定子界面"""
        
    def return_to_main_view(self):
        """返回主界面"""
        
    def get_current_subview(self):
        """获取当前子界面"""
```

### 7. SessionHandler (会话处理器)

**文件**: `session_handler.py`
**职责**: 专门处理会话相关操作
**提取的代码范围**: 行914-931 (会话加载), 行903-913 (会话保存)

```python
class SessionHandler:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        
    def load_session(self, session_id):
        """加载会话"""
        
    def save_session(self, session_id, workflow, state):
        """保存会话"""
        
    def delete_session(self, session_id):
        """删除会话"""
```

## 重构后的app.py结构

```python
class TUIApp:
    def __init__(self, config_path=None):
        # 初始化配置和基础组件
        self.config = get_tui_config(config_path)
        self.layout_manager = LayoutManager(self.config.layout)
        
        # 初始化各个管理器
        self.event_engine = EventEngine(self.terminal, self.config)
        self.state_manager = StateManager(self.session_manager)
        self.render_controller = RenderController(
            self.layout_manager, self.components, self.subviews
        )
        self.command_processor = CommandProcessor(self)
        self.callback_manager = CallbackManager()
        self.subview_controller = SubviewController(self.subviews)
        self.session_handler = SessionHandler(self.session_manager)
        
        # 设置回调
        self._setup_callbacks()
        
    def run(self):
        """运行应用程序"""
        self.event_engine.start_event_loop()
        
    def _setup_callbacks(self):
        """设置回调函数"""
        # 将回调注册到callback_manager
```

## 重构步骤

1. **第一阶段**: 创建新的模块文件并提取相关代码
   - 创建 `event_engine.py`, `state_manager.py`, `render_controller.py`
   - 提取事件处理、状态管理、渲染逻辑

2. **第二阶段**: 提取命令和回调处理
   - 创建 `command_processor.py`, `callback_manager.py`
   - 提取命令处理和回调逻辑

3. **第三阶段**: 提取子界面和会话处理
   - 创建 `subview_controller.py`, `session_handler.py`
   - 提取子界面和会话处理逻辑

4. **第四阶段**: 重构app.py为协调器
   - 移除提取的逻辑，只保留协调功能
   - 确保各模块正确协作

## 预期收益

1. **代码可维护性**: 每个模块职责单一，易于理解和修改
2. **可测试性**: 各模块可以独立测试
3. **扩展性**: 新增功能只需在相应模块中添加
4. **代码复用**: 模块可以在其他TUI应用中重用

## 风险与缓解

1. **重构风险**: 逐步提取，确保每一步都经过测试
2. **性能影响**: 模块化可能带来轻微性能开销，但可维护性收益更大
3. **接口稳定性**: 保持公共接口稳定，避免破坏现有功能