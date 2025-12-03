"""LLM配置处理器

专门处理LLM配置的继承关系，包括Provider路径解析。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING
from src.core.config.processor.config_processor_chain import IConfigProcessor
from src.core.common.exceptions.config import ConfigError

if TYPE_CHECKING:
    from src.interfaces.common_infra import ILogger


class LLMInheritanceProcessor(IConfigProcessor):
    """LLM继承处理器
    
    扩展了基础的继承处理器，支持：
    1. Provider路径解析（如 "provider/openai/common"）
    2. 智能配置合并策略
    3. 循环继承检测
    """
    
    def __init__(self, base_config_path: str = "configs/llms", logger: Optional["ILogger"] = None):
        """初始化LLM继承处理器
        
        Args:
            base_config_path: LLM配置基础路径
            logger: 日志记录器实例（可选）
        """
        self.base_config_path = Path(base_config_path)
        self._loading_stack: List[str] = []
        self.logger = logger
        if self.logger:
            self.logger.debug(f"LLM继承处理器初始化完成，基础路径: {self.base_config_path}")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置继承
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        # 检查循环继承
        if config_path in self._loading_stack:
            cycle_path = " -> ".join(self._loading_stack[self._loading_stack.index(config_path):] + [config_path])
            raise ConfigError(f"检测到循环继承: {cycle_path}")
        
        # 检查是否有继承配置
        inherits_from = config.get("inherits_from")
        if not inherits_from:
            return config
        
        self._loading_stack.append(config_path)
        
        try:
            # 加载父配置
            parent_config = self._load_parent_config(inherits_from, config_path)
            
            # 合并配置（子配置覆盖父配置）
            merged_config = self._merge_configs(parent_config, config)
            
            # 递归处理继承链
            if "inherits_from" in merged_config:
                result = self.process(merged_config, config_path)
            else:
                result = merged_config
            
            return result
            
        finally:
            self._loading_stack.pop()
    
    def _load_parent_config(self, inherits_from: str, current_path: str) -> Dict[str, Any]:
        """加载父配置
        
        Args:
            inherits_from: 继承的配置路径
            current_path: 当前配置路径
            
        Returns:
            父配置数据
        """
        # 解析继承路径
        if isinstance(inherits_from, list):
            # 多重继承，合并多个父配置
            parent_config = {}
            for parent_path in inherits_from:
                single_parent = self._load_single_parent_config(parent_path, current_path)
                parent_config = self._merge_configs(parent_config, single_parent)
            return parent_config
        else:
            # 单一继承
            return self._load_single_parent_config(inherits_from, current_path)
    
    def _load_single_parent_config(self, parent_path: str, current_path: str) -> Dict[str, Any]:
        """加载单个父配置
        
        Args:
            parent_path: 父配置路径
            current_path: 当前配置路径
            
        Returns:
            父配置数据
        """
        # 解析父配置路径
        full_parent_path = self._resolve_parent_path(parent_path, current_path)
        
        if not full_parent_path.exists():
            raise ConfigError(f"继承配置文件不存在: {full_parent_path}")
        
        # 加载父配置文件
        try:
            import yaml
            with open(full_parent_path, 'r', encoding='utf-8') as f:
                parent_config = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"加载继承配置文件失败 {full_parent_path}: {e}")
        
        return parent_config
    
    def _resolve_parent_path(self, parent_path: str, current_path: str) -> Path:
        """解析父配置路径
        
        支持以下路径格式：
        1. 相对路径：相对于当前配置文件的目录
        2. Provider路径：以 "provider/" 开头，相对于LLM配置基础路径
        3. 绝对路径：相对于LLM配置基础路径
        
        Args:
            parent_path: 父配置路径
            current_path: 当前配置路径
            
        Returns:
            解析后的完整路径
        """
        # 检查是否是Provider路径
        if parent_path.startswith("provider/"):
            # Provider路径：相对于LLM配置基础路径
            full_path = self.base_config_path / parent_path
            if self.logger:
                self.logger.debug(f"解析Provider路径: {parent_path} -> {full_path}")
        elif parent_path.startswith("/"):
            # 绝对路径：相对于LLM配置基础路径
            full_path = self.base_config_path / parent_path.lstrip("/")
            if self.logger:
                self.logger.debug(f"解析绝对路径: {parent_path} -> {full_path}")
        else:
            # 相对路径：相对于当前配置文件的目录
            current_dir = Path(current_path).parent
            full_path = current_dir / parent_path
            if self.logger:
                self.logger.debug(f"解析相对路径: {parent_path} -> {full_path}")
        
        # 确保文件有正确的扩展名
        if not full_path.suffix:
            # 尝试添加支持的扩展名
            for ext in ['.yaml', '.yml', '.json']:
                test_path = full_path.with_suffix(ext)
                if test_path.exists():
                    return test_path
            # 如果都没有找到，默认使用.yaml
            full_path = full_path.with_suffix('.yaml')
        
        return full_path
    
    def _merge_configs(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（子配置覆盖父配置）
        
        使用智能合并策略：
        1. 基本类型：直接覆盖
        2. 字典：递归合并
        3. 列表：根据字段类型选择合并策略
        
        Args:
            parent: 父配置
            child: 子配置
            
        Returns:
            合并后的配置
        """
        result = parent.copy()
        
        for key, value in child.items():
            if key == "inherits_from":
                # 跳过inherits_from字段，因为它已在上层处理
                continue
            
            if key in result:
                merged_value = self._merge_values(result[key], value, key)
                result[key] = merged_value
            else:
                result[key] = value
        
        return result
    
    def _merge_values(self, parent_value: Any, child_value: Any, key: str) -> Any:
        """合并两个值
        
        Args:
            parent_value: 父值
            child_value: 子值
            key: 字段名
            
        Returns:
            合并后的值
        """
        # 如果两个值都是字典，递归合并
        if isinstance(parent_value, dict) and isinstance(child_value, dict):
            return self._merge_configs(parent_value, child_value)
        
        # 如果两个值都是列表，根据字段类型选择合并策略
        if isinstance(parent_value, list) and isinstance(child_value, list):
            return self._merge_lists(parent_value, child_value, key)
        
        # 其他情况直接覆盖
        return child_value
    
    def _merge_lists(self, parent_list: List[Any], child_list: List[Any], key: str) -> List[Any]:
        """合并列表
        
        根据字段名选择合并策略：
        1. 某些字段使用替换策略（如 models, endpoints）
        2. 某些字段使用追加策略（如 tags, capabilities）
        3. 某些字段使用去重合并策略
        
        Args:
            parent_list: 父列表
            child_list: 子列表
            key: 字段名
            
        Returns:
            合并后的列表
        """
        # 替换策略的字段
        replace_fields = {"models", "endpoints", "apis", "servers"}
        # 追加策略的字段
        append_fields = {"tags", "capabilities", "features", "middleware"}
        # 去重合并策略的字段
        dedup_fields = {"allowed_origins", "allowed_hosts", "permissions"}
        
        if key in replace_fields:
            # 替换策略：子列表完全替换父列表
            return child_list
        elif key in append_fields:
            # 追加策略：合并列表，保持顺序
            return parent_list + child_list
        elif key in dedup_fields:
            # 去重合并策略：合并并去重，保持顺序
            merged = parent_list + child_list
            seen = set()
            result = []
            for item in merged:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        else:
            # 默认策略：子列表替换父列表
            return child_list


