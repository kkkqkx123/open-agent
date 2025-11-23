"""按键序列监控器 - 用于调试和监控键盘输入序列"""

import time
from typing import List, Dict, Any, Optional
from collections import defaultdict


class SequenceMonitor:
    """按键序列监控器"""
    
    def __init__(self, max_history: int = 100):
        """初始化按键序列监控器
        
        Args:
            max_history: 最大历史记录数
        """
        self.sequences: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.start_time = time.time()
        self.sequence_counts = defaultdict(int)
        self.total_sequences = 0
        self.total_bytes = 0
    
    def add_sequence(self, sequence: str, parsed_key: Optional[str] = None) -> None:
        """添加按键序列
        
        Args:
            sequence: 原始按键序列字符串
            parsed_key: 解析后的按键名称
        """
        entry = {
            'timestamp': time.time() - self.start_time,
            'sequence': repr(sequence),
            'parsed_key': parsed_key,
            'length': len(sequence),
            'bytes': len(sequence.encode('utf-8'))
        }
        self.sequences.append(entry)
        self.sequence_counts[sequence] += 1
        self.total_sequences += 1
        self.total_bytes += entry['bytes']
        
        # 保持最近的历史记录
        if len(self.sequences) > self.max_history:
            removed = self.sequences.pop(0)
            self.sequence_counts[removed['sequence']] -= 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取序列统计信息
        
        Returns:
            统计信息字典
        """
        if not self.sequences:
            return {}
            
        unique_sequences = len([k for k, v in self.sequence_counts.items() if v > 0])
        avg_length = self.total_bytes / self.total_sequences if self.total_sequences > 0 else 0
        
        return {
            'total_sequences': self.total_sequences,
            'unique_sequences': unique_sequences,
            'average_length': avg_length,
            'time_span': self.sequences[-1]['timestamp'] - self.sequences[0]['timestamp'] if self.sequences else 0,
            'sequences_per_second': self.total_sequences / (time.time() - self.start_time) if self.total_sequences > 0 else 0
        }
    
    def print_recent(self, count: int = 10) -> None:
        """打印最近的序列
        
        Args:
            count: 要打印的序列数量
        """
        recent = self.sequences[-count:] if len(self.sequences) > count else self.sequences
        for seq in recent:
            print(f"{seq['timestamp']:.3f}s: {seq['sequence']} -> {seq['parsed_key']}")
    
    def get_top_sequences(self, count: int = 5) -> List[tuple]:
        """获取最常用的序列
        
        Args:
            count: 要返回的序列数量
            
        Returns:
            序列和出现次数的列表
        """
        sorted_sequences = sorted(self.sequence_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_sequences[:count]
    
    def clear(self) -> None:
        """清空所有记录"""
        self.sequences.clear()
        self.sequence_counts.clear()
        self.total_sequences = 0
        self.total_bytes = 0
        self.start_time = time.time()
    
    def export_data(self) -> Dict[str, Any]:
        """导出监控数据
        
        Returns:
            包含所有监控数据的字典
        """
        return {
            'sequences': self.sequences.copy(),
            'sequence_counts': dict(self.sequence_counts),
            'total_sequences': self.total_sequences,
            'total_bytes': self.total_bytes,
            'statistics': self.get_statistics(),
            'start_time': self.start_time
        }
    
    def import_data(self, data: Dict[str, Any]) -> None:
        """导入监控数据
        
        Args:
            data: 要导入的数据
        """
        self.sequences = data.get('sequences', [])
        self.sequence_counts = defaultdict(int, data.get('sequence_counts', {}))
        self.total_sequences = data.get('total_sequences', 0)
        self.total_bytes = data.get('total_bytes', 0)
        self.start_time = data.get('start_time', time.time())