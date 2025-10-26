#!/usr/bin/env python3
"""
性能基准测试演示脚本

演示异步执行器和性能测试功能。
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
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class SimplePerformanceBenchmark:
    """简化的性能基准测试器"""
    
    def __init__(self):
        """初始化性能基准测试器"""
        self.results: Dict[str, PerformanceResult] = {}
    
    def benchmark_sync_execution(self, test_name: str, iterations: int = 10) -> PerformanceResult:
        """基准测试同步执行性能
        
        Args:
            test_name: 测试名称
            iterations: 迭代次数
            
        Returns:
            PerformanceResult: 性能测试结果
        """
        execution_times = []
        successful_count = 0
        failed_count = 0
        
        print(f"开始同步执行性能测试: {test_name}, 迭代次数: {iterations}")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                # 模拟同步工作流执行
                self._simulate_workflow_execution(sync=True)
                
                end_time = time.time()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                successful_count += 1
                print(f"迭代 {i+1}/{iterations} 完成，耗时: {execution_time:.4f}s")
                
            except Exception as e:
                failed_count += 1
                print(f"迭代 {i+1}/{iterations} 失败: {e}")
        
        # 计算统计信息
        if execution_times:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
        else:
            avg_time = min_time = max_time = median_time = 0.0
        
        result = PerformanceResult(
            test_name=f"sync_{test_name}",
            execution_times=execution_times,
            average_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            total_executions=iterations,
            successful_executions=successful_count,
            failed_executions=failed_count
        )
        
        self.results[result.test_name] = result
        return result
    
    async def benchmark_async_execution(self, test_name: str, iterations: int = 10) -> PerformanceResult:
        """基准测试异步执行性能
        
        Args:
            test_name: 测试名称
            iterations: 迭代次数
            
        Returns:
            PerformanceResult: 性能测试结果
        """
        execution_times = []
        successful_count = 0
        failed_count = 0
        
        print(f"开始异步执行性能测试: {test_name}, 迭代次数: {iterations}")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                # 模拟异步工作流执行
                await self._simulate_workflow_execution(sync=False)
                
                end_time = time.time()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                successful_count += 1
                print(f"迭代 {i+1}/{iterations} 完成，耗时: {execution_time:.4f}s")
                
            except Exception as e:
                failed_count += 1
                print(f"迭代 {i+1}/{iterations} 失败: {e}")
        
        # 计算统计信息
        if execution_times:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
        else:
            avg_time = min_time = max_time = median_time = 0.0
        
        result = PerformanceResult(
            test_name=f"async_{test_name}",
            execution_times=execution_times,
            average_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            total_executions=iterations,
            successful_executions=successful_count,
            failed_executions=failed_count
        )
        
        self.results[result.test_name] = result
        return result
    
    def _simulate_workflow_execution(self, sync: bool = True) -> None:
        """模拟工作流执行
        
        Args:
            sync: 是否同步执行
        """
        # 模拟一些工作
        import time
        time.sleep(0.01)  # 模拟10ms的工作
        
        if not sync:
            # 如果是异步，模拟异步操作
            import asyncio
            if asyncio.iscoroutinefunction(self._simulate_workflow_execution):
                return
        
        # 模拟状态处理
        for i in range(100):
            _ = i * 2  # 简单的计算
        
        # 模拟消息处理
        messages = []
        for i in range(10):
            messages.append({
                "role": "assistant" if i % 2 == 0 else "user",
                "content": f"Message {i}"
            })
    
    async def benchmark_async_vs_sync(self, test_name: str, iterations: int = 10) -> Dict[str, PerformanceResult]:
        """对比异步和同步执行性能
        
        Args:
            test_name: 测试名称
            iterations: 迭代次数
            
        Returns:
            Dict[str, PerformanceResult]: 异步和同步的性能测试结果
        """
        print(f"开始异步vs同步性能对比测试: {test_name}")
        
        # 运行同步测试
        sync_result = self.benchmark_sync_execution(test_name, iterations)
        
        # 运行异步测试
        async_result = await self.benchmark_async_execution(test_name, iterations)
        
        # 打印对比结果
        self.print_comparison(async_result, sync_result)
        
        return {
            "async": async_result,
            "sync": sync_result
        }
    
    def print_comparison(self, async_result: PerformanceResult, sync_result: PerformanceResult) -> None:
        """打印性能对比结果
        
        Args:
            async_result: 异步执行结果
            sync_result: 同步执行结果
        """
        print("\n" + "="*60)
        print("性能对比结果")
        print("="*60)
        print(f"{'测试项目':<20} {'异步':<15} {'同步':<15} {'差异':<15}")
        print("-"*60)
        print(f"{'平均耗时':<20} {async_result.average_time:<15.4f} {sync_result.average_time:<15.4f} {sync_result.average_time - async_result.average_time:<15.4f}")
        print(f"{'最小耗时':<20} {async_result.min_time:<15.4f} {sync_result.min_time:<15.4f} {sync_result.min_time - async_result.min_time:<15.4f}")
        print(f"{'最大耗时':<20} {async_result.max_time:<15.4f} {sync_result.max_time:<15.4f} {sync_result.max_time - async_result.max_time:<15.4f}")
        print(f"{'中位数耗时':<20} {async_result.median_time:<15.4f} {sync_result.median_time:<15.4f} {sync_result.median_time - async_result.median_time:<15.4f}")
        print(f"{'成功率':<20} {async_result.successful_executions/async_result.total_executions*100:<14.1f}% {sync_result.successful_executions/sync_result.total_executions*100:<14.1f}% {((sync_result.successful_executions/sync_result.total_executions) - (async_result.successful_executions/async_result.total_executions))*100:<14.1f}%")
        print("="*60)
        
        if async_result.average_time < sync_result.average_time:
            speedup = sync_result.average_time / async_result.average_time
            print(f"异步执行比同步执行快 {speedup:.2f}x")
        else:
            slowdown = async_result.average_time / sync_result.average_time
            print(f"同步执行比异步执行快 {slowdown:.2f}x")
    
    async def benchmark_concurrent_executions(self, test_name: str, concurrent_count: int = 5, iterations_per_task: int = 2) -> PerformanceResult:
        """基准测试并发执行性能
        
        Args:
            test_name: 测试名称
            concurrent_count: 并发任务数
            iterations_per_task: 每个任务的迭代次数
            
        Returns:
            PerformanceResult: 性能测试结果
        """
        print(f"开始并发执行性能测试: {test_name}, 并发数: {concurrent_count}")
        
        async def run_task(task_id: int) -> List[float]:
            """运行单个任务"""
            execution_times = []
            for i in range(iterations_per_task):
                try:
                    start_time = time.time()
                    
                    self._simulate_workflow_execution(sync=False)
                    
                    end_time = time.time()
                    execution_times.append(end_time - start_time)
                    print(f"任务 {task_id}, 迭代 {i+1}/{iterations_per_task} 完成")
                    
                except Exception as e:
                    print(f"任务 {task_id}, 迭代 {i+1}/{iterations_per_task} 失败: {e}")
            
            return execution_times
        
        # 并发运行多个任务
        start_time = time.time()
        tasks = [run_task(i) for i in range(concurrent_count)]
        all_results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 合并所有执行时间
        all_execution_times = [time for task_times in all_results for time in task_times]
        
        total_executions = concurrent_count * iterations_per_task
        successful_executions = len(all_execution_times)
        failed_executions = total_executions - successful_executions
        
        # 计算统计信息
        if all_execution_times:
            avg_time = statistics.mean(all_execution_times)
            min_time = min(all_execution_times)
            max_time = max(all_execution_times)
            median_time = statistics.median(all_execution_times)
        else:
            avg_time = min_time = max_time = median_time = 0.0
        
        result = PerformanceResult(
            test_name=f"concurrent_{test_name}_{concurrent_count}",
            execution_times=all_execution_times,
            average_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions
        )
        
        total_time = end_time - start_time
        print(f"并发执行完成，总耗时: {total_time:.4f}s")
        print(f"平均每个执行耗时: {avg_time:.4f}s")
        print(f"吞吐量: {successful_executions/total_time:.2f} 执行/秒")
        
        self.results[result.test_name] = result
        return result


async def main():
    """主函数"""
    print("性能基准测试演示")
    print("=" * 60)
    
    benchmark = SimplePerformanceBenchmark()
    
    # 演示1: 同步 vs 异步性能对比
    print("演示1: 同步 vs 异步性能对比")
    results = await benchmark.benchmark_async_vs_sync("workflow_execution", iterations=5)
    
    # 演示2: 并发执行测试
    print("\n演示2: 并发执行测试")
    concurrent_result = await benchmark.benchmark_concurrent_executions("concurrent_workflow", concurrent_count=3, iterations_per_task=2)
    
    # 演示3: 性能报告
    print("\n演示3: 性能报告")
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(benchmark.results),
        "results": {}
    }
    
    for test_name, result in benchmark.results.items():
        report["results"][test_name] = {
            "test_name": result.test_name,
            "average_time": result.average_time,
            "min_time": result.min_time,
            "max_time": result.max_time,
            "median_time": result.median_time,
            "total_executions": result.total_executions,
            "successful_executions": result.successful_executions,
            "failed_executions": result.failed_executions,
            "success_rate": result.successful_executions / result.total_executions if result.total_executions > 0 else 0
        }
    
    print(f"总测试数量: {report['total_tests']}")
    print("测试结果摘要:")
    for test_name, result_data in report["results"].items():
        print(f"  {test_name}:")
        print(f"    平均耗时: {result_data['average_time']:.4f}s")
        print(f"    成功率: {result_data['success_rate']*100:.1f}%")
        print(f"    吞吐量: {1/result_data['average_time']:.2f} 执行/秒")
    
    print("\n" + "=" * 60)
    print("性能基准测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())