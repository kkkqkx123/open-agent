## 详细的实现计划

基于完善的插件化架构设计，我现在创建一个详细的实现计划，包括所有需要创建的文件和实现步骤。

### 实现文件清单

#### 1. 插件系统核心文件
- [`src/infrastructure/graph/plugins/__init__.py`](src/infrastructure/graph/plugins/__init__.py) - 插件模块初始化
- [`src/infrastructure/graph/plugins/interfaces.py`](src/infrastructure/graph/plugins/interfaces.py) - 插件接口定义
- [`src/infrastructure/graph/plugins/registry.py`](src/infrastructure/graph/plugins/registry.py) - 插件注册表
- [`src/infrastructure/graph/plugins/manager.py`](src/infrastructure/graph/plugins/manager.py) - 插件管理器

#### 2. 内置插件实现
- [`src/infrastructure/graph/plugins/builtin/__init__.py`](src/infrastructure/graph/plugins/builtin/__init__.py) - 内置插件模块
- [`src/infrastructure/graph/plugins/builtin/start/__init__.py`](src/infrastructure/graph/plugins/builtin/start/__init__.py) - START插件模块
- [`src/infrastructure/graph/plugins/builtin/start/context_summary.py`](src/infrastructure/graph/plugins/builtin/start/context_summary.py) - 上下文摘要插件
- [`src/infrastructure/graph/plugins/builtin/start/environment_check.py`](src/infrastructure/graph/plugins/builtin/start/environment_check.py) - 环境检查插件
- [`src/infrastructure/graph/plugins/builtin/start/metadata_collector.py`](src/infrastructure/graph/plugins/builtin/start/metadata_collector.py) - 元数据收集插件

- [`src/infrastructure/graph/plugins/builtin/end/__init__.py`](src/infrastructure/graph/plugins/builtin/end/__init__.py) - END插件模块
- [`src/infrastructure/graph/plugins/builtin/end/result_summary.py`](src/infrastructure/graph/plugins/builtin/end/result_summary.py) - 结果汇总插件
- [`src/infrastructure/graph/plugins/builtin/end/execution_stats.py`](src/infrastructure/graph/plugins/builtin/end/execution_stats.py) - 执行统计插件
- [`src/infrastructure/graph/plugins/builtin/end/file_tracker.py`](src/infrastructure/graph/plugins/builtin/end/file_tracker.py) - 文件追踪插件
- [`src/infrastructure/graph/plugins/builtin/end/cleanup_manager.py`](src/infrastructure/graph/plugins/builtin/end/cleanup_manager.py) - 清理管理插件

#### 3. 节点实现
- [`src/infrastructure/graph/nodes/start_node.py`](src/infrastructure/graph/nodes/start_node.py) - START节点
- [`src/infrastructure/graph/nodes/end_node.py`](src/infrastructure/graph/nodes/end_node.py) - END节点

#### 4. 配置文件
- [`configs/plugins/start_end_plugins.yaml`](configs/plugins/start_end_plugins.yaml) - 插件配置文件
- [`configs/nodes/start.yaml`](configs/nodes/start.yaml) - START节点配置
- [`configs/nodes/end.yaml`](configs/nodes/end.yaml) - END节点配置
- 更新 [`configs/nodes/_group.yaml`](configs/nodes/_group.yaml) - 添加默认配置

#### 5. 更新现有文件
- 更新 [`src/infrastructure/graph/nodes/__init__.py`](src/infrastructure/graph/nodes/__init__.py) - 导出新节点
- 更新 [`src/infrastructure/graph/__init__.py`](src/infrastructure/graph/__init__.py) - 导出插件系统

### 实现步骤

#### 阶段1: 插件系统核心架构
1. **创建插件接口定义** - 定义所有插件必须实现的接口
2. **实现插件注册表** - 管理插件的注册和获取
3. **实现插件管理器** - 负责插件的加载、配置和执行

#### 阶段2: 内置插件实现
1. **START插件实现** - 实现上下文摘要、环境检查、元数据收集
2. **END插件实现** - 实现结果汇总、执行统计、文件追踪、清理管理
3. **插件测试** - 确保每个插件正常工作

#### 阶段3: 节点实现
1. **START节点实现** - 集成插件管理器，实现插件化执行
2. **END节点实现** - 集成插件管理器，实现插件化执行
3. **节点注册** - 将节点注册到系统

#### 阶段4: 配置系统集成
1. **创建插件配置文件** - 定义插件配置结构
2. **创建节点配置文件** - 定义节点配置
3. **更新配置组** - 添加默认配置

#### 阶段5: 集成和测试
1. **更新模块导入** - 确保所有新模块可正确导入
2. **集成测试** - 测试完整的start/end节点功能
3. **文档更新** - 更新相关文档

### 配置文件示例