class LLMConfigProcessorChain:
    """LLM配置处理器链
    
    专门用于LLM配置的处理链，包含：
    1. 继承处理器（支持Provider路径）
    2. 环境变量处理器
    3. 引用处理器
    """
    
    def __init__(self, base_config_path: str = "configs/llms", logger: Optional["ILogger"] = None):
        """初始化LLM配置处理器链
        
        Args:
            base_config_path: LLM配置基础路径
            logger: 日志记录器实例（可选）
        """
        self.base_config_path = base_config_path
        self.processors: List[IConfigProcessor] = []
        self.logger = logger
        
        # 添加默认处理器
        self._setup_default_processors()
        
        if self.logger:
            self.logger.debug("LLM配置处理器链初始化完成")
    
    def _setup_default_processors(self) -> None:
        """设置默认处理器"""
        # 1. 继承处理器（支持Provider路径）
        self.add_processor(LLMInheritanceProcessor(self.base_config_path, self.logger))
        
        # 2. 环境变量处理器
        from src.core.config.processor.config_processor_chain import EnvironmentVariableProcessor
        self.add_processor(EnvironmentVariableProcessor())
        
        # 3. 引用处理器
        from src.core.config.processor.config_processor_chain import ReferenceProcessor
        self.add_processor(ReferenceProcessor())
    
    def add_processor(self, processor: IConfigProcessor) -> None:
        """添加处理器
        
        Args:
            processor: 配置处理器
        """
        self.processors.append(processor)
        if self.logger:
            self.logger.debug(f"已添加LLM配置处理器: {processor.__class__.__name__}")
    
    def process_config(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        result = config
        
        for i, processor in enumerate(self.processors):
            try:
                if self.logger:
                    self.logger.debug(f"执行LLM处理器 {i+1}/{len(self.processors)}: {processor.__class__.__name__}")
                result = processor.process(result, config_path)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"LLM处理器 {processor.__class__.__name__} 执行失败: {e}")
                raise
        
        if self.logger:
            self.logger.debug(f"LLM配置处理完成，共执行 {len(self.processors)} 个处理器")
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