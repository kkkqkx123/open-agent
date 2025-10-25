"""Agent配置加载器"""

from typing import Dict, List
from .config import AgentConfig
from ...src.infrastructure.config_loader import IConfigLoader  # 使用现有的配置加载器接口


class AgentConfigLoader:
    """Agent配置加载器"""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self._agent_configs: Dict[str, AgentConfig] = {}
    
    def load_agent_config(self, config_name: str) -> AgentConfig:
        """加载指定名称的Agent配置"""
        if config_name in self._agent_configs:
            return self._agent_configs[config_name]
        
        # 从配置文件加载
        config_data = self.config_loader.load(f"agents/{config_name}.yaml")
        
        # 创建AgentConfig实例
        agent_config = AgentConfig(
            name=config_data.get("name", config_name),
            description=config_data.get("description", ""),
            agent_type=config_data.get("agent_type", ""),
            system_prompt=config_data.get("system_prompt", ""),
            decision_strategy=config_data.get("decision_strategy", ""),
            tools=config_data.get("tools", []),
            tool_sets=config_data.get("tool_sets", []),
            max_iterations=config_data.get("max_iterations", 10),
            timeout=config_data.get("timeout", 300),
            retry_count=config_data.get("retry_count", 3),
            llm=config_data.get("llm", ""),
            metadata=config_data.get("metadata", {})
        )
        
        # 处理记忆配置
        memory_config_data = config_data.get("memory_config", {})
        if memory_config_data:
            from .config import MemoryConfig
            agent_config.memory_config = MemoryConfig(
                enabled=memory_config_data.get("enabled", True),
                max_size=memory_config_data.get("max_size", 10),
                retention_time=memory_config_data.get("retention_time", 3600)
            )
        
        self._agent_configs[config_name] = agent_config
        return agent_config
    
    def load_agent_group_config(self, group_name: str) -> List[AgentConfig]:
        """加载Agent组配置"""
        # 从组配置文件加载
        group_config_data = self.config_loader.load(f"agents/{group_name}/_group.yaml")
        
        agent_configs = []
        for agent_name in group_config_data.get("agents", []):
            agent_config = self.load_agent_config(agent_name)
            agent_configs.append(agent_config)
        
        return agent_configs
    
    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """获取所有已加载的Agent配置"""
        return self._agent_configs.copy()