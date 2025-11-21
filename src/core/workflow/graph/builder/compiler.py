"""图编译器

负责图的编译和检查点管理。
"""

from typing import Any, Dict, Optional
import logging

from src.core.workflow.config.config import GraphConfig

logger = logging.getLogger(__name__)


class GraphCompiler:
    """图编译器
    
    负责图的编译和检查点管理。
    """
    
    def __init__(self):
        """初始化图编译器"""
        self._checkpointer_cache: Dict[str, Any] = {}
    
    def compile(self, builder: Any, config: GraphConfig) -> Any:
        """编译图
        
        Args:
            builder: LangGraph构建器
            config: 图配置
            
        Returns:
            编译后的图
        """
        # 获取检查点
        checkpointer = self._get_checkpointer(config)
        
        # 编译图
        if checkpointer:
            compiled_graph = builder.compile(checkpointer=checkpointer)
        else:
            compiled_graph = builder.compile()
        
        return compiled_graph
    
    def _get_checkpointer(self, config: GraphConfig) -> Optional[Any]:
        """获取检查点
        
        Args:
            config: 图配置
            
        Returns:
            Optional[Any]: 检查点实例
        """
        if not config.checkpointer:
            return None
        
        if config.checkpointer in self._checkpointer_cache:
            return self._checkpointer_cache[config.checkpointer]
        
        checkpointer: Any = None
        if config.checkpointer == "memory":
            from langgraph.checkpoint.memory import InMemorySaver
            checkpointer = InMemorySaver()
        elif config.checkpointer.startswith("sqlite:"):
            # sqlite:/path/to/db.sqlite
            from langgraph.checkpoint.sqlite import SqliteSaver
            db_path = config.checkpointer[7:]  # 移除 "sqlite:" 前缀
            checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")
        
        if checkpointer:
            self._checkpointer_cache[config.checkpointer] = checkpointer
        
        return checkpointer