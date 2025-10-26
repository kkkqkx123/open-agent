#!/usr/bin/env python3
"""
简化的性能基准测试演示脚本
"""

import asyncio
import time
import statistics
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceResult:
    """性能测试结果"""
    test_name: str
    execution_times: List[float]
    average_time: float
    min_time: float
    max_time: float
    median_time: float
    total_executions: int
    successful_executions: int
    failed_executions: int
    timestamp: str = None # type: ignore
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


def simulate_sync_work() -> None:
    """模拟同步工作"""
    time.sleep(0.01)  # 10ms同步延迟
    # 模拟一些CPU工作
    for i in range(1000):
        _ = i * 2


async def simulate_async_work() -> None:
    """模拟异步工作"""
    await asyncio.sleep(0.01)  # 10ms异步延迟
    # 模拟一些CPU工作
    for i in range(1000):
        _ = i * 2


def benchmark_sync(iterations: int = 5) -> PerformanceResult:
    """基准测试同步执行"""
    execution_times = []
    successful = 0
    failed = 0
    
    print(f"开始同步执行测试，迭代次数: {iterations}")
    
    for i in range(iterations):
        try:
            start_time = time.time()
            simulate_sync_work()
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            successful += 1
            print(f"  迭代 {i+1}: {execution_time:.4f}s")
            
        except Exception as e:
            failed += 1
            print(f"  迭代 {i+1} 失败: {e}")
    
    if execution_times:
        return PerformanceResult(
            test_name="sync_execution",
            execution_times=execution_times,
            average_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            median_time=statistics.median(execution_times),
            total_executions=iterations,
            successful_executions=successful,
            failed_executions=failed
        )
    else:
        return PerformanceResult(
            test_name="sync_execution",
            execution_times=[],
            average_time=0.0,
            min_time=0.0,
            max_time=0.0,
            median_time=0.0,
            total_executions=iterations,
            successful_executions=0,
            failed_executions=failed
        )


async def benchmark_async(iterations: int = 5) -> PerformanceResult:
    """基准测试异步执行"""
    execution_times = []
    successful = 0
    failed = 0
    
    print(f"开始异步执行测试，迭代次数: {iterations}")
    
    for i in range(iterations):
        try:
            start_time = time.time()
            await simulate_async_work()
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            successful += 1
            print(f"  迭代 {i+1}: {execution_time:.4f}s")
            
        except Exception as e:
            failed += 1
            print(f"  迭代 {i+1} 失败: {e}")
    
    if execution_times:
        return PerformanceResult(
            test_name="async_execution",
            execution_times=execution_times,
            average_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            median_time=statistics.median(execution_times),
            total_executions=iterations,
            successful_executions=successful,
            failed_executions=failed
        )
    else:
        return PerformanceResult(
            test_name="async_execution",
            execution_times=[],
            average_time=0.0,
            min_time=0.0,
            max_time=0.0,
            median_time=0.0,
            total_executions=iterations,
            successful_executions=0,
            failed_executions=failed
        )


async def benchmark_concurrent(task_count: int = 3, iterations_per_task: int = 2) -> PerformanceResult:
    """基准测试并发执行"""
    execution_times = []
    
    print(f"开始并发执行测试，任务数: {task_count}, 每个任务迭代: {iterations_per_task}")
    
    async def worker_task(task_id: int) -> List[float]:
        """工作协程"""
        task_times = []
        for i in range(iterations_per_task):
            start_time = time.time()
            await simulate_async_work()
            end_time = time.time()
            execution_time = end_time - start_time
            task_times.append(execution_time)
            print(f"  任务 {task_id}, 迭代 {i+1}: {execution_time:.4f}s")
        return task_times
    
    # 并发执行所有任务
    start_time = time.time()
    all_task_results = await asyncio.gather(*[worker_task(i) for i in range(task_count)])
    end_time = time.time()
    
    # 合并所有执行时间
    for task_times in all_task_results:
        execution_times.extend(task_times)
    
    total_executions = task_count * iterations_per_task
    successful_executions = len(execution_times)
    
    if execution_times:
        return PerformanceResult(
            test_name="concurrent_execution",
            execution_times=execution_times,
            average_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            median_time=statistics.median(execution_times),
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=total_executions - successful_executions
        )
    else:
        return PerformanceResult(
            test_name="concurrent_execution",
            execution_times=[],
            average_time=0.0,
            min_time=0.0,
            max_time=0.0,
            median_time=0.0,
            total_executions=total_executions,
            successful_executions=0,
            failed_executions=total_executions
        )


def print_comparison(sync_result: PerformanceResult, async_result: PerformanceResult) -> None:
    """打印性能对比结果"""
    print("\n" + "="*60)
    print("性能对比结果")
    print("="*60)
    print(f"{'测试项目':<20} {'同步':<15} {'异步':<15} {'差异':<15}")
    print("-"*60)
    print(f"{'平均耗时':<20} {sync_result.average_time:<15.4f} {async_result.average_time:<15.4f} {async_result.average_time - sync_result.average_time:<15.4f}")
    print(f"{'最小耗时':<20} {sync_result.min_time:<15.4f} {async_result.min_time:<15.4f} {async_result.min_time - sync_result.min_time:<15.4f}")
    print(f"{'最大耗时':<20} {sync_result.max_time:<15.4f} {async_result.max_time:<15.4f} {async_result.max_time - sync_result.max_time:<15.4f}")
    print(f"{'中位数耗时':<20} {sync_result.median_time:<15.4f} {async_result.median_time:<15.4f} {async_result.median_time - sync_result.median_time:<15.4f}")
    print(f"{'成功率':<20} {sync_result.successful_executions/sync_result.total_executions*100:<14.1f}% {async_result.successful_executions/async_result.total_executions*100:<14.1f}% {((async_result.successful_executions/async_result.total_executions) - (sync_result.successful_executions/sync_result.total_executions))*100:<14.1f}%")
    print("="*60)
    
    if async_result.average_time > 0 and sync_result.average_time > 0:
        if async_result.average_time < sync_result.average_time:
            speedup = sync_result.average_time / async_result.average_time
            print(f"异步执行比同步执行快 {speedup:.2f}x")
        else:
            slowdown = async_result.average_time / sync_result.average_time
            print(f"同步执行比异步执行快 {slowdown:.2f}x")
    else:
        print("某些测试失败，无法计算性能对比")


async def main():
    """主函数"""
    print("性能基准测试演示")
    print("=" * 60)
    
    # 演示1: 同步 vs 异步性能对比
    print("演示1: 同步 vs 异步性能对比")
    sync_result = benchmark_sync(iterations=5)
    async_result = await benchmark_async(iterations=5)
    print_comparison(sync_result, async_result)
    
    # 演示2: 并发执行测试
    print("\n演示2: 并发执行测试")
    concurrent_result = await benchmark_concurrent(task_count=3, iterations_per_task=2)
    
    # 演示3: 性能总结
    print("\n演示3: 性能总结")
    print(f"同步执行平均耗时: {sync_result.average_time:.4f}s")
    print(f"异步执行平均耗时: {async_result.average_time:.4f}s")
    print(f"并发执行平均耗时: {concurrent_result.average_time:.4f}s")
    print(f"并发执行吞吐量: {concurrent_result.total_executions / concurrent_result.average_time:.2f} 执行/秒")
    
    print("\n" + "=" * 60)
    print("性能基准测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())