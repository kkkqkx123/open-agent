"""配置错误恢复机制

为配置系统提供错误恢复功能，包括备份管理和自动恢复策略。
整合了所有配置错误恢复相关的功能。
"""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from ..common.exceptions.config import ConfigError, ConfigValidationError
from ..common.error_management import handle_error, operation_with_retry


class ConfigBackupManager:
    """配置备份管理器"""

    def __init__(self, backup_dir: str = "configs/backups", max_backups: int = 10):
        """初始化备份管理器

        Args:
            backup_dir: 备份目录
            max_backups: 最大备份数量
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, config_path: str) -> str:
        """创建配置文件备份

        Args:
            config_path: 配置文件路径

        Returns:
            备份文件路径

        Raises:
            ConfigError: 备份失败
        """
        try:
            source_path = Path(config_path)
            if not source_path.exists():
                raise ConfigError(f"配置文件不存在: {config_path}")

            # 生成备份文件名（包含微秒以避免冲突）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = self.backup_dir / backup_name

            # 复制文件
            shutil.copy2(source_path, backup_path)

            # 清理旧备份
            self._cleanup_old_backups(source_path.stem)

            return str(backup_path)

        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "config_path": config_path,
                "operation": "create_backup",
                "module": "config_backup_manager",
                "backup_dir": str(self.backup_dir)
            }
            
            # 记录错误并抛出配置异常
            handle_error(e, error_context)
            raise ConfigError(f"创建配置备份失败: {e}")

    def restore_backup(
        self, config_path: str, backup_timestamp: Optional[str] = None
    ) -> bool:
        """恢复配置文件备份

        Args:
            config_path: 配置文件路径
            backup_timestamp: 备份时间戳，如果为None则恢复最新备份

        Returns:
            是否成功恢复
        """
        try:
            source_path = Path(config_path)
            backup_name_pattern = f"{source_path.stem}_*{source_path.suffix}"

            # 查找备份文件
            if backup_timestamp:
                backup_name = (
                    f"{source_path.stem}_{backup_timestamp}{source_path.suffix}"
                )
                backup_path = self.backup_dir / backup_name
            else:
                # 查找最新备份
                backups = list(self.backup_dir.glob(backup_name_pattern))
                if not backups:
                    return False
                backup_path = max(backups, key=lambda p: p.stat().st_mtime)

            if not backup_path.exists():
                return False

            # 恢复文件
            shutil.copy2(backup_path, source_path)
            return True

        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "config_path": config_path,
                "backup_timestamp": backup_timestamp,
                "operation": "restore_backup",
                "module": "config_backup_manager"
            }
            
            handle_error(e, error_context)
            return False

    def list_backups(self, config_path: str) -> List[Dict[str, Any]]:
        """列出配置文件的所有备份

        Args:
            config_path: 配置文件路径

        Returns:
            备份信息列表
        """
        source_path = Path(config_path)
        backup_name_pattern = f"{source_path.stem}_*{source_path.suffix}"

        backups = []
        for backup_path in self.backup_dir.glob(backup_name_pattern):
            stat = backup_path.stat()
            backups.append(
                {
                    "path": str(backup_path),
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y%m%d_%H%M%S"
                    ),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                }
            )

        # 按时间戳排序（最新的在前）
        backups.sort(key=lambda b: str(b["timestamp"]), reverse=True)
        return backups

    def _cleanup_old_backups(self, config_stem: str) -> None:
        """清理旧备份

        Args:
            config_stem: 配置文件名（不含扩展名）
        """
        backup_name_pattern = f"{config_stem}_*"
        backups = list(self.backup_dir.glob(backup_name_pattern))

        # 按修改时间排序（最新的在前）
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # 删除超出数量限制的备份
        for backup_path in backups[self.max_backups :]:
            try:
                backup_path.unlink()
            except Exception as e:
                # 使用统一错误处理，但不影响备份创建流程
                error_context = {
                    "backup_path": str(backup_path),
                    "operation": "cleanup_old_backup",
                    "module": "config_backup_manager"
                }
                
                handle_error(e, error_context)
                pass  # 忽略删除错误


class ConfigErrorRecovery:
    """配置错误恢复器
    
    整合了所有配置错误恢复相关的功能，包括：
    - 备份恢复策略
    - 默认配置恢复策略
    - 重试和降级策略
    - 自定义恢复策略
    """

    def __init__(self, backup_manager: Optional[ConfigBackupManager] = None):
        """初始化错误恢复器

        Args:
            backup_manager: 备份管理器
        """
        self.backup_manager = backup_manager or ConfigBackupManager()
        self.recovery_strategies: List[Callable[[str, Exception], bool]] = []
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """注册默认恢复策略"""
        # 策略1: 从备份恢复（最高优先级）
        self.recovery_strategies.append(self._recover_from_backup)

        # 策略2: 重置为默认配置
        self.recovery_strategies.append(self._reset_to_default)

        # 策略3: 创建空配置文件（最低优先级）
        self.recovery_strategies.append(self._create_empty_config)

    def recover_config(self, config_path: str, error: Exception) -> bool:
        """尝试恢复配置文件

        Args:
            config_path: 配置文件路径
            error: 发生的错误

        Returns:
            是否成功恢复
        """
        # 尝试各种恢复策略
        for strategy in self.recovery_strategies:
            try:
                if strategy(config_path, error):
                    return True
            except Exception as e:
                # 使用统一错误处理记录恢复策略失败
                error_context = {
                    "config_path": config_path,
                    "strategy": strategy.__name__,
                    "operation": "config_recovery",
                    "module": "config_error_recovery"
                }
                
                handle_error(e, error_context)
                continue  # 尝试下一个策略

        return False

    def _recover_from_backup(self, config_path: str, error: Exception) -> bool:
        """从备份恢复配置

        Args:
            config_path: 配置文件路径
            error: 发生的错误

        Returns:
            是否成功恢复
        """
        return self.backup_manager.restore_backup(config_path)

    def _reset_to_default(self, config_path: str, error: Exception) -> bool:
        """重置为默认配置

        Args:
            config_path: 配置文件路径
            error: 发生的错误

        Returns:
            是否成功恢复
        """
        # 这里可以实现默认配置模板逻辑
        # 简化处理，创建一个基本的YAML结构
        default_configs = {
            "global.yaml": {
                "name": "global",
                "type": "global",
                "log_level": "INFO",
                "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
                "secret_patterns": ["sk-[a-zA-Z0-9]{20,}"],
                "env": "development",
                "debug": False,
            },
            "_group.yaml": {
                "name": "group_config",
                "type": "group"
            },
        }

        config_name = Path(config_path).name
        if config_name in default_configs:
            try:
                import yaml

                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(default_configs[config_name], f, default_flow_style=False)
                return True
            except Exception as e:
                # 使用统一错误处理
                error_context = {
                    "config_path": config_path,
                    "config_name": config_name,
                    "operation": "reset_to_default",
                    "module": "config_error_recovery"
                }
                
                handle_error(e, error_context)
                pass

        return False

    def _create_empty_config(self, config_path: str, error: Exception) -> bool:
        """创建空配置文件

        Args:
            config_path: 配置文件路径
            error: 发生的错误

        Returns:
            是否成功恢复
        """
        try:
            # 确保目录存在
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)

            # 创建空文件（使用英文注释避免编码问题）
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("# Configuration file - auto created\n")

            return True
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "config_path": config_path,
                "operation": "create_empty_config",
                "module": "config_error_recovery"
            }
            
            handle_error(e, error_context)
            return False

    def add_recovery_strategy(self, strategy: Callable[[str, Exception], bool]) -> None:
        """添加自定义恢复策略

        Args:
            strategy: 恢复策略函数
        """
        # 将自定义策略插入到列表开头，使其优先执行
        self.recovery_strategies.insert(0, strategy)

    def can_recover(self, config_path: str) -> bool:
        """检查是否可以恢复配置

        Args:
            config_path: 配置文件路径

        Returns:
            是否可以恢复
        """
        # 检查是否有备份
        backups = self.backup_manager.list_backups(config_path)
        if backups:
            return True

        # 检查是否可以创建默认配置
        config_name = Path(config_path).name
        if config_name in ["global.yaml", "_group.yaml"]:
            return True

        # 检查是否可以创建空文件
        return True
    
    # 从 error_handler.py 移动过来的恢复策略
    @staticmethod
    def retry_config_load(config_loader_func: Callable, max_retries: int = 3) -> Any:
        """重试配置加载"""
        return operation_with_retry(
            config_loader_func,
            max_retries=max_retries,
            retryable_exceptions=(IOError, TimeoutError, ConnectionError),
            context={"operation": "config_load"}
        )
    
    @staticmethod
    def fallback_to_default_config(primary_config_func: Callable, default_config_func: Callable) -> Any:
        """降级到默认配置"""
        from src.services.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            return primary_config_func()
        except Exception as e:
            logger.warning(f"主配置加载失败，使用默认配置: {e}")
            return default_config_func()
    
    @staticmethod
    def validate_config_before_load(config_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """加载前验证配置"""
        from src.services.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            # 简单的配置验证逻辑
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in config_data:
                    raise ConfigValidationError(f"缺少必需字段: {field}")
            
            return True
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False


class ConfigValidatorWithRecovery:
    """带错误恢复的配置验证器"""

    def __init__(self, error_recovery: Optional[ConfigErrorRecovery] = None):
        """初始化验证器

        Args:
            error_recovery: 错误恢复器
        """
        self.error_recovery = error_recovery or ConfigErrorRecovery()

    def validate_with_recovery(
        self,
        config_path: str,
        validator: Callable[[Dict[str, Any]], bool],
        config_loader: Callable[[str], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """验证配置并在失败时尝试恢复

        Args:
            config_path: 配置文件路径
            validator: 验证函数
            config_loader: 配置加载函数

        Returns:
            配置字典

        Raises:
            ConfigError: 无法恢复的错误
        """
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                # 尝试加载配置
                config = config_loader(config_path)

                # 验证配置
                if validator(config):
                    return config
                else:
                    raise ConfigError("配置验证失败")

            except Exception as e:
                last_error = e
                
                # 使用统一错误处理
                error_context = {
                    "config_path": config_path,
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "operation": "validate_with_recovery",
                    "module": "config_validator_with_recovery"
                }
                
                handle_error(e, error_context)

                # 如果不是最后一次尝试，尝试恢复
                if attempt < max_attempts - 1:
                    if self.error_recovery.recover_config(config_path, e):
                        # 等待一小段时间再重试
                        time.sleep(0.1)
                        continue

        # 所有尝试都失败了
        final_error_context = {
            "config_path": config_path,
            "max_attempts": max_attempts,
            "operation": "validate_with_recovery_final",
            "module": "config_validator_with_recovery"
        }
        
        if last_error:
            handle_error(last_error, final_error_context)
        raise ConfigError(f"无法加载或验证配置文件 {config_path}: {last_error}")


# 便捷函数
def create_backup_manager(backup_dir: str = "configs/backups", max_backups: int = 10) -> ConfigBackupManager:
    """创建备份管理器的便捷函数
    
    Args:
        backup_dir: 备份目录
        max_backups: 最大备份数量
        
    Returns:
        备份管理器实例
    """
    return ConfigBackupManager(backup_dir, max_backups)


def create_error_recovery(backup_manager: Optional[ConfigBackupManager] = None) -> ConfigErrorRecovery:
    """创建错误恢复器的便捷函数
    
    Args:
        backup_manager: 备份管理器
        
    Returns:
        错误恢复器实例
    """
    return ConfigErrorRecovery(backup_manager)