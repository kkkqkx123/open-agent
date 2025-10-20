
# 节点自动发现配置示例

## 配置结构说明

本文件展示如何在全局配置中添加节点自动发现相关配置项。

## 完整配置示例

```yaml
# configs/global.yaml
# 全局配置

log_level: "ERROR"
log_outputs:
  - type: "console"
    level: "INFO"
    format: "text"
  - type: "file"
    level: "DEBUG"
    format: "json"
    path: "logs/agent.log"
    rotation: "daily"
    max_size: "10MB"

secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
  - "\\w+@\\w+\\.\\w+"
  - "1\\d{10}"

env: "development"
debug: true

# 热重载配置
hot_reload: true
watch_interval: 5  # 5秒

# 节点自动发现配置
node_discovery:
  enabled: false  # 是否启用自动发现机制
  scan_internal: true  # 是否扫描内部节点目录
  scan_external: true  # 是否扫描外部插件
  entry_point_name: "modular_agent.nodes"
  internal_nodes_path: "src/workflow.nodes"
  exclude_patterns:
    - "*_test.py"
    - "*_mock.py"
  - "*.pyc"
  retry_attempts: 3  # 重试次数
  timeout: 30  # 扫描超时时间（秒）
  cache_discovered_nodes: true  # 是否缓存已发现的节点
  cache_ttl: 3600  # 缓存过期时间（秒）
  external_plugins: []  # 外部插件包列表
  security:
    enable_sandbox: true  # 是否启用沙箱环境
  allowed_packages:
    - "modular_agent.*"
  scan_on_startup: true  # 是否在启动时扫描
  enable_hot_reload: false  # 是否启用热重载
  hot_reload_delay: 2  # 热重载延迟（秒）
  validation:
    enable_type_check: true
    enable_schema_validation: true
  fallback_to_manual: true  # 自动发现失败时是否回退到手动注册
```

## 配置项说明

### 核心配置
- **enabled**: 控制是否启用自动发现机制，默认关闭
- **scan_internal**: 是否扫描内部节点目录
- **scan_external**: 是否扫描外部插件

### 使用示例

1. **开发环境配置**：
```yaml
node_discovery:
  enabled: true
  scan_internal: true
  scan_external: false  # 开发环境通常不需要外部插件

2. **生产环境配置**：
```yaml
node_discovery:
  enabled: false  # 生产环境建议关闭以提升性能

3. **插件化架构配置**：
```yaml
node_discovery:
  enabled: true
  scan_internal: true
  scan_external: true
```

## 配置验证规则

```python
# 配置验证逻辑
def validate_node_discovery_config(config: Dict[str, Any]) -> List[str]:
    """验证节点发现配置的有效性"""
    errors = []
    
    if config.get("enabled", False):
        # 验证扫描路径存在
        if not os.path.exists(config.get("internal_nodes_path", "src/workflow.nodes")):
        errors.append("内部节点路径不存在")
    
    # 验证超时时间
    if config.get("timeout", 30) <= 0:
        errors.append("超时时间必须大于0")
    
    return errors
```

## 启用自动发现的场景

### 适用场景
- 多团队协作开发
- 第三方插件集成
- 大型项目模块化

## 性能优化建议

1. **开发环境**：可以启用自动发现
2. **生产环境**：建议禁用自动发现
3. **测试环境**：根据需要启用

### 推荐配置

**默认配置（推荐）**：
```yaml
node_discovery:
  enabled: false  # 保持手动注册的清晰性

## 总结

节点自动发现机制作为可选功能，通过配置控制启用，适用于特定的扩展场景。
```

<line_count>75</line_count>
</write_to_file>