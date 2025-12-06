"""Thread检查点扩展功能

提供Thread检查点的扩展功能和工具方法。
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import hashlib

from .models import ThreadCheckpoint, CheckpointStatus, CheckpointType


class CheckpointCompressionHelper:
    """检查点压缩助手"""
    
    @staticmethod
    def compress_state_data(state_data: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """压缩状态数据
        
        Args:
            state_data: 原始状态数据
            
        Returns:
            (压缩后的数据, 压缩率百分比)
        """
        try:
            import gzip
            import pickle
            
            # 序列化并压缩
            serialized = pickle.dumps(state_data)
            compressed = gzip.compress(serialized)
            
            # 计算压缩率
            original_size = len(serialized)
            compressed_size = len(compressed)
            compression_ratio = ((original_size - compressed_size) / original_size) * 100
            
            # 返回压缩数据和压缩率
            return {
                "compressed_data": compressed.hex(),
                "compression_method": "gzip+pickle",
                "original_size": original_size,
                "compressed_size": compressed_size
            }, compression_ratio
            
        except ImportError:
            # 如果没有gzip，返回原始数据
            return state_data, 0
    
    @staticmethod
    def decompress_state_data(compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """解压缩状态数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压后的状态数据
        """
        try:
            import gzip
            import pickle
            
            if "compressed_data" not in compressed_data:
                return compressed_data
            
            # 解压缩
            compressed_bytes = bytes.fromhex(compressed_data["compressed_data"])
            decompressed = gzip.decompress(compressed_bytes)
            state_data = pickle.loads(decompressed)
            
            return state_data
            
        except (ImportError, KeyError, ValueError):
            # 如果解压失败，返回原始数据
            return compressed_data


class CheckpointHashHelper:
    """检查点哈希助手"""
    
    @staticmethod
    def calculate_state_hash(state_data: Dict[str, Any]) -> str:
        """计算状态数据的哈希值
        
        Args:
            state_data: 状态数据
            
        Returns:
            哈希值
        """
        # 序列化状态数据
        serialized = json.dumps(state_data, sort_keys=True, ensure_ascii=False)
        
        # 计算SHA256哈希
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    
    @staticmethod
    def calculate_checkpoint_hash(checkpoint: ThreadCheckpoint) -> str:
        """计算检查点的完整哈希值
        
        Args:
            checkpoint: 检查点
            
        Returns:
            哈希值
        """
        # 构建用于哈希的数据
        hash_data = {
            "thread_id": checkpoint.thread_id,
            "state_data": checkpoint.state_data,
            "metadata": checkpoint.metadata,
            "checkpoint_type": checkpoint.checkpoint_type.value,
            "created_at": checkpoint.created_at.isoformat()
        }
        
        return CheckpointHashHelper.calculate_state_hash(hash_data)
    
    @staticmethod
    def verify_checkpoint_integrity(checkpoint: ThreadCheckpoint, expected_hash: str) -> bool:
        """验证检查点完整性
        
        Args:
            checkpoint: 检查点
            expected_hash: 期望的哈希值
            
        Returns:
            是否完整
        """
        actual_hash = CheckpointHashHelper.calculate_checkpoint_hash(checkpoint)
        return actual_hash == expected_hash


class CheckpointDiffHelper:
    """检查点差异助手"""
    
    @staticmethod
    def calculate_state_diff(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态差异
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            差异信息
        """
        diff = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {}
        }
        
        # 找出所有键
        all_keys = set(old_state.keys()) | set(new_state.keys())
        
        for key in all_keys:
            old_value = old_state.get(key)
            new_value = new_state.get(key)
            
            if key not in old_state:
                diff["added"][key] = new_value
            elif key not in new_state:
                diff["removed"][key] = old_value
            elif old_value != new_value:
                diff["modified"][key] = {
                    "old": old_value,
                    "new": new_value
                }
            else:
                diff["unchanged"][key] = old_value
        
        return diff
    
    @staticmethod
    def calculate_checkpoint_diff(old_checkpoint: ThreadCheckpoint, new_checkpoint: ThreadCheckpoint) -> Dict[str, Any]:
        """计算检查点差异
        
        Args:
            old_checkpoint: 旧检查点
            new_checkpoint: 新检查点
            
        Returns:
            差异信息
        """
        return {
            "state_diff": CheckpointDiffHelper.calculate_state_diff(
                old_checkpoint.state_data, 
                new_checkpoint.state_data
            ),
            "metadata_diff": CheckpointDiffHelper.calculate_state_diff(
                old_checkpoint.metadata, 
                new_checkpoint.metadata
            ),
            "time_diff": {
                "old_created_at": old_checkpoint.created_at.isoformat(),
                "new_created_at": new_checkpoint.created_at.isoformat(),
                "time_delta_seconds": (new_checkpoint.created_at - old_checkpoint.created_at).total_seconds()
            }
        }


