"""
转换管道

提供转换流程的管理和执行。
"""

from typing import Any, Dict, List, Optional, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from src.services.logger.injection import get_logger
from .base_converter import BaseConverter, ConversionError
from src.interfaces.llm.converters import IConversionContext

if TYPE_CHECKING:
    from .conversion_context import ConversionContext


class PipelineStage(Enum):
    """管道阶段"""
    
    PRE_VALIDATION = "pre_validation"
    PREPARATION = "preparation"
    CONVERSION = "conversion"
    POST_PROCESSING = "post_processing"
    POST_VALIDATION = "post_validation"


@dataclass
class PipelineStep:
    """管道步骤"""
    
    name: str
    stage: PipelineStage
    converter: BaseConverter
    condition: Optional[Callable[[ConversionContext], bool]] = None
    enabled: bool = True
    retry_count: int = 0
    max_retries: int = 3


class ConversionPipeline:
    """转换管道
    
    管理多个转换器的执行流程，支持条件执行、重试和错误处理。
    """
    
    def __init__(self, name: str):
        """初始化转换管道
        
        Args:
            name: 管道名称
        """
        self.name = name
        self.logger = get_logger(__name__)
        self.steps: List[PipelineStep] = []
        self.error_handlers: Dict[PipelineStage, List[Callable]] = {
            stage: [] for stage in PipelineStage
        }
        self.middleware: List[Callable] = []
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_time": 0.0
        }
    
    def add_step(self, step: PipelineStep) -> "ConversionPipeline":
        """添加管道步骤
        
        Args:
            step: 管道步骤
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        self.steps.append(step)
        self.logger.debug(f"添加管道步骤: {step.name} ({step.stage.value})")
        return self
    
    def add_converter(self, converter: BaseConverter, stage: PipelineStage = PipelineStage.CONVERSION,
                     name: Optional[str] = None, condition: Optional[Callable[[ConversionContext], bool]] = None) -> "ConversionPipeline":
        """添加转换器作为管道步骤
        
        Args:
            converter: 转换器
            stage: 管道阶段
            name: 步骤名称
            condition: 执行条件
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        step_name = name or f"{converter.name}_{stage.value}"
        step = PipelineStep(
            name=step_name,
            stage=stage,
            converter=converter,
            condition=condition
        )
        return self.add_step(step)
    
    def add_pre_validation(self, converter: BaseConverter, name: Optional[str] = None) -> "ConversionPipeline":
        """添加预验证步骤
        
        Args:
            converter: 验证转换器
            name: 步骤名称
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        return self.add_converter(converter, PipelineStage.PRE_VALIDATION, name)
    
    def add_preparation(self, converter: BaseConverter, name: Optional[str] = None) -> "ConversionPipeline":
        """添加准备步骤
        
        Args:
            converter: 准备转换器
            name: 步骤名称
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        return self.add_converter(converter, PipelineStage.PREPARATION, name)
    
    def add_post_processing(self, converter: BaseConverter, name: Optional[str] = None) -> "ConversionPipeline":
        """添加后处理步骤
        
        Args:
            converter: 后处理转换器
            name: 步骤名称
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        return self.add_converter(converter, PipelineStage.POST_PROCESSING, name)
    
    def add_post_validation(self, converter: BaseConverter, name: Optional[str] = None) -> "ConversionPipeline":
        """添加后验证步骤
        
        Args:
            converter: 验证转换器
            name: 步骤名称
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        return self.add_converter(converter, PipelineStage.POST_VALIDATION, name)
    
    def add_error_handler(self, stage: PipelineStage, handler: Callable) -> "ConversionPipeline":
        """添加错误处理器
        
        Args:
            stage: 管道阶段
            handler: 错误处理函数
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        self.error_handlers[stage].append(handler)
        return self
    
    def add_middleware(self, middleware: Callable) -> "ConversionPipeline":
        """添加中间件
        
        Args:
            middleware: 中间件函数
            
        Returns:
            ConversionPipeline: 返回自身以支持链式调用
        """
        self.middleware.append(middleware)
        return self
    
    def execute(self, source: Any, context: ConversionContext) -> Any:
        """执行转换管道
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Returns:
            Any: 转换结果
            
        Raises:
            ConversionError: 管道执行失败
        """
        from datetime import datetime
        
        start_time = datetime.now()
        self._stats["total_executions"] += 1
        
        try:
            self.logger.info(f"开始执行转换管道: {self.name}")
            
            # 执行中间件
            for middleware in self.middleware:
                source, context = middleware(source, context)
            
            result = source
            
            # 按阶段执行步骤
            for stage in PipelineStage:
                stage_steps = [step for step in self.steps if step.stage == stage and step.enabled]
                
                for step in stage_steps:
                    # 检查执行条件
                    if step.condition and not step.condition(context):
                        self.logger.debug(f"跳过步骤 {step.name}: 条件不满足")
                        continue
                    
                    # 执行步骤
                    result = self._execute_step(step, result, context)
            
            # 更新成功统计
            self._stats["successful_executions"] += 1
            self.logger.info(f"转换管道执行成功: {self.name}")
            
            return result
            
        except Exception as e:
            # 更新失败统计
            self._stats["failed_executions"] += 1
            self.logger.error(f"转换管道执行失败: {self.name}, 错误: {e}")
            raise ConversionError(f"管道执行失败: {e}") from e
            
        finally:
            # 更新时间统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self._stats["total_time"] += duration
    
    def _execute_step(self, step: PipelineStep, source: Any, context: ConversionContext) -> Any:
        """执行单个步骤
        
        Args:
            step: 管道步骤
            source: 输入数据
            context: 转换上下文
            
        Returns:
            Any: 步骤输出
            
        Raises:
            ConversionError: 步骤执行失败
        """
        self.logger.debug(f"执行步骤: {step.name}")
        
        # 创建步骤上下文
        step_context = context.create_child_context(
            conversion_type=f"pipeline_step_{step.stage.value}",
            step_name=step.name
        )
        
        # 执行步骤（支持重试）
        last_exception = None
        for attempt in range(step.max_retries + 1):
            try:
                result = step.converter.convert(source, step_context)
                
                # 如果成功，合并上下文并返回
                context.merge_context(step_context)
                return result
                
            except Exception as e:
                last_exception = e
                step.retry_count += 1
                
                if attempt < step.max_retries:
                    self.logger.warning(f"步骤 {step.name} 执行失败，重试 {attempt + 1}/{step.max_retries}: {e}")
                    continue
                else:
                    self.logger.error(f"步骤 {step.name} 执行失败，已达最大重试次数: {e}")
                    
                    # 执行错误处理器
                    self._handle_error(step.stage, e, context)
                    raise ConversionError(f"步骤 {step.name} 执行失败: {e}") from e
    
    def _handle_error(self, stage: PipelineStage, error: Exception, context: ConversionContext) -> None:
        """处理错误
        
        Args:
            stage: 管道阶段
            error: 错误对象
            context: 转换上下文
        """
        handlers = self.error_handlers.get(stage, [])
        
        for handler in handlers:
            try:
                handler(error, context)
            except Exception as handler_error:
                self.logger.error(f"错误处理器执行失败: {handler_error}")
    
    def get_step_names(self, stage: Optional[PipelineStage] = None) -> List[str]:
        """获取步骤名称列表
        
        Args:
            stage: 管道阶段，如果为None则返回所有步骤
            
        Returns:
            List[str]: 步骤名称列表
        """
        if stage is None:
            return [step.name for step in self.steps]
        else:
            return [step.name for step in self.steps if step.stage == stage]
    
    def get_step(self, name: str) -> Optional[PipelineStep]:
        """获取指定名称的步骤
        
        Args:
            name: 步骤名称
            
        Returns:
            Optional[PipelineStep]: 步骤对象，如果不存在则返回None
        """
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def remove_step(self, name: str) -> bool:
        """移除指定名称的步骤
        
        Args:
            name: 步骤名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, step in enumerate(self.steps):
            if step.name == name:
                del self.steps[i]
                self.logger.debug(f"移除管道步骤: {name}")
                return True
        return False
    
    def enable_step(self, name: str) -> bool:
        """启用指定名称的步骤
        
        Args:
            name: 步骤名称
            
        Returns:
            bool: 是否成功启用
        """
        step = self.get_step(name)
        if step:
            step.enabled = True
            return True
        return False
    
    def disable_step(self, name: str) -> bool:
        """禁用指定名称的步骤
        
        Args:
            name: 步骤名称
            
        Returns:
            bool: 是否成功禁用
        """
        step = self.get_step(name)
        if step:
            step.enabled = False
            return True
        return False
    
    def clear_steps(self, stage: Optional[PipelineStage] = None) -> None:
        """清空步骤
        
        Args:
            stage: 管道阶段，如果为None则清空所有步骤
        """
        if stage is None:
            self.steps.clear()
            self.logger.debug("清空所有管道步骤")
        else:
            self.steps = [step for step in self.steps if step.stage != stage]
            self.logger.debug(f"清空 {stage.value} 阶段的管道步骤")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管道统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        
        # 计算平均时间
        if stats["successful_executions"] > 0:
            stats["average_time"] = stats["total_time"] / stats["successful_executions"]
        else:
            stats["average_time"] = 0.0
        
        # 计算成功率
        if stats["total_executions"] > 0:
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
        else:
            stats["success_rate"] = 0.0
        
        # 添加步骤统计
        stats["total_steps"] = len(self.steps)
        stats["enabled_steps"] = len([step for step in self.steps if step.enabled])
        
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_time": 0.0
        }
        
        # 重置步骤重试计数
        for step in self.steps:
            step.retry_count = 0
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 字符串表示
        """
        return f"ConversionPipeline(name='{self.name}', steps={len(self.steps)})"
    
    def __repr__(self) -> str:
        """详细字符串表示
        
        Returns:
            str: 详细字符串表示
        """
        stats = self.get_stats()
        return (f"ConversionPipeline(name='{self.name}', "
                f"steps={len(self.steps)}, "
                f"success_rate={stats['success_rate']:.2%})")