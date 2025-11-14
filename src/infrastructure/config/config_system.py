"""配置系统核心实现"""

import os
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, cast
from pathlib import Path

from .core.loader import IConfigLoader
from ..exceptions import ConfigurationError
from .core.merger import IConfigMerger
from .utils.validator import IConfigValidator, ValidationResult
from .models.global_config import GlobalConfig
from .models.task_group_config import TaskGroupsConfig
from .models.llm_config import LLMConfig
from .models.agent_config import AgentConfig
from .models.tool_config import ToolConfig
from .models.token_counter_config import TokenCounterConfig
from .utils.env_resolver import EnvResolver
from .utils.file_watcher import FileWatcher
from .error_recovery import ConfigErrorRecovery, ConfigValidatorWithRecovery
from .config_callback_manager import (
    get_global_callback_manager,
    trigger_config_callbacks,
)


class IConfigSystem(ABC):
    """配置系统接口"""

    @abstractmethod
    def load_global_config(self) -> GlobalConfig:
        """加载全局配置

        Returns:
            全局配置对象
        """
        pass

    @abstractmethod
    def load_llm_config(self, name: str) -> LLMConfig:
        """加载LLM配置

        Args:
            name: 配置名称

        Returns:
            LLM配置对象
        """
        pass

    @abstractmethod
    def load_agent_config(self, name: str) -> AgentConfig:
        """加载Agent配置

        Args:
            name: 配置名称

        Returns:
            Agent配置对象
        """
        pass

    @abstractmethod
    def load_tool_config(self, name: str) -> ToolConfig:
        """加载工具配置

        Args:
            name: 配置名称

        Returns:
            工具配置对象
        """
        pass

    @abstractmethod
    def load_token_counter_config(self, name: str) -> "TokenCounterConfig":
        """加载Token计数器配置

        Args:
            name: 配置名称

        Returns:
            Token计数器配置对象
        """
        pass

    @abstractmethod
    def load_task_groups_config(self) -> TaskGroupsConfig:
        """加载任务组配置

        Returns:
            任务组配置对象
        """
        pass

    @abstractmethod
    def reload_configs(self) -> None:
        """重新加载所有配置"""
        pass

    @abstractmethod
    def get_config_path(self, config_type: str, name: str) -> str:
        """获取配置路径

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            配置路径
        """
        pass

    @abstractmethod
    def watch_for_changes(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """监听配置变化

        Args:
            callback: 变化回调函数
        """
        pass

    @abstractmethod
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass

    @abstractmethod
    def list_configs(self, config_type: str) -> List[str]:
        """列出指定类型的所有配置

        Args:
            config_type: 配置类型

        Returns:
            配置名称列表
        """
        pass

    @abstractmethod
    def config_exists(self, config_type: str, name: str) -> bool:
        """检查配置是否存在

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            是否存在
        """
        pass


class ConfigSystem(IConfigSystem):
    """配置系统实现"""

    def __init__(
        self,
        config_loader: IConfigLoader,
        config_merger: IConfigMerger,
        config_validator: IConfigValidator,
        base_path: str = "configs",
        enable_error_recovery: bool = True,
        enable_callback_manager: bool = True,
    ):
        """初始化配置系统

        Args:
            config_loader: 配置加载器
            config_merger: 配置合并器
            config_validator: 配置验证器
            base_path: 配置基础路径
            enable_error_recovery: 是否启用错误恢复
            enable_callback_manager: 是否启用回调管理
        """
        self._config_loader = config_loader
        self._config_merger = config_merger
        self._config_validator = config_validator
        self._base_path = Path(base_path)

        # 配置缓存
        self._cache: Dict[str, Any] = {}
        self._global_config: Optional[GlobalConfig] = None

        # 环境变量解析器
        self._env_resolver: Optional[EnvResolver] = None

        # 文件监听器
        self._file_watcher: Optional[FileWatcher] = None
        self._watch_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        # 错误恢复
        self._error_recovery: Optional[ConfigErrorRecovery] = None
        if enable_error_recovery:
            self._error_recovery = ConfigErrorRecovery()
            self._validator_with_recovery = ConfigValidatorWithRecovery(
                self._error_recovery
            )

        # 回调管理器
        self._callback_manager = None
        if enable_callback_manager:
            self._callback_manager = get_global_callback_manager()

        # 线程锁
        self._lock = threading.RLock()

    def load_global_config(self) -> GlobalConfig:
        """加载全局配置

        Returns:
            全局配置对象
        """
        with self._lock:
            if self._global_config is not None:
                return self._global_config

            # 加载配置文件（带错误恢复）
            config_path = "global.yaml"
            config_data = None

            try:
                config_data = self._config_loader.load(config_path)
            except Exception as e:
                if self._error_recovery:
                    # 尝试错误恢复
                    full_path = self._base_path / config_path
                    if self._error_recovery.recover_config(str(full_path), e):
                        # 恢复成功，再次尝试加载
                        try:
                            config_data = self._config_loader.load(config_path)
                        except Exception as recovery_error:
                            raise ConfigurationError(
                                f"全局配置恢复后仍然无法加载: {recovery_error}"
                            )
                    else:
                        raise ConfigurationError(f"无法恢复全局配置文件: {e}")
                else:
                    raise ConfigurationError(f"加载全局配置文件失败: {e}")

            # 验证配置
            result = self._config_validator.validate_global_config(config_data)
            if not result.is_valid:
                raise ConfigurationError(f"全局配置验证失败: {result.errors}")

            # 创建配置对象
            self._global_config = GlobalConfig(**config_data)

            # 初始化环境变量解析器
            if self._env_resolver is None:
                self._env_resolver = EnvResolver(self._global_config.env_prefix)

            return self._global_config

    def load_llm_config(self, name: str) -> LLMConfig:
        """加载LLM配置

        Args:
            name: 配置名称

        Returns:
            LLM配置对象
        """
        with self._lock:
            cache_key = f"llm_{name}"
            if cache_key in self._cache:
                return cast(LLMConfig, self._cache[cache_key])

            # 加载配置并处理继承
            config_data = self._load_config_with_inheritance("llms", name)

            # 验证配置
            result = self._config_validator.validate_llm_config(config_data)
            if not result.is_valid:
                raise ConfigurationError(f"LLM配置验证失败: {result.errors}")

            # 创建配置对象
            config = LLMConfig(**config_data)
            self._cache[cache_key] = config
            return config

    def load_agent_config(self, name: str) -> AgentConfig:
        """加载Agent配置

        Args:
            name: 配置名称

        Returns:
            Agent配置对象
        """
        with self._lock:
            cache_key = f"agent_{name}"
            if cache_key in self._cache:
                return cast(AgentConfig, self._cache[cache_key])

            # 加载配置并处理继承
            config_data = self._load_config_with_inheritance("agents", name)

            # 验证配置
            result = self._config_validator.validate_agent_config(config_data)
            if not result.is_valid:
                raise ConfigurationError(f"Agent配置验证失败: {result.errors}")

            # 创建配置对象
            config = AgentConfig(**config_data)
            self._cache[cache_key] = config
            return config

    def load_tool_config(self, name: str) -> ToolConfig:
        """加载工具配置

        Args:
            name: 配置名称

        Returns:
            工具配置对象
        """
        with self._lock:
            cache_key = f"tool_{name}"
            if cache_key in self._cache:
                return cast(ToolConfig, self._cache[cache_key])

            # 加载配置并处理继承
            config_data = self._load_config_with_inheritance("tool-sets", name)

            # 验证配置
            result = self._config_validator.validate_tool_config(config_data)
            if not result.is_valid:
                raise ConfigurationError(f"工具配置验证失败: {result.errors}")

            # 创建配置对象
            config = ToolConfig(**config_data)
            self._cache[cache_key] = config
            return config

    def load_token_counter_config(self, name: str) -> TokenCounterConfig:
        """加载Token计数器配置

        Args:
            name: 配置名称

        Returns:
            Token计数器配置对象
        """
        with self._lock:
            cache_key = f"token_counter_{name}"
            if cache_key in self._cache:
                return cast(TokenCounterConfig, self._cache[cache_key])

            # 加载配置并处理继承
            config_data = self._load_config_with_inheritance("llms/tokens_counter", name)

            # 验证配置
            result = self._config_validator.validate_token_counter_config(config_data)
            if not result.is_valid:
                raise ConfigurationError(f"Token计数器配置验证失败: {result.errors}")

            # 创建配置对象
            config = TokenCounterConfig(**config_data)
            self._cache[cache_key] = config
            return config

    def load_task_groups_config(self) -> TaskGroupsConfig:
        """加载任务组配置

        Returns:
            任务组配置对象
        """
        with self._lock:
            cache_key = "task_groups"
            if cache_key in self._cache:
                return cast(TaskGroupsConfig, self._cache[cache_key])

            # 使用任务组管理器加载配置
            from ..llm.task_group_manager import TaskGroupManager
            task_group_manager = TaskGroupManager(self._config_loader)
            config = task_group_manager.load_config()
            
            self._cache[cache_key] = config
            return config

    def reload_configs(self) -> None:
        """重新加载所有配置"""
        with self._lock:
            # 清除缓存
            self._cache.clear()
            self._global_config = None

            # 重新加载配置加载器中的缓存
            self._config_loader.reload()

    def get_config_path(self, config_type: str, name: str) -> str:
        """获取配置路径

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            配置路径
        """
        return f"{config_type}/{name}.yaml"

    def watch_for_changes(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """监听配置变化

        Args:
            callback: 变化回调函数
        """
        with self._lock:
            self._watch_callbacks.append(callback)

            # 如果还没有文件监听器，创建一个
            if self._file_watcher is None:
                self._file_watcher = FileWatcher(
                    str(self._base_path), ["*.yaml", "*.yml"]
                )

                # 添加文件变化回调
                self._file_watcher.add_callback("*.yaml", self._handle_file_change)
                self._file_watcher.add_callback("*.yml", self._handle_file_change)

                # 开始监听
                self._file_watcher.start()

    def stop_watching(self) -> None:
        """停止监听配置变化"""
        with self._lock:
            if self._file_watcher is not None:
                self._file_watcher.stop()
                self._file_watcher = None
            self._watch_callbacks.clear()

    def _load_config_with_inheritance(
        self, config_type: str, name: str
    ) -> Dict[str, Any]:
        """加载配置并处理继承关系

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            配置字典
        """
        # 检查是否为provider目录下的LLM配置
        if config_type == "llms":
            provider_config = self._try_load_provider_config(name)
            if provider_config:
                return provider_config

        # 加载个体配置
        individual_path = self.get_config_path(config_type, name)
        individual_config: Dict[str, Any] = self._config_loader.load(individual_path)

        # 检查是否有组配置
        if "group" in individual_config:
            group_name = individual_config["group"]
            group_path = f"{config_type}/_group.yaml"

            try:
                group_configs = self._config_loader.load(group_path)

                if group_name in group_configs:
                    group_config = group_configs[group_name]
                    # 合并组配置和个体配置
                    merged_config = self._config_merger.merge_group_config(
                        group_config, individual_config
                    )
                    # 重新添加group字段，因为在合并过程中它被移除了
                    merged_config["group"] = group_name
                    return merged_config
            except Exception as e:
                # 如果加载组配置失败，记录警告但继续使用个体配置
                print(f"警告: 加载组配置失败 {group_path}: {e}")

        return individual_config

    def _try_load_provider_config(self, name: str) -> Optional[Dict[str, Any]]:
        """尝试加载provider-based配置

        Args:
            name: 配置名称

        Returns:
            配置字典，如果不是provider配置则返回None
        """
        # 检查是否存在provider目录下的配置
        provider_paths = [
            f"llms/provider/openai/{name}.yaml",
            f"llms/provider/anthropic/{name}.yaml", 
            f"llms/provider/gemini/{name}.yaml"
        ]
        
        for provider_path in provider_paths:
            try:
                individual_config = self._config_loader.load(provider_path)
                
                # 获取provider类型
                provider_type = individual_config.get("provider")
                if not provider_type:
                    # 从路径推断provider类型
                    if "openai" in provider_path:
                        provider_type = "openai"
                    elif "anthropic" in provider_path:
                        provider_type = "anthropic"
                    elif "gemini" in provider_path:
                        provider_type = "gemini"
                
                if provider_type:
                    # 加载provider的common配置
                    common_config_path = f"llms/provider/{provider_type}/common.yaml"
                    try:
                        common_config = self._config_loader.load(common_config_path)
                        
                        # 合并provider common配置和个体配置
                        merged_config = self._merge_provider_config(
                            common_config, individual_config, provider_type
                        )
                        
                        # 检查是否还有组配置需要继承
                        if "group" in merged_config:
                            group_name = merged_config["group"]
                            group_path = "llms/_group.yaml"
                            
                            try:
                                group_configs = self._config_loader.load(group_path)
                                if group_name in group_configs:
                                    group_config = group_configs[group_name]
                                    # 合并组配置
                                    merged_config = self._config_merger.merge_group_config(
                                        group_config, merged_config
                                    )
                                    # 重新添加group字段
                                    merged_config["group"] = group_name
                            except Exception as e:
                                print(f"警告: 加载组配置失败 {group_path}: {e}")
                        
                        return merged_config
                        
                    except Exception as e:
                        print(f"警告: 加载provider common配置失败 {common_config_path}: {e}")
                        # 如果common配置加载失败，返回个体配置
                        return individual_config
                        
            except Exception:
                # 如果provider配置不存在，继续尝试下一个
                continue
        
        # 如果没有找到provider配置，返回None
        return None

    def _merge_provider_config(
        self, 
        common_config: Dict[str, Any], 
        individual_config: Dict[str, Any],
        provider_type: str
    ) -> Dict[str, Any]:
        """合并provider common配置和个体配置
        
        Args:
            common_config: provider common配置
            individual_config: 个体配置
            provider_type: provider类型
            
        Returns:
            合并后的配置
        """
        
        # 从common配置中提取默认参数
        default_parameters = common_config.get("default_parameters", {})
        cache_config = common_config.get("cache_config", {})
        fallback_config = common_config.get("fallback_config", {})
        
        # 创建合并后的配置
        merged = {
            # 基础配置从个体配置获取
            "model_type": individual_config.get("model_type", provider_type),
            "model_name": individual_config.get("model_name"),
            "base_url": individual_config.get("base_url", common_config.get("base_url")),
            "api_key": individual_config.get("api_key"),
            "headers": individual_config.get("headers", common_config.get("headers", {})),
            "provider": individual_config.get("provider", provider_type),
            "token_counter": individual_config.get("token_counter"),
            
            # 参数配置：合并默认参数和个体参数
            "parameters": self._config_merger.deep_merge(
                default_parameters, 
                individual_config.get("parameters", {})
            ),
            
            # 缓存配置：合并默认缓存配置和个体缓存配置
            "supports_caching": individual_config.get(
                "supports_caching", 
                common_config.get("supports_caching", False)
            ),
            "cache_config": self._config_merger.deep_merge(
                cache_config,
                individual_config.get("cache_config", {})
            ),
            
            # 其他配置
            "group": individual_config.get("group"),
            "fallback_enabled": individual_config.get(
                "fallback_enabled",
                fallback_config.get("enabled", True)
            ),
            "fallback_models": individual_config.get("fallback_models", []),
            "max_fallback_attempts": individual_config.get(
                "max_fallback_attempts",
                fallback_config.get("max_attempts", 3)
            ),
            
            # 元数据合并
            "metadata": self._config_merger.deep_merge(
                common_config.get("metadata", {}),
                individual_config.get("metadata", {})
            )
        }
        
        # 移除None值
        merged = {k: v for k, v in merged.items() if v is not None}
        
        return merged

    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件

        Args:
            file_path: 文件路径
        """
        try:
            # 获取相对路径
            rel_path = Path(file_path).relative_to(self._base_path)
            config_path = str(rel_path).replace("\\", "/")

            # 保存旧配置（用于回调）
            old_config = None
            cached_config = self._config_loader.get_config(config_path)
            if cached_config:
                old_config = cached_config.copy()

            # 重新加载配置
            # 先从缓存中移除，确保重新加载
            cache_keys_to_remove = []
            for cache_key in self._cache:
                if config_path in cache_key or config_path.endswith("_group.yaml"):
                    cache_keys_to_remove.append(cache_key)

            for cache_key in cache_keys_to_remove:
                del self._cache[cache_key]

            # 如果是全局配置文件，清除全局配置缓存
            if config_path == "global.yaml":
                self._global_config = None

            # 尝试重新加载配置文件（带错误恢复）
            new_config = None
            try:
                new_config = self._config_loader.load(config_path)
            except Exception as e:
                if self._error_recovery:
                    # 尝试错误恢复
                    if self._error_recovery.recover_config(file_path, e):
                        # 恢复成功，再次尝试加载
                        try:
                            new_config = self._config_loader.load(config_path)
                        except Exception as recovery_error:
                            print(
                                f"错误: 配置恢复后仍然无法加载 {config_path}: {recovery_error}"
                            )
                            return
                    else:
                        print(f"错误: 无法恢复配置文件 {config_path}: {e}")
                        return
                else:
                    print(f"错误: 加载配置文件失败 {config_path}: {e}")
                    return

            # 通知传统回调
            for callback in self._watch_callbacks:
                try:
                    callback(config_path, new_config)
                except Exception as e:
                    print(f"警告: 配置变化回调执行失败: {e}")

            # 通知新的回调管理器
            if self._callback_manager:
                try:
                    trigger_config_callbacks(
                        config_path, old_config, new_config, "file_watcher"
                    )
                except Exception as e:
                    print(f"警告: 配置回调管理器执行失败: {e}")

        except Exception as e:
            print(f"警告: 处理配置文件变化失败 {file_path}: {e}")

    def list_configs(self, config_type: str) -> List[str]:
        """列出指定类型的所有配置

        Args:
            config_type: 配置类型

        Returns:
            配置名称列表
        """
        configs = []
        
        # 查找主配置目录下的配置
        config_dir = self._base_path / config_type
        if config_dir.exists():
            for file_path in config_dir.glob("*.yaml"):
                if file_path.name != "_group.yaml":
                    configs.append(file_path.stem)
        
        # 如果是LLM配置，还要查找provider目录下的配置
        if config_type == "llms":
            provider_dir = self._base_path / "llms" / "provider"
            if provider_dir.exists():
                for provider_subdir in provider_dir.iterdir():
                    if provider_subdir.is_dir():
                        for file_path in provider_subdir.glob("*.yaml"):
                            if file_path.name != "common.yaml":
                                configs.append(file_path.stem)
        
        return configs

    def config_exists(self, config_type: str, name: str) -> bool:
        """检查配置是否存在

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            是否存在
        """
        # 检查主配置路径
        config_path = self._base_path / self.get_config_path(config_type, name)
        if config_path.exists():
            return True
        
        # 如果是LLM配置，检查provider目录
        if config_type == "llms":
            provider_paths = [
                self._base_path / "llms" / "provider" / "openai" / f"{name}.yaml",
                self._base_path / "llms" / "provider" / "anthropic" / f"{name}.yaml",
                self._base_path / "llms" / "provider" / "gemini" / f"{name}.yaml"
            ]
            for provider_path in provider_paths:
                if provider_path.exists():
                    return True
        
        return False

    def get_env_resolver(self) -> EnvResolver:
        """获取环境变量解析器

        Returns:
            环境变量解析器
        """
        if self._env_resolver is None:
            # 加载全局配置以获取环境变量前缀
            global_config = self.load_global_config()
            self._env_resolver = EnvResolver(global_config.env_prefix)

        return self._env_resolver

    def __del__(self) -> None:
        """析构函数，确保停止文件监听"""
        self.stop_watching()