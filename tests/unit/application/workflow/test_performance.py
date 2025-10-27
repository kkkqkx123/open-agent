"""工作流性能基准测试模块测试

测试工作流性能基准测试功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, AsyncMock, mock_open
import asyncio
import time
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.application.workflow.performance import (
    PerformanceResult, PerformanceBenchmark, run_performance_test
)
from src.infrastructure.graph.states import WorkflowState


class TestPerformanceResult(unittest.TestCase):
    """测试性能测试结果"""
    
    def test_init_with_timestamp(self):
        """测试初始化（带时间戳）"""
        timestamp = "2023-01-01T12:00:00"
        result = PerformanceResult(
            test_name="test",
            execution_times=[1.0, 2.0, 3.0],
            average_time=2.0,
            min_time=1.0,
            max_time=3.0,
            median_time=2.0,
            total_executions=3,
            successful_executions=3,
            failed_executions=0,
            timestamp=timestamp
        )
        
        self.assertEqual(result.test_name, "test")
        self.assertEqual(result.execution_times, [1.0, 2.0, 3.0])
        self.assertEqual(result.average_time, 2.0)
        self.assertEqual(result.min_time, 1.0)
        self.assertEqual(result.max_time, 3.0)
        self.assertEqual(result.median_time, 2.0)
        self.assertEqual(result.total_executions, 3)
        self.assertEqual(result.successful_executions, 3)
        self.assertEqual(result.failed_executions, 0)
        self.assertEqual(result.timestamp, timestamp)
    
    def test_init_without_timestamp(self):
        """测试初始化（不带时间戳）"""
        with patch('src.application.workflow.performance.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            mock_datetime.now.isoformat.return_value = "2023-01-01T12:00:00"
            
            result = PerformanceResult(
                test_name="test",
                execution_times=[1.0, 2.0, 3.0],
                average_time=2.0,
                min_time=1.0,
                max_time=3.0,
                median_time=2.0,
                total_executions=3,
                successful_executions=3,
                failed_executions=0
            )
            
            self.assertEqual(result.timestamp, "2023-01-01T12:00:00")


class TestPerformanceBenchmark(unittest.TestCase):
    """测试性能基准测试器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_workflow_manager = Mock()
        self.benchmark = PerformanceBenchmark(self.mock_workflow_manager)
        
        # 创建模拟的工作流状态
        self.mock_workflow_state = Mock(spec=WorkflowState)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.benchmark.workflow_manager, self.mock_workflow_manager)
        self.assertEqual(len(self.benchmark.results), 0)
    
    @patch('src.application.workflow.performance.time')
    @patch('src.application.workflow.performance.print')
    def test_benchmark_async_execution_success(self, mock_print, mock_time):
        """测试异步执行性能基准测试（成功）"""
        # 设置时间模拟
        start_time = 1000.0
        end_time = 1002.5
        mock_time.time.side_effect = [start_time, end_time, start_time + 1, end_time + 1]
        
        # 设置工作流管理器模拟
        self.mock_workflow_manager.run_workflow_async = AsyncMock(return_value=self.mock_workflow_state)
        
        # 执行基准测试
        async def run_test():
            return await self.benchmark.benchmark_async_execution(
                "test_workflow",
                iterations=2
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result.test_name, "async_execution_test_workflow")
        self.assertEqual(len(result.execution_times), 2)
        self.assertEqual(result.execution_times[0], 2.5)
        self.assertEqual(result.execution_times[1], 2.5)
        self.assertEqual(result.total_executions, 2)
        self.assertEqual(result.successful_executions, 2)
        self.assertEqual(result.failed_executions, 0)
        
        # 验证调用
        self.assertEqual(self.mock_workflow_manager.run_workflow_async.call_count, 2)
        
        # 验证打印
        mock_print.assert_any_call("开始异步执行性能测试: test_workflow, 迭代次数: 2")
        mock_print.assert_any_call("迭代 1/2 完成，耗时: 2.5000s")
        mock_print.assert_any_call("迭代 2/2 完成，耗时: 2.5000s")
        
        # 验证结果存储
        self.assertIn(result.test_name, self.benchmark.results)
    
    @patch('src.application.workflow.performance.time')
    @patch('src.application.workflow.performance.print')
    def test_benchmark_async_execution_failure(self, mock_print, mock_time):
        """测试异步执行性能基准测试（失败）"""
        # 设置时间模拟
        mock_time.time.return_value = 1000.0
        
        # 设置工作流管理器模拟（抛出异常）
        test_error = Exception("Test error")
        self.mock_workflow_manager.run_workflow_async = AsyncMock(side_effect=test_error)
        
        # 执行基准测试
        async def run_test():
            return await self.benchmark.benchmark_async_execution(
                "test_workflow",
                iterations=2
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result.test_name, "async_execution_test_workflow")
        self.assertEqual(len(result.execution_times), 0)
        self.assertEqual(result.total_executions, 2)
        self.assertEqual(result.successful_executions, 0)
        self.assertEqual(result.failed_executions, 2)
        
        # 验证调用
        self.assertEqual(self.mock_workflow_manager.run_workflow_async.call_count, 2)
        
        # 验证错误打印
        mock_print.assert_any_call("迭代 1/2 失败: Test error")
        mock_print.assert_any_call("迭代 2/2 失败: Test error")
    
    @patch('src.application.workflow.performance.time')
    @patch('src.application.workflow.performance.print')
    def test_benchmark_sync_execution_success(self, mock_print, mock_time):
        """测试同步执行性能基准测试（成功）"""
        # 设置时间模拟
        start_time = 1000.0
        end_time = 1001.5
        mock_time.time.side_effect = [start_time, end_time, start_time + 1, end_time + 1]
        
        # 设置工作流管理器模拟
        self.mock_workflow_manager.run_workflow.return_value = self.mock_workflow_state
        
        # 执行基准测试
        result = self.benchmark.benchmark_sync_execution(
            "test_workflow",
            iterations=2
        )
        
        # 验证结果
        self.assertEqual(result.test_name, "sync_execution_test_workflow")
        self.assertEqual(len(result.execution_times), 2)
        self.assertEqual(result.execution_times[0], 1.5)
        self.assertEqual(result.execution_times[1], 1.5)
        self.assertEqual(result.total_executions, 2)
        self.assertEqual(result.successful_executions, 2)
        self.assertEqual(result.failed_executions, 0)
        
        # 验证调用
        self.assertEqual(self.mock_workflow_manager.run_workflow.call_count, 2)
        
        # 验证打印
        mock_print.assert_any_call("开始同步执行性能测试: test_workflow, 迭代次数: 2")
        mock_print.assert_any_call("迭代 1/2 完成，耗时: 1.5000s")
        mock_print.assert_any_call("迭代 2/2 完成，耗时: 1.5000s")
    
    @patch('src.application.workflow.performance.time')
    @patch('src.application.workflow.performance.print')
    def test_benchmark_sync_execution_failure(self, mock_print, mock_time):
        """测试同步执行性能基准测试（失败）"""
        # 设置时间模拟
        mock_time.time.return_value = 1000.0
        
        # 设置工作流管理器模拟（抛出异常）
        test_error = Exception("Test error")
        self.mock_workflow_manager.run_workflow.side_effect = test_error
        
        # 执行基准测试
        result = self.benchmark.benchmark_sync_execution(
            "test_workflow",
            iterations=2
        )
        
        # 验证结果
        self.assertEqual(result.test_name, "sync_execution_test_workflow")
        self.assertEqual(len(result.execution_times), 0)
        self.assertEqual(result.total_executions, 2)
        self.assertEqual(result.successful_executions, 0)
        self.assertEqual(result.failed_executions, 2)
        
        # 验证调用
        self.assertEqual(self.mock_workflow_manager.run_workflow.call_count, 2)
        
        # 验证错误打印
        mock_print.assert_any_call("迭代 1/2 失败: Test error")
        mock_print.assert_any_call("迭代 2/2 失败: Test error")
    
    @patch.object(PerformanceBenchmark, 'benchmark_async_execution')
    @patch.object(PerformanceBenchmark, 'benchmark_sync_execution')
    @patch.object(PerformanceBenchmark, 'print_comparison')
    def test_benchmark_async_vs_sync(self, mock_print_comparison, mock_sync_benchmark, mock_async_benchmark):
        """测试异步vs同步性能对比"""
        # 设置模拟结果
        async_result = PerformanceResult(
            test_name="async_test",
            execution_times=[1.0, 2.0],
            average_time=1.5,
            min_time=1.0,
            max_time=2.0,
            median_time=1.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        
        sync_result = PerformanceResult(
            test_name="sync_test",
            execution_times=[2.0, 3.0],
            average_time=2.5,
            min_time=2.0,
            max_time=3.0,
            median_time=2.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        
        mock_async_benchmark.return_value = async_result
        mock_sync_benchmark.return_value = sync_result
        
        # 执行对比测试
        async def run_test():
            return await self.benchmark.benchmark_async_vs_sync(
                "test_workflow",
                iterations=2
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result["async"], async_result)
        self.assertEqual(result["sync"], sync_result)
        
        # 验证调用
        mock_async_benchmark.assert_called_once_with("test_workflow", 2, None)
        mock_sync_benchmark.assert_called_once_with("test_workflow", 2, None)
        mock_print_comparison.assert_called_once_with(async_result, sync_result)
    
    @patch('src.application.workflow.performance.print')
    def test_print_comparison_async_faster(self, mock_print):
        """测试打印性能对比结果（异步更快）"""
        # 创建测试结果
        async_result = PerformanceResult(
            test_name="async_test",
            execution_times=[1.0, 2.0],
            average_time=1.5,
            min_time=1.0,
            max_time=2.0,
            median_time=1.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        
        sync_result = PerformanceResult(
            test_name="sync_test",
            execution_times=[2.0, 3.0],
            average_time=2.5,
            min_time=2.0,
            max_time=3.0,
            median_time=2.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        
        # 打印对比结果
        self.benchmark.print_comparison(async_result, sync_result)
        
        # 验证打印调用
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        
        # 验证表头
        self.assertIn("性能对比结果", print_calls)
        # 找到包含"测试项目"的行
        header_line = ""
        for call in print_calls:
            if "测试项目" in call:
                header_line = call
                break
        self.assertIn("异步", header_line)
        self.assertIn("同步", header_line)
        
        # 验证加速比
        self.assertIn("异步执行比同步执行快 1.67x", print_calls)
    
    @patch('src.application.workflow.performance.print')
    def test_print_comparison_sync_faster(self, mock_print):
        """测试打印性能对比结果（同步更快）"""
        # 创建测试结果（同步更快）
        async_result = PerformanceResult(
            test_name="async_test",
            execution_times=[2.0, 3.0],
            average_time=2.5,
            min_time=2.0,
            max_time=3.0,
            median_time=2.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        
        sync_result = PerformanceResult(
            test_name="sync_test",
            execution_times=[1.0, 2.0],
            average_time=1.5,
            min_time=1.0,
            max_time=2.0,
            median_time=1.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        
        # 打印对比结果
        self.benchmark.print_comparison(async_result, sync_result)
        
        # 验证减速比
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        self.assertIn("同步执行比异步执行快 1.67x", print_calls)
    
    @patch('src.application.workflow.performance.asyncio.gather')
    @patch('src.application.workflow.performance.time')
    @patch('src.application.workflow.performance.print')
    def test_benchmark_concurrent_executions(self, mock_print, mock_time, mock_gather):
        """测试并发执行性能基准测试"""
        # 设置时间模拟
        start_time = 1000.0
        end_time = 1005.0
        mock_time.time.side_effect = [start_time] + [end_time] * 10  # 多次调用返回相同时间
        
        # 设置异步gather模拟
        async def mock_run_task(task_id):
            # 模拟任务执行时间
            await asyncio.sleep(0.001)
            return [1.0, 1.5]  # 每个任务2次执行
        
        mock_gather.return_value = [
            [1.0, 1.5],  # 任务1的执行时间
            [2.0, 2.5],  # 任务2的执行时间
            [1.5, 2.0]   # 任务3的执行时间
        ]
        
        # 设置工作流管理器模拟
        self.mock_workflow_manager.run_workflow_async = AsyncMock(return_value=self.mock_workflow_state)
        
        # 执行并发基准测试
        async def run_test():
            return await self.benchmark.benchmark_concurrent_executions(
                "test_workflow",
                concurrent_count=3,
                iterations_per_task=2
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result.test_name, "concurrent_execution_test_workflow_3")
        self.assertEqual(len(result.execution_times), 6)  # 3个任务 × 2次执行
        self.assertEqual(result.total_executions, 6)
        self.assertEqual(result.successful_executions, 6)
        self.assertEqual(result.failed_executions, 0)
        
        # 验证打印
        mock_print.assert_any_call("开始并发执行性能测试: test_workflow, 并发数: 3")
        mock_print.assert_any_call("并发执行完成，总耗时: 5.0000s")
        mock_print.assert_any_call("平均每个执行耗时: 1.6667s")
        mock_print.assert_any_call("吞吐量: 1.20 执行/秒")
    
    @patch('src.application.workflow.performance.datetime')
    def test_get_report(self, mock_datetime):
        """测试获取完整的性能报告"""
        # 设置时间模拟
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.now.isoformat.return_value = "2023-01-01T12:00:00"
        
        # 添加测试结果
        test_result = PerformanceResult(
            test_name="test",
            execution_times=[1.0, 2.0],
            average_time=1.5,
            min_time=1.0,
            max_time=2.0,
            median_time=1.5,
            total_executions=2,
            successful_executions=2,
            failed_executions=0
        )
        self.benchmark.results["test"] = test_result
        
        # 获取报告
        report = self.benchmark.get_report()
        
        # 验证报告结构
        self.assertIn("timestamp", report)
        self.assertIn("total_tests", report)
        self.assertIn("results", report)
        
        # 验证报告内容
        self.assertEqual(report["timestamp"], "2023-01-01T12:00:00")
        self.assertEqual(report["total_tests"], 1)
        self.assertIn("test", report["results"])
        
        # 验证测试结果
        test_report = report["results"]["test"]
        self.assertEqual(test_report["test_name"], "test")
        self.assertEqual(test_report["average_time"], 1.5)
        self.assertEqual(test_report["min_time"], 1.0)
        self.assertEqual(test_report["max_time"], 2.0)
        self.assertEqual(test_report["median_time"], 1.5)
        self.assertEqual(test_report["total_executions"], 2)
        self.assertEqual(test_report["successful_executions"], 2)
        self.assertEqual(test_report["failed_executions"], 0)
        self.assertEqual(test_report["success_rate"], 1.0)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.application.workflow.performance.print')
    def test_save_report(self, mock_print, mock_open_func):
        """测试保存性能报告到文件"""
        # 设置模拟
        mock_report = {"test": "report"}
        
        with patch('json.dump') as mock_json_dump:
            with patch.object(self.benchmark, 'get_report', return_value=mock_report):
                # 保存报告
                self.benchmark.save_report("test_report.json")
            
            # 验证文件操作
            mock_open_func.assert_called_once_with("test_report.json", 'w', encoding='utf-8')
            mock_json_dump.assert_called_once_with(mock_report, mock_open_func(), indent=2, ensure_ascii=False)
        
        # 验证打印
        mock_print.assert_called_once_with("性能报告已保存到: test_report.json")


class TestRunPerformanceTest(unittest.TestCase):
    """测试便捷的性能测试函数"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_workflow_manager = Mock()
    
    @patch('src.application.workflow.performance.PerformanceBenchmark')
    def test_run_performance_test_async(self, mock_benchmark_class):
        """测试运行异步性能测试"""
        # 设置模拟
        mock_benchmark = Mock()
        mock_benchmark_class.return_value = mock_benchmark
        
        mock_result = Mock()
        mock_benchmark.benchmark_async_execution = AsyncMock(return_value=mock_result)
        
        # 运行测试
        async def run_test():
            return await run_performance_test(
                self.mock_workflow_manager,
                "test_workflow",
                test_type="async",
                iterations=5
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result, {"async": mock_result})
        
        # 验证调用
        mock_benchmark_class.assert_called_once_with(self.mock_workflow_manager)
        mock_benchmark.benchmark_async_execution.assert_called_once_with("test_workflow", 5)
    
    @patch('src.application.workflow.performance.PerformanceBenchmark')
    def test_run_performance_test_sync(self, mock_benchmark_class):
        """测试运行同步性能测试"""
        # 设置模拟
        mock_benchmark = Mock()
        mock_benchmark_class.return_value = mock_benchmark
        
        mock_result = Mock()
        mock_benchmark.benchmark_sync_execution.return_value = mock_result
        
        # 运行测试
        async def run_test():
            return await run_performance_test(
                self.mock_workflow_manager,
                "test_workflow",
                test_type="sync",
                iterations=5
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result, {"sync": mock_result})
        
        # 验证调用
        mock_benchmark_class.assert_called_once_with(self.mock_workflow_manager)
        mock_benchmark.benchmark_sync_execution.assert_called_once_with("test_workflow", 5)
    
    @patch('src.application.workflow.performance.PerformanceBenchmark')
    def test_run_performance_test_both(self, mock_benchmark_class):
        """测试运行异步vs同步性能测试"""
        # 设置模拟
        mock_benchmark = Mock()
        mock_benchmark_class.return_value = mock_benchmark
        
        mock_result = {"async": Mock(), "sync": Mock()}
        mock_benchmark.benchmark_async_vs_sync = AsyncMock(return_value=mock_result)
        
        # 运行测试
        async def run_test():
            return await run_performance_test(
                self.mock_workflow_manager,
                "test_workflow",
                test_type="both",
                iterations=5
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result, mock_result)
        
        # 验证调用
        mock_benchmark_class.assert_called_once_with(self.mock_workflow_manager)
        mock_benchmark.benchmark_async_vs_sync.assert_called_once_with("test_workflow", 5)
    
    @patch('src.application.workflow.performance.PerformanceBenchmark')
    def test_run_performance_test_concurrent(self, mock_benchmark_class):
        """测试运行并发性能测试"""
        # 设置模拟
        mock_benchmark = Mock()
        mock_benchmark_class.return_value = mock_benchmark
        
        mock_result = Mock()
        mock_benchmark.benchmark_concurrent_executions = AsyncMock(return_value=mock_result)
        
        # 运行测试
        async def run_test():
            return await run_performance_test(
                self.mock_workflow_manager,
                "test_workflow",
                test_type="concurrent",
                iterations=10,
                concurrent_count=5
            )
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result, {"concurrent": mock_result})
        
        # 验证调用
        mock_benchmark_class.assert_called_once_with(self.mock_workflow_manager)
        mock_benchmark.benchmark_concurrent_executions.assert_called_once_with(
            "test_workflow", 5, 2  # iterations // concurrent_count
        )
    
    @patch('src.application.workflow.performance.PerformanceBenchmark')
    def test_run_performance_test_invalid_type(self, mock_benchmark_class):
        """测试运行无效类型的性能测试"""
        # 设置模拟
        mock_benchmark = Mock()
        mock_benchmark_class.return_value = mock_benchmark
        
        # 运行测试
        async def run_test():
            await run_performance_test(
                self.mock_workflow_manager,
                "test_workflow",
                test_type="invalid"
            )
        
        with self.assertRaises(ValueError) as context:
            asyncio.run(run_test())
        
        # 验证错误
        self.assertIn("不支持的测试类型", str(context.exception))
        
        # 验证没有调用任何测试方法
        mock_benchmark.benchmark_async_execution.assert_not_called()
        mock_benchmark.benchmark_sync_execution.assert_not_called()
        mock_benchmark.benchmark_async_vs_sync.assert_not_called()
        mock_benchmark.benchmark_concurrent_executions.assert_not_called()


if __name__ == '__main__':
    unittest.main()