# 改进的Tool-Sets配置结构设计

## 1. 当前tool-sets配置问题分析

### 1.1 现有问题

1. **_group.yaml几乎为空**
   ```yaml
   # 工具集组配置
   ```
   没有提供任何有用的基础配置或模板

2. **配置结构不统一**
   - basic-tools.yaml结构简单
   - 缺少标准化的配置模板
   - 没有继承机制

3. **工具集管理困难**
   - 无法快速创建新工具集
   - 缺少工具集分类和标签
   - 没有依赖关系管理

### 1.2 需求分析

1. **标准化配置模板**
   - 提供基础配置结构
   - 支持配置继承
   - 统一字段定义

2. **工具集分类管理**
   - 按功能分类
   - 支持标签系统
   - 版本管理

3. **依赖关系管理**
   - 工具依赖检查
   - 自动依赖解析
   - 冲突检测

## 2. 改进的配置结构设计

### 2.1 基础配置模板 (_base.yaml)

```yaml
# configs/tool-sets/_base.yaml
# 工具集基础配置模板

# 元数据模板
metadata_template:
  version: "1.0.0"
  author: "ModularAgent Team"
  created_at: "2024-01-01"
  updated_at: "2024-01-01"
  tags: []
  category: "general"
  description: ""
  documentation_url: ""

# 默认配置
defaults:
  enabled: true
  auto_load: true
  priority: 100  # 优先级，数字越小优先级越高
  
# 工具集类型定义
tool_set_types:
  basic:
    description: "基础工具集，包含常用工具"
    recommended_tools:
      - calculator
      - weather
      - time_tool
    default_tags: ["basic", "common"]
    
  advanced:
    description: "高级工具集，包含复杂功能工具"
    recommended_tools:
      - fetch
      - database
      - sequentialthinking
      - hash_convert
    default_tags: ["advanced", "powerful"]
    
  development:
    description: "开发工具集，面向开发者"
    recommended_tools:
      - hash_convert
      - fetch
      - calculator
      - database
    default_tags: ["development", "developer"]
    
  analysis:
    description: "分析工具集，用于数据分析"
    recommended_tools:
      - fetch
      - sequentialthinking
      - database
    default_tags: ["analysis", "data"]
    
  external:
    description: "外部工具集，依赖外部API"
    recommended_tools:
      - weather
      - duckduckgo_search
      - fetch
    default_tags: ["external", "api"]

# 工具依赖关系
tool_dependencies:
  calculator: []
  weather: []
  time_tool: []
  fetch: []
  database: []
  sequentialthinking: []
  hash_convert: []
  duckduckgo_search: []

# 工具冲突关系
tool_conflicts:
  # 示例：某些工具可能存在冲突
  # tool_a: [tool_b, tool_c]

# 配置验证规则
validation_rules:
  required_fields:
    - name
    - description
    - tools
  optional_fields:
    - enabled
    - metadata
    - inherits_from
    - tool_groups
    - dependencies
    - conflicts
  field_types:
    name: "string"
    description: "string"
    tools: "array"
    enabled: "boolean"
    inherits_from: "string_or_array"
    tool_groups: "object"
    dependencies: "array"
    conflicts: "array"

# 工具组定义（用于批量管理）
tool_groups:
  math_tools:
    description: "数学相关工具"
    tools: [calculator]
    
  time_tools:
    description: "时间相关工具"
    tools: [time_tool]
    
  web_tools:
    description: "网络相关工具"
    tools: [fetch, duckduckgo_search]
    
  data_tools:
    description: "数据处理工具"
    tools: [database, hash_convert]
    
  thinking_tools:
    description: "思维工具"
    tools: [sequentialthinking]
    
  api_tools:
    description: "API调用工具"
    tools: [weather, fetch]

# 环境特定配置
environments:
  development:
    default_enabled: true
    tool_timeout: 60
    retry_count: 3
    
  production:
    default_enabled: false
    tool_timeout: 30
    retry_count: 2
    
  testing:
    default_enabled: true
    tool_timeout: 10
    retry_count: 1
```

### 2.2 具体工具集配置示例

#### 2.2.1 基础工具集 (basic.yaml)

```yaml
# configs/tool-sets/basic.yaml
# 基础工具集配置

# 继承基础配置
inherits_from: "_base"

# 工具集基本信息
name: "basic"
description: "基础工具集，包含日常使用的基本工具"
enabled: true
priority: 10  # 高优先级

# 元数据
metadata:
  version: "1.2.0"
  author: "ModularAgent Team"
  created_at: "2024-01-01"
  updated_at: "2024-01-15"
  tags: ["basic", "common", "starter"]
  category: "basic"
  documentation_url: "https://docs.example.com/tool-sets/basic"

# 包含的工具
tools:
  - calculator
  - weather
  - time_tool

# 工具组（从_base继承）
tool_groups:
  math_tools:
    enabled: true
  time_tools:
    enabled: true
  api_tools:
    enabled: true
    tools: [weather]  # 覆盖默认配置

# 依赖关系
dependencies: []

# 冲突检查
conflicts: []

# 环境特定配置
environment_config:
  development:
    tool_timeout: 30
  production:
    tool_timeout: 15
  testing:
    tool_timeout: 5

# 工具特定配置
tool_config_overrides:
  calculator:
    timeout: 10
    precision: 4
  weather:
    timeout: 20
    retry_count: 2
  time_tool:
    timeout: 5
```

