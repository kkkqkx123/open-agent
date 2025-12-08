"""
基础转换器

提供所有转换器的通用基础实现。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union, TYPE_CHECKING
from datetime import datetime

from src.services.logger.injection import get_logger
from .interfaces import IConverter
from src.interfaces.llm.converters import IConversionContext

if TYPE_CHECKING:
    from .conversion_context import ConversionContext
else:
    # 在运行时使用IConversionContext作为实际类型
    ConversionContext = IConversionContext


class ConversionError(Exception):
    """转换错误"""
    pass


class ValidationError(ConversionError):
    """验证错误"""
    pass


class BaseConverter(IConverter, ABC):
    """基础转换器
    
    提供所有转换器的通用基础实现，使用模板方法模式。
    """
    
    def __init__(self, name: str):
        """初始化基础转换器
        
        Args:
            name: 转换器名称
        """
        self.name = name
        self.logger = get_logger(__name__)
        self._stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "total_time": 0.0
        }
    
    def convert(self, source: Any, context: IConversionContext) -> Any:
        """执行转换
        
        使用模板方法模式定义转换流程。
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Returns:
            Any: 转换结果
            
        Raises:
            ConversionError: 转换失败
        """
        start_time = datetime.now()
        
        try:
            # 更新统计信息
            self._stats["total_conversions"] += 1
            
            # 添加调试信息
            context.add_debug_info("converter_name", self.name)
            context.add_debug_info("source_type", type(source).__name__)
            
            # 执行转换流程
            self.validate_input(source, context)
            self.prepare_context(context)
            result = self.do_convert(source, context)
            result = self.post_process(result, context)
            
            # 更新成功统计
            self._stats["successful_conversions"] += 1
            
            return result
            
        except Exception as e:
            # 更新失败统计
            self._stats["failed_conversions"] += 1
            
            # 处理错误
            self.handle_error(e, context)
            raise
            
        finally:
            # 更新时间统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self._stats["total_time"] += duration
            
            # 标记上下文完成
            context.mark_completed()
    
    @abstractmethod
    def do_convert(self, source: Any, context: IConversionContext) -> Any:
        """执行具体的转换逻辑
        
        子类必须实现此方法来定义具体的转换逻辑。
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Returns:
            Any: 转换结果
        """
        pass
    
    def can_convert(self, source_type: type, target_type: type) -> bool:
        """检查是否可以转换指定类型
        
        默认实现检查类型是否在支持的类型列表中。
        
        Args:
            source_type: 源类型
            target_type: 目标类型
            
        Returns:
            bool: 是否可以转换
        """
        supported_conversions = self.get_supported_conversions()
        return (source_type, target_type) in supported_conversions
    
    def get_supported_conversions(self) -> List[tuple[type, type]]:
        """获取支持的转换类型列表
        
        子类可以重写此方法来定义支持的转换类型。
        
        Returns:
            List[tuple[type, type]]: 支持的转换类型列表
        """
        return []
    
    def validate_input(self, source: Any, context: IConversionContext) -> None:
        """验证输入数据
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Raises:
            ValidationError: 验证失败
        """
        if source is None:
            raise ValidationError("输入数据不能为空")
        
        # 检查是否支持该类型转换
        source_type = type(source)
        target_type = self.get_target_type(context)
        
        if target_type and not self.can_convert(source_type, target_type):
            raise ValidationError(f"不支持的转换类型: {source_type} -> {target_type}")
    
    def prepare_context(self, context: IConversionContext) -> None:
        """准备转换上下文
        
        子类可以重写此方法来添加特定的上下文准备逻辑。
        
        Args:
            context: 转换上下文
        """
        # 添加转换器信息到上下文
        context.set_metadata("converter_name", self.name)
        context.set_metadata("converter_version", self.get_version())
    
    def post_process(self, result: Any, context: IConversionContext) -> Any:
        """后处理转换结果
        
        子类可以重写此方法来添加特定的后处理逻辑。
        
        Args:
            result: 转换结果
            context: 转换上下文
            
        Returns:
            Any: 后处理后的结果
        """
        # 添加结果信息到上下文
        context.set_metadata("result_type", type(result).__name__)
        
        return result
    
    def handle_error(self, error: Exception, context: IConversionContext) -> None:
        """处理转换错误
        
        Args:
            error: 错误对象
            context: 转换上下文
        """
        error_msg = f"转换失败: {error}"
        context.add_error(error_msg)
        
        if isinstance(error, ConversionError):
            self.logger.error(f"转换器 {self.name} 转换失败: {error}")
        else:
            self.logger.error(f"转换器 {self.name} 发生未预期错误: {error}")
    
    def get_target_type(self, context: IConversionContext) -> Optional[type]:
        """获取目标类型
        
        Args:
            context: 转换上下文
            
        Returns:
            Optional[type]: 目标类型
        """
        target_format = context.get_parameter("target_format")
        if target_format:
            return self.get_type_from_format(target_format)
        return None
    
    def get_type_from_format(self, format_name: str) -> Optional[type]:
        """根据格式名称获取类型
        
        子类可以重写此方法来定义格式到类型的映射。
        
        Args:
            format_name: 格式名称
            
        Returns:
            Optional[type]: 对应的类型
        """
        return None
    
    def get_version(self) -> str:
        """获取转换器版本
        
        Returns:
            str: 版本号
        """
        return "1.0.0"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取转换器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        
        # 计算平均时间
        if stats["successful_conversions"] > 0:
            stats["average_time"] = stats["total_time"] / stats["successful_conversions"]
        else:
            stats["average_time"] = 0.0
        
        # 计算成功率
        if stats["total_conversions"] > 0:
            stats["success_rate"] = stats["successful_conversions"] / stats["total_conversions"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "total_time": 0.0
        }
    
    def create_child_context(self, source: Any, parent_context: IConversionContext, 
                           conversion_type: str, **kwargs: Any) -> IConversionContext:
        """创建子转换上下文
        
        Args:
            source: 源数据
            parent_context: 父上下文
            conversion_type: 转换类型
            **kwargs: 额外的上下文参数
            
        Returns:
            IConversionContext: 子上下文
        """
        child_context = parent_context.create_child_context(
            conversion_type=conversion_type,
            source_format=type(source).__name__,
            **kwargs
        )
        
        return child_context
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 字符串表示
        """
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """详细字符串表示
        
        Returns:
            str: 详细字符串表示
        """
        stats = self.get_stats()
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"total_conversions={stats['total_conversions']}, "
                f"success_rate={stats['success_rate']:.2%})")