#### 插件配置文件 (`configs/plugins/start_end_plugins.yaml`)
```yaml
# START/END节点插件配置
metadata:
  name: "start_end_plugins"
  version: "1.0.0"
  description: "START和END节点的插件配置"

# START节点插件配置
start_plugins:
  builtin:
    - name: "context_summary"
      enabled: true
      priority: 10
      config:
        include_file_structure: true
        include_recent_changes: true
        include_git_status: true
        max_summary_length: 1000
    
    - name: "environment_check"
      enabled: true
      priority: 20
      config:
        check_dependencies: true
        check_resources: true
        check_permissions: true
        fail_on_error: false
    
    - name: "metadata_collector"
      enabled: true
      priority: 30
      config:
        collect_system_info: true
        collect_project_info: true
        collect_user_info: false

  external: []

# END节点插件配置
end_plugins:
  builtin:
    - name: "result_summary"
      enabled: true
      priority: 10
      config:
        include_tool_results: true
        include_error_analysis: true
        include_recommendations: true
        output_format: "markdown"
    
    - name: "execution_stats"
      enabled: true
      priority: 20
      config:
        track_execution_time: true
        track_resource_usage: true
        track_node_performance: true
        generate_report: true
    
    - name: "file_tracker"
      enabled: true
      priority: 30
      config:
        track_created_files: true
        track_modified_files: true
        track_deleted_files: true
        include_file_hashes: false
        generate_diff_report: true
    
    - name: "cleanup_manager"
      enabled: true
      priority: 40
      config:
        cleanup_temp_files: true
        cleanup_cache: false
        cleanup_logs: false
        retain_patterns: ["*.log", "*.report"]

  external: []

# 插件执行配置
execution:
  parallel_execution: false
  max_parallel_plugins: 3
  error_handling:
    continue_on_error: true
    log_errors: true
    fail_on_critical_error: false
  timeout:
    default_timeout: 30
    per_plugin_timeout: 60
```

#### START节点配置 (`configs/nodes/start.yaml`)
```yaml
# START节点配置
inherits_from: "_group.yaml#start_node"

# 节点特定配置
plugin_config_path: "${PLUGIN_CONFIG_PATH:configs/plugins/start_end_plugins.yaml}"

# 执行配置
next_node: null  # 由工作流配置决定
error_next_node: "error_handler"

# 上下文元数据
context_metadata:
  environment: "${ENVIRONMENT:development}"
  debug_mode: "${DEBUG_MODE:false}"
```

#### END节点配置 (`configs/nodes/end.yaml`)
```yaml
# END节点配置
inherits_from: "_group.yaml#end_node"

# 节点特定配置
plugin_config_path: "${PLUGIN_CONFIG_PATH:configs/plugins/start_end_plugins.yaml}"

# 执行配置
error_next_node: "error_handler"

# 输出配置
output_directory: "${OUTPUT_DIR:./output}"
generate_reports: true
```

### 使用示例

#### 工作流配置中使用START/END节点
```yaml
# 工作流配置示例
workflow_name: "enhanced_workflow"
description: "使用插件化START/END节点的工作流"

nodes:
  start_node:
    function: "start_node"
    config:
      plugin_config_path: "configs/plugins/start_end_plugins.yaml"
      context_metadata:
        project_type: "web_development"
        debug_mode: true
  
  analysis_node:
    function: "analysis_node"
    config:
      llm_client: "openai-gpt4"
  
  end_node:
    function: "end_node"
    config:
      plugin_config_path: "configs/plugins/start_end_plugins.yaml"
      output_directory: "./workflow_output"
      generate_reports: true

edges:
  - from: "start_node"
    to: "analysis_node"
    type: "simple"
  
  - from: "analysis_node"
    to: "end_node"
    type: "simple"

entry_point: "start_node"
```

### 扩展插件示例

#### 自定义插件实现
```python
# plugins/custom/project_analyzer.py
from src.infrastructure.graph.plugins.interfaces import IStartPlugin, PluginMetadata, PluginType

class CustomProjectAnalyzer(IStartPlugin):
    """自定义项目分析插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom_project_analyzer",
            version="1.0.0",
            description="自定义项目分析器",
            author="custom",
            plugin_type=PluginType.START
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self.analysis_depth = config.get('analysis_depth', 'standard')
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        # 执行自定义分析逻辑
        analysis_result = self._analyze_project()
        state['custom_analysis'] = analysis_result
        return state
    
    def cleanup(self) -> bool:
        return True
    
    def _analyze_project(self) -> Dict[str, Any]:
        # 实现项目分析逻辑
        return {
            "complexity": "medium",
            "technologies": ["python", "yaml"],
            "recommendations": ["添加测试", "优化配置"]
        }
```

#### 在配置中使用自定义插件
```yaml
# configs/plugins/start_end_plugins.yaml
start_plugins:
  external:
    - name: "custom_project_analyzer"
      enabled: true
      priority: 15
      module: "plugins.custom.project_analyzer"
      class: "CustomProjectAnalyzer"
      config:
        analysis_depth: "deep"
        include_metrics: true
```