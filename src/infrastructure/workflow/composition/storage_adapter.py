"""组合存储适配器实现

提供组合功能的持久化存储，包括组合配置持久化、组合结果存储、历史记录管理。
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import os
from pathlib import Path
from src.interfaces.dependency_injection import get_logger

from src.infrastructure.storage.base_storage import BaseStorage
from src.infrastructure.common.serialization import Serializer
from src.infrastructure.common.utils.temporal import TemporalManager
from src.infrastructure.common.utils.metadata import MetadataManager

logger = get_logger(__name__)


class CompositionStorageAdapter(BaseStorage):
    """组合存储适配器
    
    负责组合配置和结果的持久化存储。
    遵循Infrastructure层原则，只依赖Interfaces层。
    """
    
    def __init__(
        self,
        storage_path: str = "data/compositions",
        serializer: Optional[Serializer] = None,
        temporal_manager: Optional[TemporalManager] = None,
        metadata_manager: Optional[MetadataManager] = None
    ):
        """初始化组合存储适配器
        
        Args:
            storage_path: 存储路径
            serializer: 序列化器
            temporal_manager: 时间管理器
            metadata_manager: 元数据管理器
        """
        super().__init__(
            serializer=serializer,
            temporal_manager=temporal_manager,
            metadata_manager=metadata_manager
        )
        
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self._storage_path / "configs").mkdir(exist_ok=True)
        (self._storage_path / "results").mkdir(exist_ok=True)
        (self._storage_path / "history").mkdir(exist_ok=True)
        
        self._logger = get_logger(f"{__name__}.CompositionStorageAdapter")
        self._logger.info(f"组合存储适配器初始化完成，存储路径: {storage_path}")
    
    async def save_composition_config(
        self,
        composition_id: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存组合配置
        
        Args:
            composition_id: 组合ID
            config: 组合配置
            metadata: 元数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            self._logger.debug(f"保存组合配置: {composition_id}")
            
            # 准备配置数据
            config_data = {
                "composition_id": composition_id,
                "config": config,
                "type": "composition_config",
                "version": "1.0"
            }
            
            # 添加元数据
            if metadata:
                config_data["metadata"] = metadata
            
            # 保存到文件
            config_file = self._storage_path / "configs" / f"{composition_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self._logger.info(f"组合配置保存成功: {composition_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"保存组合配置失败: {composition_id}, 错误: {e}")
            return False
    
    async def load_composition_config(self, composition_id: str) -> Optional[Dict[str, Any]]:
        """加载组合配置
        
        Args:
            composition_id: 组合ID
            
        Returns:
            Dict[str, Any]: 组合配置，如果不存在则返回None
        """
        try:
            self._logger.debug(f"加载组合配置: {composition_id}")
            
            config_file = self._storage_path / "configs" / f"{composition_id}.json"
            
            if not config_file.exists():
                self._logger.warning(f"组合配置文件不存在: {composition_id}")
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._logger.debug(f"组合配置加载成功: {composition_id}")
            return config_data
            
        except Exception as e:
            self._logger.error(f"加载组合配置失败: {composition_id}, 错误: {e}")
            return None
    
    async def save_composition_result(
        self,
        composition_id: str,
        execution_id: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存组合执行结果
        
        Args:
            composition_id: 组合ID
            execution_id: 执行ID
            result: 执行结果
            metadata: 元数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            self._logger.debug(f"保存组合执行结果: {composition_id}/{execution_id}")
            
            # 准备结果数据
            result_data = {
                "composition_id": composition_id,
                "execution_id": execution_id,
                "result": result,
                "type": "composition_result",
                "version": "1.0"
            }
            
            # 添加元数据
            if metadata:
                result_data["metadata"] = metadata
            
            # 保存到文件
            result_file = (
                self._storage_path / "results" / 
                f"{composition_id}_{execution_id}.json"
            )
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            self._logger.info(f"组合执行结果保存成功: {composition_id}/{execution_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"保存组合执行结果失败: {composition_id}/{execution_id}, 错误: {e}")
            return False
    
    async def load_composition_result(
        self,
        composition_id: str,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """加载组合执行结果
        
        Args:
            composition_id: 组合ID
            execution_id: 执行ID
            
        Returns:
            Dict[str, Any]: 执行结果，如果不存在则返回None
        """
        try:
            self._logger.debug(f"加载组合执行结果: {composition_id}/{execution_id}")
            
            result_file = (
                self._storage_path / "results" / 
                f"{composition_id}_{execution_id}.json"
            )
            
            if not result_file.exists():
                self._logger.warning(f"组合执行结果文件不存在: {composition_id}/{execution_id}")
                return None
            
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            self._logger.debug(f"组合执行结果加载成功: {composition_id}/{execution_id}")
            return result_data
            
        except Exception as e:
            self._logger.error(f"加载组合执行结果失败: {composition_id}/{execution_id}, 错误: {e}")
            return None
    
    async def save_composition_history(
        self,
        composition_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存组合历史记录
        
        Args:
            composition_id: 组合ID
            event_type: 事件类型
            event_data: 事件数据
            metadata: 元数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            self._logger.debug(f"保存组合历史记录: {composition_id}/{event_type}")
            
            # 准备历史数据
            history_data = {
                "composition_id": composition_id,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": self.temporal.format_timestamp(
                    self.temporal.now(), "iso"
                ),
                "type": "composition_history",
                "version": "1.0"
            }
            
            # 添加元数据
            if metadata:
                history_data["metadata"] = metadata
            
            # 保存到文件
            timestamp = self.temporal.format_timestamp(
                self.temporal.now(), "timestamp"
            )
            history_file = (
                self._storage_path / "history" / 
                f"{composition_id}_{timestamp}_{event_type}.json"
            )
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            self._logger.debug(f"组合历史记录保存成功: {composition_id}/{event_type}")
            return True
            
        except Exception as e:
            self._logger.error(f"保存组合历史记录失败: {composition_id}/{event_type}, 错误: {e}")
            return False
    
    async def list_composition_configs(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """列出组合配置
        
        Args:
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 组合配置列表
        """
        try:
            self._logger.debug("列出组合配置")
            
            configs = []
            config_dir = self._storage_path / "configs"
            
            for config_file in config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # 应用过滤条件
                    if filters:
                        match = True
                        for key, value in filters.items():
                            if config_data.get(key) != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    configs.append(config_data)
                    
                except Exception as e:
                    self._logger.warning(f"读取配置文件失败: {config_file}, 错误: {e}")
                    continue
            
            self._logger.debug(f"列出组合配置完成，数量: {len(configs)}")
            return configs
            
        except Exception as e:
            self._logger.error(f"列出组合配置失败: {e}")
            return []
    
    async def list_composition_results(
        self,
        composition_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """列出组合执行结果
        
        Args:
            composition_id: 组合ID（可选）
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 执行结果列表
        """
        try:
            self._logger.debug(f"列出组合执行结果: {composition_id}")
            
            results = []
            result_dir = self._storage_path / "results"
            
            for result_file in result_dir.glob("*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    
                    # 过滤组合ID
                    if composition_id and result_data.get("composition_id") != composition_id:
                        continue
                    
                    # 应用过滤条件
                    if filters:
                        match = True
                        for key, value in filters.items():
                            if result_data.get(key) != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    results.append(result_data)
                    
                except Exception as e:
                    self._logger.warning(f"读取结果文件失败: {result_file}, 错误: {e}")
                    continue
            
            self._logger.debug(f"列出组合执行结果完成，数量: {len(results)}")
            return results
            
        except Exception as e:
            self._logger.error(f"列出组合执行结果失败: {e}")
            return []
    
    async def list_composition_history(
        self,
        composition_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出组合历史记录
        
        Args:
            composition_id: 组合ID（可选）
            event_type: 事件类型（可选）
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 历史记录列表
        """
        try:
            self._logger.debug(f"列出组合历史记录: {composition_id}/{event_type}")
            
            history = []
            history_dir = self._storage_path / "history"
            
            for history_file in history_dir.glob("*.json"):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history_data = json.load(f)
                    
                    # 过滤组合ID
                    if composition_id and history_data.get("composition_id") != composition_id:
                        continue
                    
                    # 过滤事件类型
                    if event_type and history_data.get("event_type") != event_type:
                        continue
                    
                    history.append(history_data)
                    
                    # 限制数量
                    if limit and len(history) >= limit:
                        break
                    
                except Exception as e:
                    self._logger.warning(f"读取历史文件失败: {history_file}, 错误: {e}")
                    continue
            
            # 按时间戳排序（最新的在前）
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            self._logger.debug(f"列出组合历史记录完成，数量: {len(history)}")
            return history
            
        except Exception as e:
            self._logger.error(f"列出组合历史记录失败: {e}")
            return []
    
    async def delete_composition_config(self, composition_id: str) -> bool:
        """删除组合配置
        
        Args:
            composition_id: 组合ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self._logger.debug(f"删除组合配置: {composition_id}")
            
            config_file = self._storage_path / "configs" / f"{composition_id}.json"
            
            if config_file.exists():
                config_file.unlink()
                self._logger.info(f"组合配置删除成功: {composition_id}")
                return True
            else:
                self._logger.warning(f"组合配置文件不存在: {composition_id}")
                return False
                
        except Exception as e:
            self._logger.error(f"删除组合配置失败: {composition_id}, 错误: {e}")
            return False
    
    async def delete_composition_result(
        self,
        composition_id: str,
        execution_id: str
    ) -> bool:
        """删除组合执行结果
        
        Args:
            composition_id: 组合ID
            execution_id: 执行ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self._logger.debug(f"删除组合执行结果: {composition_id}/{execution_id}")
            
            result_file = (
                self._storage_path / "results" / 
                f"{composition_id}_{execution_id}.json"
            )
            
            if result_file.exists():
                result_file.unlink()
                self._logger.info(f"组合执行结果删除成功: {composition_id}/{execution_id}")
                return True
            else:
                self._logger.warning(f"组合执行结果文件不存在: {composition_id}/{execution_id}")
                return False
                
        except Exception as e:
            self._logger.error(f"删除组合执行结果失败: {composition_id}/{execution_id}, 错误: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        try:
            config_count = len(list((self._storage_path / "configs").glob("*.json")))
            result_count = len(list((self._storage_path / "results").glob("*.json")))
            history_count = len(list((self._storage_path / "history").glob("*.json")))
            
            return {
                "storage_path": str(self._storage_path),
                "config_count": config_count,
                "result_count": result_count,
                "history_count": history_count,
                "total_files": config_count + result_count + history_count,
            }
            
        except Exception as e:
            self._logger.error(f"获取存储统计信息失败: {e}")
            return {}
    
    # IStorage 接口实现
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        composition_id = data.get("id", str(hash(str(data))))
        if not await self.save_composition_config(composition_id, data):
            raise RuntimeError(f"Failed to save composition: {composition_id}")
        return composition_id
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        return await self.load_composition_config(id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        config = await self.load_composition_config(id)
        if not config:
            return False
        config.update(updates)
        return await self.save_composition_config(id, config)
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        return await self.delete_composition_config(id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列表数据"""
        configs = await self.list_composition_configs(filters)
        if limit:
            return configs[:limit]
        return configs
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询数据"""
        return []
    
    async def exists(self, id: str) -> bool:
        """检查存在"""
        config = await self.load_composition_config(id)
        return config is not None
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        configs = await self.list_composition_configs(filters)
        return len(configs)
    
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务"""
        try:
            for op in operations:
                op_type = op.get("type")
                if op_type == "save":
                    await self.save(op.get("data", {}))
                elif op_type == "delete":
                    id_val = op.get("id")
                    if id_val is not None:
                        await self.delete(id_val)
            return True
        except Exception:
            return False
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        ids = []
        for data in data_list:
            try:
                id_str = await self.save(data)
                ids.append(id_str)
            except Exception as e:
                self._logger.error(f"Batch save failed: {e}")
        return ids
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        count = 0
        for id_str in ids:
            if await self.delete(id_str):
                count += 1
        return count
    
    def stream_list(self, filters: Dict[str, Any], batch_size: int = 100):
        """流式列表"""
        async def _stream():
            configs = await self.list_composition_configs(filters)
            for i in range(0, len(configs), batch_size):
                yield configs[i:i + batch_size]
        return _stream()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "storage_path": str(self._storage_path),
            "accessible": self._storage_path.exists()
        }
    
    async def connect(self) -> None:
        """连接"""
        pass
    
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    async def is_connected(self) -> bool:
        """检查连接"""
        return self._storage_path.exists()


# 便捷函数
def create_composition_storage_adapter(
    storage_path: str = "data/compositions"
) -> CompositionStorageAdapter:
    """创建组合存储适配器实例
    
    Args:
        storage_path: 存储路径
        
    Returns:
        CompositionStorageAdapter: 组合存储适配器实例
    """
    return CompositionStorageAdapter(storage_path=storage_path)


# 导出实现
__all__ = [
    "CompositionStorageAdapter",
    "create_composition_storage_adapter",
]