class CompositeConverter(BaseConverter):
    """复合转换器
    
    可以组合多个转换器来实现复杂的转换逻辑。
    """
    
    def __init__(self, name: str, converters: List[BaseConverter]):
        """初始化复合转换器
        
        Args:
            name: 转换器名称
            converters: 子转换器列表
        """
        super().__init__(name)
        self.converters = converters
    
    def do_convert(self, source: Any, context: IConversionContext) -> Any:
        """执行复合转换
        
        按顺序执行所有子转换器。
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Returns:
            Any: 转换结果
        """
        result = source
        
        for i, converter in enumerate(self.converters):
            # 创建子上下文
            child_context = self.create_child_context(
                result, context, f"step_{i+1}"
            )
            
            # 执行转换
            result = converter.convert(result, child_context)
            
            # 合并上下文
            context.merge_context(child_context)
        
        return result
    
    def get_supported_conversions(self) -> List[tuple[type, type]]:
        """获取支持的转换类型列表
        
        Returns:
            List[tuple[type, type]]: 支持的转换类型列表
        """
        # 合并所有子转换器的支持类型
        supported = []
        for converter in self.converters:
            supported.extend(converter.get_supported_conversions())
        return supported
    
    def add_converter(self, converter: BaseConverter) -> None:
        """添加子转换器
        
        Args:
            converter: 子转换器
        """
        self.converters.append(converter)
    
    def remove_converter(self, converter: BaseConverter) -> bool:
        """移除子转换器
        
        Args:
            converter: 子转换器
            
        Returns:
            bool: 是否成功移除
        """
        if converter in self.converters:
            self.converters.remove(converter)
            return True
        return False