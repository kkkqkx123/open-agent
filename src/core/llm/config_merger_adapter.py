"""LLM配置合并适配器

复用通用配置合并功能，添加LLM特定的合并逻辑。
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from src.services.logger import get_logger
from src.core.common.utils.dict_merger import DictMerger
from src.core.config.config_loader import merge_configs

logger = get_logger(__name__)


@dataclass
class LLMMergeRule:
    """LLM特定合并规则"""
    field_path: str
    merge_strategy: str  # "override", "merge", "append", "concat"
    priority: int  # 优先级，数字越大优先级越高
    condition: Optional[callable] = None  # 合并条件
    description: Optional[str] = None


class LLMConfigMergerAdapter:
    """LLM配置合并适配器
    
    复用通用配置合并功能，添加LLM特定的合并逻辑。
    """
    
    def __init__(self, base_merger: Optional[DictMerger] = None):
        """初始化适配器
        
        Args:
            base_merger: 基础字典合并器
        """
        self.base_merger = base_merger or DictMerger()
        self.llm_rules: List[LLMMergeRule] = []
        self._setup_llm_merge_rules()
        logger.debug("LLM配置合并适配器初始化完成")
    
    def _setup_llm_merge_rules(self) -> None:
        """设置LLM特定合并规则"""
        self.llm_rules.extend([
            # 基础信息覆盖规则
            LLMMergeRule(
                field_path="model_name",
                merge_strategy="override",
                priority=100,
                description="模型名称直接覆盖"
            ),
            
            LLMMergeRule(
                field_path="model_type",
                merge_strategy="override",
                priority=100,
                description="模型类型直接覆盖"
            ),
            
            # API配置合并规则
            LLMMergeRule(
                field_path="api_key",
                merge_strategy="override",
                priority=90,
                description="API密钥直接覆盖"
            ),
            
            LLMMergeRule(
                field_path="base_url",
                merge_strategy="override",
                priority=90,
                description="基础URL直接覆盖"
            ),
            
            LLMMergeRule(
                field_path="headers",
                merge_strategy="merge",
                priority=80,
                description="请求头合并"
            ),
            
            # 参数配置合并规则
            LLMMergeRule(
                field_path="parameters",
                merge_strategy="merge",
                priority=70,
                description="模型参数合并"
            ),
            
            LLMMergeRule(
                field_path="api_formats",
                merge_strategy="merge",
                priority=70,
                description="API格式配置合并"
            ),
            
            # 重试和超时配置合并规则
            LLMMergeRule(
                field_path="retry_config",
                merge_strategy="merge",
                priority=60,
                description="重试配置合并"
            ),
            
            LLMMergeRule(
                field_path="timeout_config",
                merge_strategy="merge",
                priority=60,
                description="超时配置合并"
            ),
            
            # 缓存配置合并规则
            LLMMergeRule(
                field_path="cache_config",
                merge_strategy="merge",
                priority=50,
                description="缓存配置合并"
            ),
            
            # 降级配置合并规则
            LLMMergeRule(
                field_path="fallback_models",
                merge_strategy="append",
                priority=40,
                description="降级模型列表追加"
            ),
            
            LLMMergeRule(
                field_path="fallback_groups",
                merge_strategy="append",
                priority=40,
                description="降级组列表追加"
            ),
            
            # 元数据合并规则
            LLMMergeRule(
                field_path="metadata",
                merge_strategy="merge",
                priority=30,
                description="元数据合并"
            ),
            
            # 连接池配置合并规则
            LLMMergeRule(
                field_path="connection_pool_config",
                merge_strategy="merge",
                priority=50,
                description="连接池配置合并"
            )
        ])
    
    def merge_llm_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并LLM配置
        
        Args:
            configs: 配置列表，按优先级排序（后面的覆盖前面的）
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        if not configs:
            return {}
        
        if len(configs) == 1:
            return configs[0].copy()
        
        logger.debug(f"开始合并 {len(configs)} 个LLM配置")
        
        # 1. 使用通用合并器进行基础合并
        base_result = self.base_merger.deep_merge({}, *configs)
        logger.debug("通用配置合并完成")
        
        # 2. 应用LLM特定的合并规则
        llm_result = self._apply_llm_merge_rules(base_result, configs)
        logger.debug("LLM特定合并规则应用完成")
        
        # 3. 后处理
        final_result = self._post_process_config(llm_result, configs)
        logger.debug("配置后处理完成")
        
        logger.info("LLM配置合并完成")
        return final_result
    
    def merge_provider_configs(self, common_config: Dict[str, Any], 
                             model_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并Provider配置
        
        Args:
            common_config: Provider通用配置
            model_config: 模型特定配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        logger.debug("合并Provider配置")
        
        # 添加Provider元信息
        merged = self.merge_llm_configs([common_config, model_config])
        
        # 添加Provider特定的元信息
        if "_provider_meta" in model_config:
            merged["_provider_meta"] = model_config["_provider_meta"]
        
        return merged
    
    def merge_task_group_configs(self, base_config: Dict[str, Any], 
                               echelon_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并任务组配置
        
        Args:
            base_config: 基础配置
            echelon_config: 层级配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        logger.debug("合并任务组配置")
        
        # 任务组配置有特殊的合并逻辑
        merged = base_config.copy()
        
        # 层级配置优先级更高
        for key, value in echelon_config.items():
            if key == "parameters":
                # 参数需要特殊合并
                merged[key] = self._merge_parameters(merged.get(key, {}), value)
            elif key in ["retry_config", "timeout_config", "connection_pool_config"]:
                # 配置对象合并
                merged[key] = self._merge_config_objects(merged.get(key, {}), value)
            else:
                # 直接覆盖
                merged[key] = value
        
        return merged
    
    def _apply_llm_merge_rules(self, base_config: Dict[str, Any], 
                             source_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """应用LLM特定的合并规则
        
        Args:
            base_config: 基础合并结果
            source_configs: 源配置列表
            
        Returns:
            Dict[str, Any]: 应用规则后的配置
        """
        result = base_config.copy()
        
        # 按优先级排序规则
        sorted_rules = sorted(self.llm_rules, key=lambda x: x.priority, reverse=True)
        
        for rule in sorted_rules:
            if rule.field_path not in result:
                continue
            
            # 检查合并条件
            if rule.condition and not rule.condition(result, source_configs):
                continue
            
            # 应用合并策略
            field_value = result[rule.field_path]
            merged_value = self._apply_merge_strategy(
                rule.field_path, 
                field_value, 
                source_configs, 
                rule.merge_strategy
            )
            
            result[rule.field_path] = merged_value
            logger.debug(f"应用合并规则 [{rule.field_path}]: {rule.description}")
        
        return result
    
    def _apply_merge_strategy(self, field_path: str, current_value: Any, 
                            source_configs: List[Dict[str, Any]], 
                            strategy: str) -> Any:
        """应用合并策略
        
        Args:
            field_path: 字段路径
            current_value: 当前值
            source_configs: 源配置列表
            strategy: 合并策略
            
        Returns:
            Any: 合并后的值
        """
        if strategy == "override":
            # 直接覆盖，使用最后一个非空值
            for config in reversed(source_configs):
                if field_path in config and config[field_path] is not None:
                    return config[field_path]
            return current_value
        
        elif strategy == "merge":
            # 深度合并
            if isinstance(current_value, dict):
                for config in source_configs:
                    if field_path in config and isinstance(config[field_path], dict):
                        current_value = self.base_merger.deep_merge(
                            current_value, config[field_path]
                        )
            return current_value
        
        elif strategy == "append":
            # 列表追加
            if not isinstance(current_value, list):
                current_value = [current_value] if current_value is not None else []
            
            for config in source_configs:
                if field_path in config:
                    value = config[field_path]
                    if isinstance(value, list):
                        current_value.extend(value)
                    else:
                        current_value.append(value)
            
            # 去重
            return list(dict.fromkeys(current_value))
        
        elif strategy == "concat":
            # 字符串连接
            if not isinstance(current_value, str):
                current_value = str(current_value) if current_value is not None else ""
            
            for config in source_configs:
                if field_path in config:
                    value = config[field_path]
                    if value:
                        if current_value:
                            current_value += " "
                        current_value += str(value)
            
            return current_value
        
        else:
            logger.warning(f"未知的合并策略: {strategy}")
            return current_value
    
    def _merge_parameters(self, base_params: Dict[str, Any], 
                         override_params: Dict[str, Any]) -> Dict[str, Any]:
        """合并模型参数
        
        Args:
            base_params: 基础参数
            override_params: 覆盖参数
            
        Returns:
            Dict[str, Any]: 合并后的参数
        """
        result = base_params.copy()
        result.update(override_params)
        return result
    
    def _merge_config_objects(self, base_obj: Dict[str, Any], 
                            override_obj: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置对象
        
        Args:
            base_obj: 基础配置对象
            override_obj: 覆盖配置对象
            
        Returns:
            Dict[str, Any]: 合并后的配置对象
        """
        result = base_obj.copy()
        for key, value in override_obj.items():
            if value is not None:
                result[key] = value
        return result
    
    def _post_process_config(self, config: Dict[str, Any], 
                           source_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """配置后处理
        
        Args:
            config: 合并后的配置
            source_configs: 源配置列表
            
        Returns:
            Dict[str, Any]: 后处理后的配置
        """
        # 1. 清理空值
        config = self._clean_empty_values(config)
        
        # 2. 验证配置一致性
        config = self._validate_config_consistency(config)
        
        # 3. 添加合并元信息
        config["_merge_meta"] = {
            "source_count": len(source_configs),
            "merge_timestamp": self._get_timestamp()
        }
        
        return config
    
    def _clean_empty_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """清理空值
        
        Args:
            config: 配置字典
            
        Returns:
            Dict[str, Any]: 清理后的配置
        """
        def clean_value(value):
            if isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items() if v is not None}
            elif isinstance(value, list):
                return [clean_value(item) for item in value if item is not None]
            else:
                return value
        
        return clean_value(config)
    
    def _validate_config_consistency(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置一致性
        
        Args:
            config: 配置字典
            
        Returns:
            Dict[str, Any]: 验证后的配置
        """
        # 验证model_type和provider的一致性
        model_type = config.get("model_type")
        provider = config.get("provider")
        
        if model_type and provider and model_type != provider:
            logger.warning(f"model_type ({model_type}) 与 provider ({provider}) 不一致，使用 model_type")
            config["provider"] = model_type
        
        # 验证函数调用配置一致性
        function_calling_supported = config.get("function_calling_supported", True)
        function_calling_mode = config.get("function_calling_mode", "auto")
        
        if not function_calling_supported and function_calling_mode != "none":
            logger.warning("函数调用不支持，将模式设置为none")
            config["function_calling_mode"] = "none"
        
        return config
    
    def _get_timestamp(self) -> str:
        """获取时间戳
        
        Returns:
            str: 时间戳字符串
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def add_merge_rule(self, rule: LLMMergeRule) -> None:
        """添加合并规则
        
        Args:
            rule: 合并规则
        """
        self.llm_rules.append(rule)
        logger.debug(f"添加合并规则: {rule.field_path}")
    
    def remove_merge_rule(self, field_path: str) -> bool:
        """移除合并规则
        
        Args:
            field_path: 字段路径
            
        Returns:
            bool: 是否成功移除
        """
        original_count = len(self.llm_rules)
        self.llm_rules = [rule for rule in self.llm_rules if rule.field_path != field_path]
        removed = len(self.llm_rules) < original_count
        
        if removed:
            logger.debug(f"移除合并规则: {field_path}")
        
        return removed
    
    def get_merge_rules_summary(self) -> Dict[str, Any]:
        """获取合并规则摘要
        
        Returns:
            Dict[str, Any]: 规则摘要信息
        """
        rules_by_strategy = {}
        for rule in self.llm_rules:
            strategy = rule.merge_strategy
            if strategy not in rules_by_strategy:
                rules_by_strategy[strategy] = []
            rules_by_strategy[strategy].append(rule.field_path)
        
        return {
            "total_rules": len(self.llm_rules),
            "rules_by_strategy": rules_by_strategy,
            "rule_descriptions": {
                rule.field_path: rule.description 
                for rule in self.llm_rules 
                if rule.description
            }
        }