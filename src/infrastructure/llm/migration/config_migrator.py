"""配置迁移工具"""

import logging
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..task_group_manager import TaskGroupManager
from ..exceptions import LLMConfigurationError

logger = logging.getLogger(__name__)


class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self, task_group_manager: TaskGroupManager, config_base_path: str = "configs/llms"):
        """
        初始化配置迁移器
        
        Args:
            task_group_manager: 任务组管理器
            config_base_path: 配置基础路径
        """
        self.task_group_manager = task_group_manager
        self.config_base_path = Path(config_base_path)
        self.migration_log = []
    
    def migrate_global_fallback_to_task_groups(self, backup: bool = True) -> bool:
        """
        将全局降级配置迁移到各个任务组
        
        Args:
            backup: 是否创建备份
            
        Returns:
            是否迁移成功
        """
        try:
            logger.info("开始迁移全局降级配置到任务组")
            
            # 获取全局降级配置
            global_fallback_config = self._load_global_fallback_config()
            if not global_fallback_config:
                logger.warning("未找到全局降级配置，跳过迁移")
                return True
            
            # 获取所有任务组
            task_groups = self.task_group_manager.list_task_groups()
            
            # 创建备份
            if backup:
                self._create_backup(task_groups)
            
            # 为每个任务组添加降级配置
            migrated_count = 0
            for group_name in task_groups:
                if self._migrate_task_group(group_name, global_fallback_config):
                    migrated_count += 1
            
            logger.info(f"迁移完成，成功迁移 {migrated_count}/{len(task_groups)} 个任务组")
            return True
            
        except Exception as e:
            logger.error(f"迁移失败: {e}")
            return False
    
    def _load_global_fallback_config(self) -> Optional[Dict[str, Any]]:
        """加载全局降级配置"""
        try:
            global_fallback_path = self.config_base_path / "global_fallback.yaml"
            if not global_fallback_path.exists():
                return None
            
            with open(global_fallback_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"加载全局降级配置失败: {e}")
            return None
    
    def _create_backup(self, task_groups: List[str]) -> None:
        """创建配置备份"""
        backup_dir = self.config_base_path / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        for group_name in task_groups:
            try:
                group_config_path = self.config_base_path / "groups" / f"{group_name}.yaml"
                if group_config_path.exists():
                    backup_path = backup_dir / f"{group_name}.yaml.backup"
                    with open(group_config_path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    logger.debug(f"创建备份: {backup_path}")
            except Exception as e:
                logger.warning(f"创建备份失败 {group_name}: {e}")
    
    def _migrate_task_group(self, group_name: str, global_fallback_config: Dict[str, Any]) -> bool:
        """
        迁移单个任务组
        
        Args:
            group_name: 任务组名称
            global_fallback_config: 全局降级配置
            
        Returns:
            是否迁移成功
        """
        try:
            # 加载任务组配置
            group_config_path = self.config_base_path / "groups" / f"{group_name}.yaml"
            if not group_config_path.exists():
                logger.warning(f"任务组配置文件不存在: {group_config_path}")
                return False
            
            with open(group_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查是否已经有降级配置
            if "fallback_config" in config:
                logger.debug(f"任务组 {group_name} 已有降级配置，跳过")
                return True
            
            # 添加降级配置
            fallback_config = {
                "strategy": config.get("fallback_strategy", "echelon_down"),
                "fallback_groups": self._get_default_fallback_groups(group_name),
                "max_attempts": global_fallback_config.get("max_attempts", 3),
                "retry_delay": global_fallback_config.get("retry_delay", 1.0),
                "circuit_breaker": global_fallback_config.get("circuit_breaker", {})
            }
            
            config["fallback_config"] = fallback_config
            
            # 保存配置
            with open(group_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"成功迁移任务组: {group_name}")
            self.migration_log.append({
                "task": "migrate_task_group",
                "group_name": group_name,
                "status": "success"
            })
            return True
            
        except Exception as e:
            logger.error(f"迁移任务组失败 {group_name}: {e}")
            self.migration_log.append({
                "task": "migrate_task_group",
                "group_name": group_name,
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def _get_default_fallback_groups(self, group_name: str) -> List[str]:
        """获取默认降级组"""
        task_group = self.task_group_manager.get_task_group(group_name)
        if not task_group:
            return []
        
        # 根据任务组类型生成默认降级组
        if group_name == "fast_group":
            return ["fast_group.echelon2", "fast_group.echelon3"]
        elif group_name == "thinking_group":
            return ["thinking_group.echelon2", "thinking_group.echelon3", "fast_group.echelon1"]
        elif group_name == "plan_group":
            return ["thinking_group.echelon1", "thinking_group.echelon2"]
        else:
            # 通用降级逻辑
            fallback_groups = []
            echelon_names = list(task_group.echelons.keys())
            echelon_names.sort()
            
            for i, echelon_name in enumerate(echelon_names):
                if i > 0:  # 跳过第一个层级
                    fallback_groups.append(f"{group_name}.{echelon_name}")
            
            return fallback_groups
    
    def migrate_polling_pools(self, backup: bool = True) -> bool:
        """
        迁移轮询池配置
        
        Args:
            backup: 是否创建备份
            
        Returns:
            是否迁移成功
        """
        try:
            logger.info("开始迁移轮询池配置")
            
            # 获取所有轮询池
            polling_pools = self.task_group_manager.list_polling_pools()
            
            # 创建备份
            if backup:
                self._create_polling_pool_backup(polling_pools)
            
            # 为每个轮询池添加降级配置
            migrated_count = 0
            for pool_name in polling_pools:
                if self._migrate_polling_pool(pool_name):
                    migrated_count += 1
            
            logger.info(f"轮询池迁移完成，成功迁移 {migrated_count}/{len(polling_pools)} 个轮询池")
            return True
            
        except Exception as e:
            logger.error(f"轮询池迁移失败: {e}")
            return False
    
    def _create_polling_pool_backup(self, polling_pools: List[str]) -> None:
        """创建轮询池配置备份"""
        backup_dir = self.config_base_path / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        for pool_name in polling_pools:
            try:
                pool_config_path = self.config_base_path / "polling_pools" / f"{pool_name}.yaml"
                if pool_config_path.exists():
                    backup_path = backup_dir / f"{pool_name}.yaml.backup"
                    with open(pool_config_path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    logger.debug(f"创建轮询池备份: {backup_path}")
            except Exception as e:
                logger.warning(f"创建轮询池备份失败 {pool_name}: {e}")
    
    def _migrate_polling_pool(self, pool_name: str) -> bool:
        """
        迁移单个轮询池
        
        Args:
            pool_name: 轮询池名称
            
        Returns:
            是否迁移成功
        """
        try:
            # 加载轮询池配置
            pool_config_path = self.config_base_path / "polling_pools" / f"{pool_name}.yaml"
            if not pool_config_path.exists():
                logger.warning(f"轮询池配置文件不存在: {pool_config_path}")
                return False
            
            with open(pool_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查是否已经有降级配置
            if "fallback_config" in config:
                logger.debug(f"轮询池 {pool_name} 已有降级配置，跳过")
                return True
            
            # 添加降级配置
            fallback_config = {
                "strategy": "instance_rotation",
                "max_instance_attempts": 2
            }
            
            config["fallback_config"] = fallback_config
            
            # 保存配置
            with open(pool_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"成功迁移轮询池: {pool_name}")
            self.migration_log.append({
                "task": "migrate_polling_pool",
                "pool_name": pool_name,
                "status": "success"
            })
            return True
            
        except Exception as e:
            logger.error(f"迁移轮询池失败 {pool_name}: {e}")
            self.migration_log.append({
                "task": "migrate_polling_pool",
                "pool_name": pool_name,
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def get_migration_log(self) -> List[Dict[str, Any]]:
        """获取迁移日志"""
        return self.migration_log.copy()
    
    def validate_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        try:
            task_groups = self.task_group_manager.list_task_groups()
            polling_pools = self.task_group_manager.list_polling_pools()
            
            validation_result = {
                "task_groups": {},
                "polling_pools": {},
                "summary": {
                    "total_task_groups": len(task_groups),
                    "valid_task_groups": 0,
                    "total_polling_pools": len(polling_pools),
                    "valid_polling_pools": 0
                }
            }
            
            # 验证任务组
            for group_name in task_groups:
                task_group = self.task_group_manager.get_task_group(group_name)
                if task_group and task_group.fallback_config:
                    validation_result["task_groups"][group_name] = {
                        "valid": True,
                        "has_fallback_config": True
                    }
                    validation_result["summary"]["valid_task_groups"] += 1
                else:
                    validation_result["task_groups"][group_name] = {
                        "valid": False,
                        "has_fallback_config": False
                    }
            
            # 验证轮询池
            for pool_name in polling_pools:
                polling_pool = self.task_group_manager.get_polling_pool(pool_name)
                if polling_pool and polling_pool.fallback_config:
                    validation_result["polling_pools"][pool_name] = {
                        "valid": True,
                        "has_fallback_config": True
                    }
                    validation_result["summary"]["valid_polling_pools"] += 1
                else:
                    validation_result["polling_pools"][pool_name] = {
                        "valid": False,
                        "has_fallback_config": False
                    }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"验证迁移结果失败: {e}")
            return {"error": str(e)}