#### 2.2.2 高级工具集 (advanced.yaml)

```yaml
# configs/tool-sets/advanced.yaml
# 高级工具集配置

# 继承基础配置
inherits_from: "_base"

# 工具集基本信息
name: "advanced"
description: "高级工具集，包含复杂功能和专业工具"
enabled: true
priority: 30

# 元数据
metadata:
  version: "2.1.0"
  author: "ModularAgent Team"
  created_at: "2024-01-01"
  updated_at: "2024-01-20"
  tags: ["advanced", "powerful", "professional"]
  category: "advanced"
  documentation_url: "https://docs.example.com/tool-sets/advanced"

# 包含的工具
tools:
  - fetch
  - database
  - sequentialthinking
  - hash_convert
  - duckduckgo_search

# 工具组
tool_groups:
  web_tools:
    enabled: true
    tools: [fetch, duckduckgo_search]
  data_tools:
    enabled: true
    tools: [database, hash_convert]
  thinking_tools:
    enabled: true
    tools: [sequentialthinking]

# 依赖关系
dependencies:
  - "basic"  # 依赖基础工具集

# 冲突检查
conflicts: []

# 环境特定配置
environment_config:
  development:
    tool_timeout: 60
    parallel_execution: true
  production:
    tool_timeout: 45
    parallel_execution: false
  testing:
    tool_timeout: 20
    parallel_execution: false

# 工具特定配置
tool_config_overrides:
  fetch:
    timeout: 30
    max_length: 10000
    user_agent: "ModularAgent/Advanced/1.0"
  database:
    timeout: 45
    connection_pool_size: 5
  sequentialthinking:
    timeout: 120
    max_thoughts: 10
  hash_convert:
    timeout: 10
    supported_algorithms: ["md5", "sha1", "sha256", "sha512"]
  duckduckgo_search:
    timeout: 25
    max_results: 10
```

#### 2.2.3 开发工具集 (development.yaml)

```yaml
# configs/tool-sets/development.yaml
# 开发工具集配置

# 继承基础配置
inherits_from: "_base"

# 工具集基本信息
name: "development"
description: "开发工具集，面向软件开发者"
enabled: true
priority: 20

# 元数据
metadata:
  version: "1.5.0"
  author: "ModularAgent Team"
  created_at: "2024-01-01"
  updated_at: "2024-01-18"
  tags: ["development", "developer", "coding"]
  category: "development"
  documentation_url: "https://docs.example.com/tool-sets/development"

# 包含的工具
tools:
  - hash_convert
  - fetch
  - calculator
  - database
  - sequentialthinking

# 工具组
tool_groups:
  math_tools:
    enabled: true
    tools: [calculator]
  web_tools:
    enabled: true
    tools: [fetch]
  data_tools:
    enabled: true
    tools: [database, hash_convert]
  thinking_tools:
    enabled: true
    tools: [sequentialthinking]

# 依赖关系
dependencies:
  - "basic"

# 冲突检查
conflicts: []

# 环境特定配置
environment_config:
  development:
    tool_timeout: 45
    debug_mode: true
  production:
    tool_timeout: 30
    debug_mode: false
  testing:
    tool_timeout: 15
    debug_mode: true

# 工具特定配置
tool_config_overrides:
  hash_convert:
    timeout: 15
    supported_algorithms: ["md5", "sha1", "sha256", "sha512", "base64"]
  fetch:
    timeout: 30
    follow_redirects: true
    max_redirects: 5
  calculator:
    timeout: 15
    precision: 8
    scientific_mode: true
  database:
    timeout: 30
    query_timeout: 25
  sequentialthinking:
    timeout: 90
    max_thoughts: 15
    debug_output: true
```

### 2.3 组合工具集示例

#### 2.3.1 全功能工具集 (full.yaml)

