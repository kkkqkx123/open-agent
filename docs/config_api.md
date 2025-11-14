# 配置系统API文档

## 概述
配置系统提供统一的配置管理功能，支持配置文件加载、验证、继承、合并等。

## 核心接口

### IConfigSystem
配置系统主接口

```python
class IConfigSystem:
    def load_global_config(self) -> GlobalConfig:
        """加载全局配置"""
    
    def load_llm_config(self, name: str) -> LLMConfig:
        """加载LLM配置"""
    
    def load_tool_config(self, name: str) -> ToolConfig:
        """加载工具配置"""
    
    def load_token_counter_config(self, name: str) -> TokenCounterConfig:
        """加载Token计数器配置"""
    
    def load_task_groups_config(self) -> TaskGroupsConfig:
        """加载任务组配置"""
    
    def reload_configs(self) -> None:
        """重新加载所有配置"""
    
    def get_config_path(self, config_type: str, name: str) -> str:
        """获取配置路径"""
    
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听配置变化"""
    
    def stop_watching(self) -> None:
        """停止监听配置变化"""
    
    def list_configs(self, config_type: str) -> List[str]:
        """列出指定类型的所有配置"""
    
    def config_exists(self, config_type: str, name: str) -> bool:
        """检查配置是否存在"""
```

### IConfigLoader
配置加载器接口

```python
class IConfigLoader:
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
    
    def reload(self) -> None:
        """重新加载所有配置"""
    
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听配置变化"""
    
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""
    
    def stop_watching(self) -> None:
        """停止监听配置变化"""
    
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置，如果不存在则返回None"""
```

## 使用示例

### 基本使用
```python
from src.infrastructure.config import ConfigFactory

# 创建配置系统
config_system = ConfigFactory.create_config_system()

# 加载全局配置
global_config = config_system.load_global_config()
print(f"日志级别: {global_config.log_level}")
print(f"运行环境: {global_config.env}")

# 加载LLM配置
llm_config = config_system.load_llm_config("gpt-4")
print(f"模型名称: {llm_config.model_name}")
print(f"提供商: {llm_config.provider}")
```

### 创建最小配置系统
```python
# 创建仅包含核心功能的配置系统
config_system = ConfigFactory.create_minimal_config_system()
```

## 工厂方法

### ConfigFactory
提供创建配置系统实例的工厂方法：

- `create_config_system(base_path: str = "configs")` - 创建完整的配置系统
- `create_minimal_config_system(base_path: str = "configs")` - 创建最小配置系统