class CheckpointAnalysisHelper:
    """检查点分析助手"""
    
    @staticmethod
    def analyze_checkpoint_frequency(checkpoints: List[ThreadCheckpoint]) -> Dict[str, Any]:
        """分析检查点创建频率
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            频率分析结果
        """
        if not checkpoints:
            return {"frequency_per_hour": 0, "frequency_per_day": 0, "pattern": "none"}
        
        # 按时间排序
        sorted_checkpoints = sorted(checkpoints, key=lambda x: x.created_at)
        
        # 计算时间跨度
        time_span = sorted_checkpoints[-1].created_at - sorted_checkpoints[0].created_at
        time_span_hours = time_span.total_seconds() / 3600
        
        if time_span_hours == 0:
            return {"frequency_per_hour": len(checkpoints), "frequency_per_day": len(checkpoints) * 24, "pattern": "burst"}
        
        # 计算频率
        frequency_per_hour = len(checkpoints) / time_span_hours
        frequency_per_day = frequency_per_hour * 24
        
        # 分析模式
        if frequency_per_hour > 10:
            pattern = "high_frequency"
        elif frequency_per_hour > 1:
            pattern = "normal"
        else:
            pattern = "low_frequency"
        
        return {
            "frequency_per_hour": frequency_per_hour,
            "frequency_per_day": frequency_per_day,
            "pattern": pattern,
            "total_checkpoints": len(checkpoints),
            "time_span_hours": time_span_hours
        }
    
    @staticmethod
    def analyze_checkpoint_size_distribution(checkpoints: List[ThreadCheckpoint]) -> Dict[str, Any]:
        """分析检查点大小分布
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            大小分布分析结果
        """
        if not checkpoints:
            return {"distribution": "none"}
        
        sizes = [cp.size_bytes for cp in checkpoints]
        
        # 计算统计信息
        total_size = sum(sizes)
        average_size = total_size / len(sizes)
        max_size = max(sizes)
        min_size = min(sizes)
        
        # 计算分布
        size_ranges = {
            "small": sum(1 for size in sizes if size < 1024),  # < 1KB
            "medium": sum(1 for size in sizes if 1024 <= size < 1024 * 1024),  # 1KB - 1MB
            "large": sum(1 for size in sizes if size >= 1024 * 1024)  # > 1MB
        }
        
        return {
            "total_size_bytes": total_size,
            "average_size_bytes": average_size,
            "max_size_bytes": max_size,
            "min_size_bytes": min_size,
            "distribution": size_ranges,
            "large_checkpoint_percentage": (size_ranges["large"] / len(sizes)) * 100
        }
    
    @staticmethod
    def analyze_checkpoint_type_distribution(checkpoints: List[ThreadCheckpoint]) -> Dict[str, Any]:
        """分析检查点类型分布
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            类型分布分析结果
        """
        if not checkpoints:
            return {"distribution": "none"}
        
        type_counts = {}
        for checkpoint in checkpoints:
            checkpoint_type = checkpoint.checkpoint_type.value
            type_counts[checkpoint_type] = type_counts.get(checkpoint_type, 0) + 1
        
        total = len(checkpoints)
        distribution = {
            checkpoint_type: {
                "count": count,
                "percentage": (count / total) * 100
            }
            for checkpoint_type, count in type_counts.items()
        }
        
        return {
            "distribution": distribution,
            "total_checkpoints": total,
            "unique_types": len(type_counts)
        }


class CheckpointOptimizationHelper:
    """检查点优化助手"""
    
    @staticmethod
    def suggest_optimization_strategy(checkpoints: List[ThreadCheckpoint]) -> Dict[str, Any]:
        """建议优化策略
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            优化建议
        """
        suggestions = []
        
        # 分析频率
        frequency_analysis = CheckpointAnalysisHelper.analyze_checkpoint_frequency(checkpoints)
        if frequency_analysis["pattern"] == "high_frequency":
            suggestions.append({
                "type": "frequency",
                "issue": "检查点创建频率过高",
                "suggestion": "考虑增加检查点创建间隔或使用增量检查点",
                "priority": "high"
            })
        
        # 分析大小
        size_analysis = CheckpointAnalysisHelper.analyze_checkpoint_size_distribution(checkpoints)
        if size_analysis["large_checkpoint_percentage"] > 20:
            suggestions.append({
                "type": "size",
                "issue": "大型检查点比例过高",
                "suggestion": "考虑使用数据压缩或只保存关键状态",
                "priority": "medium"
            })
        
        # 分析类型分布
        type_analysis = CheckpointAnalysisHelper.analyze_checkpoint_type_distribution(checkpoints)
        auto_percentage = type_analysis["distribution"].get("auto", {}).get("percentage", 0)
        if auto_percentage > 80:
            suggestions.append({
                "type": "type_balance",
                "issue": "自动检查点比例过高",
                "suggestion": "考虑增加手动检查点以保留重要状态",
                "priority": "low"
            })
        
        # 分析过期情况
        expired_count = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.EXPIRED)
        if expired_count > len(checkpoints) * 0.3:
            suggestions.append({
                "type": "expiration",
                "issue": "过期检查点比例过高",
                "suggestion": "调整过期策略或增加自动清理频率",
                "priority": "medium"
            })
        
        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "high_priority_count": sum(1 for s in suggestions if s["priority"] == "high"),
            "medium_priority_count": sum(1 for s in suggestions if s["priority"] == "medium"),
            "low_priority_count": sum(1 for s in suggestions if s["priority"] == "low")
        }


