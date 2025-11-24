"""
工具注册表实现
"""

from typing import Dict, List, Optional
import logging

from src.interfaces.tool.base import ITool, IToolRegistry


logger = logging.getLogger(__name__)


class ToolRegistry(IToolRegistry):
    """工具注册表实现"""
    
    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, ITool] = {}
    
    def register_tool(self, tool: ITool) -> None:
        """注册工具
        
        Args:
            tool: 要注册的工具
        """
        self._tools[tool.name] = tool
        logger.info(f"工具已注册: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[ITool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    def unregister_tool(self, name: str) -> bool:
        """注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 注销是否成功
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"工具已注销: {name}")
            return True
        return False
    
    def get_all_tools(self) -> Dict[str, ITool]:
        """获取所有工具
        
        Returns:
            Dict[str, ITool]: 所有工具的字典
        """
        return self._tools.copy()
    
    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        logger.info("工具注册表已清空")