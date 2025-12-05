"""正则表达式性能优化器"""

import re
import time
from typing import Pattern, Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import threading
from functools import lru_cache


class OptimizationLevel(Enum):
    """优化级别枚举"""
    NONE = "none"          # 不优化
    BASIC = "basic"        # 基础优化
    ADVANCED = "advanced"  # 高级优化
    AGGRESSIVE = "aggressive"  # 激进优化


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    pattern: str
    compilation_time: float
    match_time: float
    substitution_time: float
    memory_usage: int
    match_count: int
    false_positive_rate: float
    accuracy_score: float


class RegexOptimizer:
    """正则表达式优化器"""

    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.BASIC):
        """初始化优化器

        Args:
            optimization_level: 优化级别
        """
        self.optimization_level = optimization_level
        self._pattern_cache: Dict[str, Pattern] = {}
        self._performance_metrics: Dict[str, PerformanceMetrics] = {}
        self._cache_lock = threading.RLock()
        self._compiled_patterns: Dict[str, Pattern] = {}

    def optimize_pattern(self, pattern: str, flags: int = 0) -> str:
        """优化正则表达式模式

        Args:
            pattern: 原始模式
            flags: 正则表达式标志

        Returns:
            优化后的模式
        """
        if self.optimization_level == OptimizationLevel.NONE:
            return pattern

        optimized = pattern

        # 基础优化
        if self.optimization_level in [OptimizationLevel.BASIC, OptimizationLevel.ADVANCED, OptimizationLevel.AGGRESSIVE]:
            optimized = self._basic_optimization(optimized)

        # 高级优化
        if self.optimization_level in [OptimizationLevel.ADVANCED, OptimizationLevel.AGGRESSIVE]:
            optimized = self._advanced_optimization(optimized)

        # 激进优化
        if self.optimization_level == OptimizationLevel.AGGRESSIVE:
            optimized = self._aggressive_optimization(optimized)

        return optimized

    def _basic_optimization(self, pattern: str) -> str:
        """基础优化

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 移除不必要的转义
        optimized = re.sub(r'\\([^\w\s])', r'\1', pattern)
        
        # 优化字符类 - 使用lambda函数避免转义问题
        optimized = re.sub(r'\[a-zA-Z\]', lambda m: '[A-Za-z]', optimized)
        optimized = re.sub(r'\[0-9\]', lambda m: '\\d', optimized)
        optimized = re.sub(r'\[A-Za-z0-9_\]', lambda m: '\\w', optimized)
        
        # 优化量词
        optimized = re.sub(r'\{0,1\}', lambda m: '?', optimized)
        optimized = re.sub(r'\{0,\}', lambda m: '*', optimized)
        optimized = re.sub(r'\{1,\}', lambda m: '+', optimized)
        
        # 合并相邻的字符类
        optimized = re.sub(r'(\[([^\]]+)\])\1', r'\1', optimized)
        
        return optimized

    def _advanced_optimization(self, pattern: str) -> str:
        """高级优化

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 优化分组
        optimized = re.sub(r'\(\?:([^)]+)\)', r'(\1)', pattern)
        
        # 使用原子分组（如果支持）
        if re.compile(r'(?>)').pattern == '(?>)':
            optimized = re.sub(r'\(([^?][^)]*)\)', r'(?>\1)', optimized)
        
        # 优化选择分支
        optimized = self._optimize_alternatives(optimized)
        
        # 预编译常用模式
        optimized = self._precompile_common_patterns(optimized)
        
        return optimized

    def _aggressive_optimization(self, pattern: str) -> str:
        """激进优化

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 使用占有量词（如果支持）
        if re.compile(r'*+').pattern == '*+':
            optimized = re.sub(r'\*([^\+])', r'*+\1', pattern)
            optimized = re.sub(r'\+([^\+])', r'++\1', optimized)
            optimized = re.sub(r'\?([^\+])', r'?+\1', optimized)
        
        # 优化回溯
        optimized = self._optimize_backtracking(pattern)
        
        # 使用更高效的字符类
        optimized = self._optimize_character_classes(pattern)
        
        return optimized

    def _optimize_alternatives(self, pattern: str) -> str:
        """优化选择分支

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 将常见的前缀提取出来
        # 这是一个简化的实现，实际应用中可能需要更复杂的逻辑
        return pattern

    def _precompile_common_patterns(self, pattern: str) -> str:
        """预编译常用模式

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 常用模式的替换映射
        common_patterns = {
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}': r'EMAIL_PATTERN',
            r'1[3-9]\d{9}': r'CHINA_PHONE_PATTERN',
            r'[0-9]{16,19}': r'BANK_CARD_PATTERN',
            r'[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]': r'CHINA_ID_PATTERN',
        }
        
        optimized = pattern
        for common_pattern, placeholder in common_patterns.items():
            if common_pattern in optimized:
                optimized = optimized.replace(common_pattern, placeholder)
        
        return optimized

    def _optimize_backtracking(self, pattern: str) -> str:
        """优化回溯

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 避免灾难性回溯的优化
        # 这是一个简化的实现
        return pattern

    def _optimize_character_classes(self, pattern: str) -> str:
        """优化字符类

        Args:
            pattern: 原始模式

        Returns:
            优化后的模式
        """
        # 使用更高效的字符类表示
        # 这是一个简化的实现
        return pattern

    def compile_pattern(self, pattern: str, flags: int = 0) -> Pattern:
        """编译优化的正则表达式

        Args:
            pattern: 正则表达式模式
            flags: 正则表达式标志

        Returns:
            编译后的正则表达式对象
        """
        cache_key = f"{pattern}_{flags}"
        
        with self._cache_lock:
            if cache_key in self._compiled_patterns:
                return self._compiled_patterns[cache_key]
            
            # 优化模式
            optimized_pattern = self.optimize_pattern(pattern, flags)
            
            # 编译模式
            start_time = time.time()
            compiled = re.compile(optimized_pattern, flags | re.UNICODE)
            compilation_time = time.time() - start_time
            
            # 缓存编译结果
            self._compiled_patterns[cache_key] = compiled
            
            # 记录性能指标
            self._record_performance_metrics(pattern, optimized_pattern, compilation_time)
            
            return compiled

    def _record_performance_metrics(self, original_pattern: str, optimized_pattern: str, compilation_time: float):
        """记录性能指标

        Args:
            original_pattern: 原始模式
            optimized_pattern: 优化后的模式
            compilation_time: 编译时间
        """
        metrics = PerformanceMetrics(
            pattern=original_pattern,
            compilation_time=compilation_time,
            match_time=0.0,
            substitution_time=0.0,
            memory_usage=0,
            match_count=0,
            false_positive_rate=0.0,
            accuracy_score=0.0
        )
        
        self._performance_metrics[original_pattern] = metrics

    def benchmark_pattern(self, pattern: str, test_text: str, iterations: int = 1000) -> PerformanceMetrics:
        """基准测试正则表达式性能

        Args:
            pattern: 正则表达式模式
            test_text: 测试文本
            iterations: 迭代次数

        Returns:
            性能指标
        """
        # 编译原始模式
        original_start = time.time()
        original_compiled = re.compile(pattern, re.UNICODE)
        original_compilation_time = time.time() - original_start
        
        # 编译优化模式
        optimized_start = time.time()
        optimized_compiled = self.compile_pattern(pattern, re.UNICODE)
        optimized_compilation_time = time.time() - optimized_start
        
        # 测试匹配性能
        original_match_start = time.time()
        original_matches = 0
        for _ in range(iterations):
            matches = original_compiled.findall(test_text)
            original_matches += len(matches)
        original_match_time = time.time() - original_match_start
        
        optimized_match_start = time.time()
        optimized_matches = 0
        for _ in range(iterations):
            matches = optimized_compiled.findall(test_text)
            optimized_matches += len(matches)
        optimized_match_time = time.time() - optimized_match_start
        
        # 测试替换性能
        original_sub_start = time.time()
        for _ in range(iterations):
            original_compiled.sub('***', test_text)
        original_sub_time = time.time() - original_sub_start
        
        optimized_sub_start = time.time()
        for _ in range(iterations):
            optimized_compiled.sub('***', test_text)
        optimized_sub_time = time.time() - optimized_sub_start
        
        # 计算准确率
        accuracy = 1.0 if original_matches == optimized_matches else 0.5
        
        return PerformanceMetrics(
            pattern=pattern,
            compilation_time=optimized_compilation_time,
            match_time=optimized_match_time,
            substitution_time=optimized_sub_time,
            memory_usage=0,  # 简化实现
            match_count=optimized_matches,
            false_positive_rate=0.0,  # 需要更复杂的实现
            accuracy_score=accuracy
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告

        Returns:
            性能报告字典
        """
        report = {
            'optimization_level': self.optimization_level.value,
            'cached_patterns': len(self._compiled_patterns),
            'performance_metrics': {}
        }
        
        for pattern, metrics in self._performance_metrics.items():
            report['performance_metrics'][pattern] = {
                'compilation_time': metrics.compilation_time,
                'match_time': metrics.match_time,
                'substitution_time': metrics.substitution_time,
                'match_count': metrics.match_count,
                'accuracy_score': metrics.accuracy_score
            }
        
        return report

    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._compiled_patterns.clear()
            self._performance_metrics.clear()

    def validate_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """验证正则表达式模式

        Args:
            pattern: 正则表达式模式

        Returns:
            (是否有效, 错误信息)
        """
        try:
            re.compile(pattern, re.UNICODE)
            return True, None
        except re.error as e:
            return False, str(e)

    def suggest_improvements(self, pattern: str) -> List[str]:
        """建议模式改进

        Args:
            pattern: 正则表达式模式

        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 检查常见问题
        if '.*' in pattern and pattern.count('.*') > 1:
            suggestions.append("考虑使用更具体的字符类替代 '.*' 以提高性能")
        
        if pattern.count('(') != pattern.count(')'):
            suggestions.append("括号不匹配，请检查模式语法")
        
        if '\\b' in pattern and '[\\u4e00-\\u9fff]' in pattern:
            suggestions.append("在处理中文字符时，\\b 可能不准确，建议使用自定义边界")
        
        if '{' in pattern and '}' in pattern:
            # 检查量词是否可以简化
            if '{0,1}' in pattern:
                suggestions.append("可以使用 '?' 替代 '{0,1}'")
            if '{0,}' in pattern:
                suggestions.append("可以使用 '*' 替代 '{0,}'")
            if '{1,}' in pattern:
                suggestions.append("可以使用 '+' 替代 '{1,}'")
        
        return suggestions


# 全局优化器实例
regex_optimizer = RegexOptimizer()


@lru_cache(maxsize=128)
def cached_compile(pattern: str, flags: int = 0) -> Pattern:
    """缓存编译正则表达式

    Args:
        pattern: 正则表达式模式
        flags: 正则表达式标志

    Returns:
        编译后的正则表达式对象
    """
    return regex_optimizer.compile_pattern(pattern, flags)


def benchmark_redactor_patterns(patterns: List[str], test_texts: List[str]) -> Dict[str, Any]:
    """基准测试脱敏器模式

    Args:
        patterns: 模式列表
        test_texts: 测试文本列表

    Returns:
        基准测试结果
    """
    results = {}
    
    for pattern in patterns:
        pattern_results = []
        
        for test_text in test_texts:
            metrics = regex_optimizer.benchmark_pattern(pattern, test_text)
            pattern_results.append({
                'test_text_length': len(test_text),
                'metrics': metrics
            })
        
        results[pattern] = pattern_results
    
    return results