class ThreadCheckpointExtension:
    """Thread检查点扩展功能
    
    提供Thread检查点的创建和管理扩展功能。
    """
    
    @staticmethod
    def create_thread_checkpoint(
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> ThreadCheckpoint:
        """创建Thread检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            expiration_hours: 过期小时数
            
        Returns:
            创建的检查点
        """
        checkpoint = ThreadCheckpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            metadata=metadata or {}
        )
        
        if expiration_hours:
            checkpoint.set_expiration(expiration_hours)
        
        return checkpoint
    
    @staticmethod
    def create_backup_checkpoint(original_checkpoint: ThreadCheckpoint) -> ThreadCheckpoint:
        """创建备份检查点
        
        Args:
            original_checkpoint: 原检查点
            
        Returns:
            备份检查点
        """
        backup_metadata = original_checkpoint.metadata.copy()
        backup_metadata.update({
            "backup_of": original_checkpoint.id,
            "backup_timestamp": datetime.now().isoformat(),
            "original_created_at": original_checkpoint.created_at.isoformat()
        })
        
        backup = ThreadCheckpoint(
            thread_id=original_checkpoint.thread_id,
            state_data=original_checkpoint.state_data.copy(),
            checkpoint_type=CheckpointType.MANUAL,  # 备份总是手动类型
            metadata=backup_metadata
        )
        
        # 备份不过期
        return backup
    
    @staticmethod
    def create_checkpoint_chain(
        thread_id: str,
        state_data_list: List[Dict[str, Any]],
        chain_metadata: Optional[Dict[str, Any]] = None
    ) -> List[ThreadCheckpoint]:
        """创建检查点链
        
        Args:
            thread_id: 线程ID
            state_data_list: 状态数据列表
            chain_metadata: 链元数据
            
        Returns:
            检查点链列表
        """
        checkpoints = []
        
        for i, state_data in enumerate(state_data_list):
            metadata = {
                "chain_index": i,
                "chain_length": len(state_data_list),
                "chain_id": f"chain_{thread_id}_{datetime.now().timestamp()}"
            }
            
            if chain_metadata:
                metadata.update(chain_metadata)
            
            checkpoint = ThreadCheckpoint(
                thread_id=thread_id,
                state_data=state_data,
                checkpoint_type=CheckpointType.AUTO,
                metadata=metadata
            )
            
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    @staticmethod
    def should_cleanup_checkpoint(checkpoint: ThreadCheckpoint) -> bool:
        """判断是否应该清理检查点
        
        Args:
            checkpoint: 检查点
            
        Returns:
            是否应该清理
        """
        # 手动检查点和里程碑检查点不自动清理
        if checkpoint.checkpoint_type in [CheckpointType.MANUAL, CheckpointType.MILESTONE]:
            return False
        
        # 错误检查点保留更长时间
        if checkpoint.checkpoint_type == CheckpointType.ERROR:
            # 错误检查点保留3天
            return checkpoint.get_age_hours() > 72
        
        # 自动检查点保留24小时
        return checkpoint.get_age_hours() > 24
    
    @staticmethod
    def get_checkpoint_summary(checkpoint: ThreadCheckpoint) -> Dict[str, Any]:
        """获取检查点摘要
        
        Args:
            checkpoint: 检查点
            
        Returns:
            检查点摘要
        """
        return {
            "id": checkpoint.id,
            "thread_id": checkpoint.thread_id,
            "status": checkpoint.status.value,
            "type": checkpoint.checkpoint_type.value,
            "created_at": checkpoint.created_at.isoformat(),
            "size_bytes": checkpoint.size_bytes,
            "restore_count": checkpoint.restore_count,
            "is_expired": checkpoint.is_expired(),
            "can_restore": checkpoint.can_restore(),
            "age_hours": checkpoint.get_age_hours(),
            "metadata": checkpoint.metadata
        }