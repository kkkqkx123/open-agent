
## 节点自动发现与注册功能评估总结

### 当前实现状态
当前节点注册系统采用**手动注册机制**，通过 [`@node()`](src/workflow/registry.py:258) 装饰器进行节点注册，系统已实现：

- **4个核心节点类型**：分析节点、工具节点、LLM节点、条件节点
- **双重注册模式**：支持节点类注册和节点实例注册
- **全局注册表管理**：通过 [`get_global_registry()`](src/workflow/registry.py:215) 统一管理
- **装饰器简化**: `@node("node_type")` 语法已相当便利

### 适用场景分析
**✅ 适用场景：**
- 插件化架构（第三方扩展）
- 大型项目开发环境
- 动态节点加载场景

### 必要性评估结论
**当前阶段不建议立即实现自动发现功能**，原因：

1. **规模适中**：当前只有4个节点类型，手动注册足够高效
2. **清晰可控**：显式注册更易于理解和维护
- **性能考虑**：自动扫描可能增加启动时间

### 推荐策略
**渐进式实现方案：**
- 保持现有手动注册机制
- 预留自动发现接口
- 配置驱动控制是否启用

### 实施建议
如果未来需要实现，建议：
1. **可选功能**：通过配置控制是否启用自动发现
2. **分层扫描**：内部节点目录 + 外部插件入口点
- **错误处理机制**：确保自动发现失败不影响系统运行

**最终建议**：专注于完善现有节点功能，当项目扩展为多团队协作或需要支持第三方插件时再考虑实现自动发现功能。

---

# 节点自动发现与注册机制设计文档

## 概述

本文档详细描述节点自动发现与注册机制的设计方案，该机制作为可选功能，通过配置控制是否启用。

## 配置设计

### 全局配置（configs/global.yaml）

```yaml
# 节点自动发现配置
node_discovery:
  enabled: false  # 是否启用自动发现机制
  scan_internal: true  # 是否扫描内部节点目录
  scan_external: true  # 是否扫描外部插件
  entry_point_name: "modular_agent.nodes"
  internal_nodes_path: "src/workflow/nodes"
  external_plugins: []  # 外部插件包列表
  exclude_patterns:
    - "*_test.py"
    - "*_mock.py"
    - "*.pyc"
  retry_attempts: 3  # 重试次数
  timeout: 30  # 扫描超时时间（秒）
```

## 核心功能模块

### 1. 节点自动发现器（NodeDiscovery）

```python
class NodeDiscovery:
    """节点自动发现器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._scanners: List[NodeScanner]] = [
        InternalNodeScanner(),
        ExternalPluginScanner()
    ]
    
    def discover_nodes(self) -> None:
        """自动发现并注册节点"""
        node_registry = NodeRegistry()
        
        # 扫描内部节点目录
        if self.config.get("scan_internal", True):
            self._scan_internal_nodes(node_registry)
            
        # 扫描外部插件（可选）
        if self.config.get("scan_external", True):
            self._scan_external_plugins(node_registry)
```

### 2. 内部节点扫描器

```python
class InternalNodeScanner:
    """内部节点扫描器"""
    
    def scan(self, registry: NodeRegistry]) -> None:
        """扫描内部节点目录"""
        try:
            nodes_package = importlib.import_module(self.config["internal_nodes_path"])
            for name in dir(nodes_package):
                obj = getattr(nodes_package, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, BaseNode) and 
                    obj != BaseNode):
                    registry.register_node(obj.__name__.lower(), obj)
        except Exception as e:
            logger.warning(f"内部节点扫描失败: {e}")
```

### 3. 外部插件扫描器

```python
class ExternalPluginScanner:
    """外部插件扫描器"""
    
    def scan(self, registry: NodeRegistry]) -> None:
        """扫描外部插件"""
        try:
            for entry_point in pkg_resources.iter_entry_points(
            self.config["entry_point_name"])):
            node_class = entry_point.load()
            registry.register_node(entry_point.name, node_class)
        except Exception as e:
            logger.warning(f"外部插件扫描失败: {e}")
```

## 配置管理模块

### 节点发现配置（NodeDiscoveryConfig）

```python
@dataclass
class NodeDiscoveryConfig:
    """节点自动发现配置"""
    enabled: bool = False
    scan_internal: bool = True
  scan_external: bool = True
  entry_point_name: str = "modular_agent.nodes"
```

### 4. 配置验证

```python
def validate_node_discovery_config(config: Dict[str, Any]) -> List[str]:
    """验证节点发现配置"""
    errors = []
    
    if config.get("enabled", False):
        # 验证扫描路径
        if not os.path.exists(config.get("internal_nodes_path", "src/workflow/nodes")):
            errors.append("内部节点路径不存在")
            
        return errors
```

## 使用场景

### 启用自动发现

```yaml
# configs/global.yaml
node_discovery:
  enabled: true
  scan_internal: true
  scan_external: true
  entry_point_name: "modular_agent.nodes"
```

## 实施建议

1. **作为可选功能**：默认关闭，通过配置启用
2. **错误处理**：自动发现失败不影响系统运行
3. **性能优化**：缓存已发现节点，避免重复扫描
4. **开发环境优化**：在开发环境中可启用热重载
5. **生产环境**：建议禁用以减少启动时间

## 安全考虑

- 外部插件加载需要安全验证
- 限制可加载的包范围
- 提供白名单机制

## 测试策略

- 单元测试：测试单个扫描器功能
- 集成测试：测试与现有注册系统的集成
- 性能测试：确保自动发现不会显著影响启动性能
```

<line_count>85</line_count>
</write_to_file>