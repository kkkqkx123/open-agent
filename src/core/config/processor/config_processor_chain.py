"""配置处理器链实现

提供可组合的配置处理功能，支持继承、环境变量替换和引用解析。
"""

from typing import Dict, Any, List
import logging

from ....interfaces.config.interfaces import IConfigProcessor

logger = logging.getLogger(__name__)


class ConfigProcessorChain(IConfigProcessor):
    """配置处理器链
    
    按顺序执行多个配置处理器，支持配置的逐步处理。
    """
    
    def __init__(self):
        """初始化配置处理器链"""
        self.processors: List[IConfigProcessor] = []
        logger.debug("配置处理器链初始化完成")
    
    def add_processor(self, processor: IConfigProcessor) -> None:
        """添加处理器
        
        Args:
            processor: 配置处理器
        """
        self.processors.append(processor)
        logger.debug(f"已添加配置处理器: {processor.__class__.__name__}")
    
    def remove_processor(self, processor: IConfigProcessor) -> bool:
        """移除处理器
        
        Args:
            processor: 配置处理器
            
        Returns:
            是否成功移除
        """
        if processor in self.processors:
            self.processors.remove(processor)
            logger.debug(f"已移除配置处理器: {processor.__class__.__name__}")
            return True
        return False
    
    def clear_processors(self) -> None:
        """清除所有处理器"""
        self.processors.clear()
        logger.debug("已清除所有配置处理器")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """按顺序处理配置
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        result = config
        
        for i, processor in enumerate(self.processors):
            try:
                logger.debug(f"执行处理器 {i+1}/{len(self.processors)}: {processor.__class__.__name__}")
                result = processor.process(result, config_path)
            except Exception as e:
                logger.error(f"处理器 {processor.__class__.__name__} 执行失败: {e}")
                raise
        
        logger.debug(f"配置处理完成，共执行 {len(self.processors)} 个处理器")
        return result
    
    def get_processor_count(self) -> int:
        """获取处理器数量
        
        Returns:
            处理器数量
        """
        return len(self.processors)
    
    def get_processor_names(self) -> List[str]:
        """获取处理器名称列表
        
        Returns:
            处理器名称列表
        """
        return [processor.__class__.__name__ for processor in self.processors]