```yaml
# configs/tool-sets/full.yaml
# 全功能工具集配置

# 继承多个工具集
inherits_from:
  - "basic"
  - "advanced"
  - "development"

# 工具集基本信息
name: "full"
description: "全功能工具集，包含所有可用工具"
enabled: false  # 默认禁用，需要手动启用
priority: 100

# 元数据
metadata:
  version: "3.0.0"
  author: "ModularAgent Team"
  created_at: "2024-01-01"
  updated_at: "2024-01-25"
  tags: ["full", "complete", "all-tools"]
  category: "complete"
  documentation_url: "https://docs.example.com/tool-sets/full"

# 包含的工具（自动从继承的工具集中合并）
tools: []  # 空数组表示使用继承的所有工具

# 额外的工具组配置
tool_groups:
  all_tools:
    description: "所有可用工具"
    enabled: true
    tools: "*"  # 通配符表示所有工具

# 依赖关系
dependencies: []

# 冲突检查
conflicts: []

# 环境特定配置
environment_config:
  development:
    tool_timeout: 120
    parallel_execution: true
    max_concurrent_tools: 5
  production:
    tool_timeout: 60
    parallel_execution: true
    max_concurrent_tools: 3
  testing:
    tool_timeout: 30
    parallel_execution: false
    max_concurrent_tools: 1

# 全局工具配置覆盖
tool_config_overrides:
  "*":
    timeout: 60
    retry_count: 3
```

## 3. 配置加载和处理机制

### 3.1 配置继承处理

```python
class ToolSetConfigLoader:
    """工具集配置加载器"""
    
    def load_config(self, config_path: str) -> ToolSetConfig:
        """加载工具集配置，处理继承关系"""
        # 1. 加载基础配置
        base_config = self._load_base_config()
        
        # 2. 加载指定配置
        config = self._load_yaml_config(config_path)
        
        # 3. 处理继承关系
        if 'inherits_from' in config:
            config = self._process_inheritance(config, base_config)
        
        # 4. 验证配置
        self._validate_config(config)
        
        # 5. 返回配置对象
        return ToolSetConfig.from_dict(config)
    
    def _process_inheritance(self, config: dict, base_config: dict) -> dict:
        """处理配置继承"""
        inherits_from = config.get('inherits_from')
        
        if isinstance(inherits_from, str):
            # 单继承
            parent_config = self._load_parent_config(inherits_from)
            config = self._merge_configs(parent_config, config)
        elif isinstance(inherits_from, list):
            # 多继承
            for parent in inherits_from:
                parent_config = self._load_parent_config(parent)
                config = self._merge_configs(parent_config, config)
        
        return config
```

### 3.2 配置验证机制

```python
class ToolSetConfigValidator:
    """工具集配置验证器"""
    
    def validate(self, config: dict) -> ValidationResult:
        """验证工具集配置"""
        errors = []
        warnings = []
        
        # 1. 验证必需字段
        self._validate_required_fields(config, errors)
        
        # 2. 验证字段类型
        self._validate_field_types(config, errors)
        
        # 3. 验证工具存在性
        self._validate_tools_exist(config, errors, warnings)
        
        # 4. 验证依赖关系
        self._validate_dependencies(config, errors, warnings)
        
        # 5. 验证冲突关系
        self._validate_conflicts(config, errors, warnings)
        
        return ValidationResult(errors, warnings)
```

## 4. 配置使用示例

### 4.1 节点配置中的工具集引用

```yaml
# configs/nodes/agent_node.yaml
name: "agent_node"
type: "agent"
description: "智能代理节点"

# 工具集配置
tool_sets:
  - name: "basic"
    enabled: true
    config_overrides:
      calculator:
        precision: 6
  - name: "development"
    enabled: true
    config_overrides:
      fetch:
        timeout: 45

# 或者直接引用工具集组合
tool_set: "full"  # 使用全功能工具集
tool_set_config:
  environment: "production"
  global_timeout: 30
```

### 4.2 动态工具集创建

```python
# 运行时动态创建工具集
def create_custom_tool_set(
    name: str,
    tools: List[str],
    base_set: str = "basic"
) -> ToolSetConfig:
    """创建自定义工具集"""
    
    # 加载基础配置
    base_config = load_tool_set_config(base_set)
    
    # 创建自定义配置
    custom_config = {
        "name": name,
        "description": f"自定义工具集: {name}",
        "inherits_from": base_set,
        "tools": tools,
        "metadata": {
            "version": "1.0.0",
            "author": "Custom",
            "tags": ["custom"],
            "category": "custom"
        }
    }
    
    # 处理继承和验证
    config = process_inheritance(custom_config)
    validate_config(config)
    
    return ToolSetConfig.from_dict(config)
```

## 5. 优势总结

### 5.1 配置标准化

1. **统一模板**：所有工具集使用统一的基础模板
2. **字段规范**：明确的字段定义和类型要求
3. **验证机制**：自动验证配置正确性

### 5.2 管理便利性

1. **继承机制**：支持配置继承，减少重复
2. **分类管理**：按功能和用途分类管理
3. **版本控制**：支持配置版本管理

### 5.3 扩展性

1. **多继承**：支持从多个工具集继承
2. **动态创建**：支持运行时动态创建工具集
3. **配置覆盖**：支持细粒度的配置覆盖

### 5.4 可维护性

1. **结构清晰**：配置结构清晰易懂
2. **文档完善**：每个配置都有详细文档
3. **错误检查**：自动检查依赖和冲突

这种改进的配置结构大大提高了工具集管理的便利性和可维护性，同时保持了高度的灵活性和扩展性。