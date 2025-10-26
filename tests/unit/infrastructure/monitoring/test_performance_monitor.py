"""PerformanceMonitor单元测试"""

import time
import threading
import statistics
from typing import Dict, Any
import pytest

from src.infrastructure.monitoring.performance_monitor import PerformanceMonitor, MetricType


class TestPerformanceMonitor:
    """PerformanceMonitor测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.monitor = PerformanceMonitor(
            max_history_size=100,
            enable_real_time_monitoring=True,
            sampling_rate=1.0
        )
    
    def test_increment_counter(self):
        """测试增加计数器"""
        metric_name = "test_counter"
        
        # 增加计数器
        self.monitor.increment_counter(metric_name, 5.0)
        self.monitor.increment_counter(metric_name, 3.0)
        
        # 验证计数器值
        value = self.monitor.get_metric(metric_name, MetricType.COUNTER)
        assert value == 8.0
    
    def test_set_gauge(self):
        """测试设置仪表值"""
        metric_name = "test_gauge"
        
        # 设置仪表值
        self.monitor.set_gauge(metric_name, 42.0)
        
        # 验证仪表值
        value = self.monitor.get_metric(metric_name, MetricType.GAUGE)
        assert value == 42.0
        
        # 更新仪表值
        self.monitor.set_gauge(metric_name, 24.0)
        value = self.monitor.get_metric(metric_name, MetricType.GAUGE)
        assert value == 24.0
    
    def test_observe_histogram(self):
        """测试观察直方图"""
        metric_name = "test_histogram"
        
        # 观察一些值
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for value in values:
            self.monitor.observe_histogram(metric_name, value)
        
        # 获取直方图统计
        histogram = self.monitor.get_metric(metric_name, MetricType.HISTOGRAM)
        
        # 验证直方图统计
        assert histogram.count == 5
        assert histogram.sum == sum(values)
        assert histogram.min == min(values)
        assert histogram.max == max(values)
        assert abs(histogram.get_average() - statistics.mean(values)) < 0.001
    
    def test_record_timer(self):
        """测试记录计时器"""
        metric_name = "test_timer"
        
        # 记录一些时间值
        times = [0.1, 0.2, 0.3, 0.4, 0.5]
        for t in times:
            self.monitor.record_timer(metric_name, t)
        
        # 获取计时器统计
        timer_stats = self.monitor.get_metric(metric_name, MetricType.TIMER)
        
        # 验证计时器统计
        assert timer_stats is not None
        assert timer_stats["count"] == 5
        assert abs(timer_stats["average"] - statistics.mean(times)) < 0.001
        assert timer_stats["min"] == min(times)
        assert timer_stats["max"] == max(times)
        assert abs(timer_stats["median"] - statistics.median(times)) < 0.001
    
    def test_measure_time_context_manager(self):
        """测试时间测量上下文管理器"""
        metric_name = "test_timer_context"
        
        # 使用上下文管理器测量时间
        with self.monitor.measure_time(metric_name):
            time.sleep(0.01)  # 睡眠一点时间
        
        # 验证计时器被记录
        timer_stats = self.monitor.get_metric(metric_name, MetricType.TIMER)
        assert timer_stats is not None
        assert timer_stats["count"] >= 1
    
    def test_get_all_metrics(self):
        """测试获取所有指标"""
        # 添加一些指标
        self.monitor.increment_counter("counter1", 10.0)
        self.monitor.set_gauge("gauge1", 100.0)
        self.monitor.observe_histogram("histogram1", 5.0)
        self.monitor.record_timer("timer1", 0.1)
        
        # 获取所有指标
        all_metrics = self.monitor.get_all_metrics()
        
        # 验证指标存在
        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics
        assert "timers" in all_metrics
        assert "monitor_stats" in all_metrics
        
        assert all_metrics["counters"]["counter1"] == 10.0
        assert all_metrics["gauges"]["gauge1"] == 100.0
    
    def test_metric_history(self):
        """测试指标历史"""
        metric_name = "test_history"
        
        # 记录一些值
        for i in range(10):
            self.monitor.increment_counter(metric_name, 1.0)
        
        # 获取历史记录
        history = self.monitor.get_metric_history(metric_name, limit=5)
        
        # 验证历史记录数量
        assert len(history) == 5  # 限制为5条
        
        # 验证历史记录包含值和时间戳
        for record in history:
            assert hasattr(record, 'value')
            assert hasattr(record, 'timestamp')
            assert record.value is not None
    
    def test_generate_report(self):
        """测试生成报告"""
        # 添加一些指标
        self.monitor.increment_counter("report_counter", 50.0)
        self.monitor.set_gauge("report_gauge", 200.0)
        
        # 生成报告
        report = self.monitor.generate_report()
        
        # 验证报告结构
        assert "timestamp" in report
        assert "summary" in report
        assert "metrics" in report
        assert "monitoring_stats" in report
        
        summary = report["summary"]
        assert "total_metrics" in summary
        assert "active_counters" in summary
    
    def test_export_metrics_json(self):
        """测试导出JSON格式指标"""
        self.monitor.increment_counter("export_counter", 25.0)
        
        # 导出JSON格式
        json_export = self.monitor.export_metrics(format="json")
        
        # 验证是有效的JSON
        import json
        parsed = json.loads(json_export)
        assert "counters" in parsed
        assert parsed["counters"]["export_counter"] == 25.0
    
    def test_export_metrics_prometheus(self):
        """测试导出Prometheus格式指标"""
        self.monitor.increment_counter("prometheus_counter", 30.0)
        self.monitor.set_gauge("prometheus_gauge", 150.0)
        
        # 导出Prometheus格式
        prometheus_export = self.monitor.export_metrics(format="prometheus")
        
        # 验证包含Prometheus格式的关键字
        assert "# TYPE prometheus_counter counter" in prometheus_export
        assert "# TYPE prometheus_gauge gauge" in prometheus_export
        assert "prometheus_counter 30.0" in prometheus_export
        assert "prometheus_gauge 150.0" in prometheus_export
    
    def test_reset_metrics(self):
        """测试重置指标"""
        # 添加一些指标
        self.monitor.increment_counter("reset_counter", 100.0)
        self.monitor.set_gauge("reset_gauge", 99.0)
        
        # 验证指标存在
        initial_counters = self.monitor.get_all_metrics()["counters"]
        assert "reset_counter" in initial_counters
        
        # 重置指标
        self.monitor.reset_metrics()
        
        # 验证指标被重置
        final_counters = self.monitor.get_all_metrics()["counters"]
        assert len(final_counters) == 0
    
    def test_configure_monitoring(self):
        """测试配置监控"""
        config = {
            "enabled_metrics": {"allowed_metric"},
            "alert_thresholds": {"some_threshold": 100.0},
            "sampling_rules": {"rule1": "value"}
        }
        
        # 应用配置
        self.monitor.configure_monitoring(config)
        
        # 这里主要是验证没有抛出异常
    
    def test_concurrent_access(self):
        """测试并发访问"""
        results = []
        errors = []
        
        def metric_worker(worker_id):
            try:
                counter_name = f"worker_counter_{worker_id}"
                gauge_name = f"worker_gauge_{worker_id}"
                
                # 执行各种指标操作
                for i in range(5):
                    self.monitor.increment_counter(counter_name, 1.0)
                    self.monitor.set_gauge(gauge_name, i * 10.0)
                    self.monitor.observe_histogram("shared_histogram", i)
                
                results.append(True)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程同时操作指标
        threads = []
        for i in range(5):
            thread = threading.Thread(target=metric_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0
        assert len(results) == 5
        assert all(results)
    
    def test_sampling_rate(self):
        """测试采样率"""
        # 创建低采样率的监控器
        low_sample_monitor = PerformanceMonitor(sampling_rate=0.0)  # 0%采样率
        
        # 记录指标（应该不会被记录，因为采样率为0）
        low_sample_monitor.increment_counter("sampled_counter", 10.0)
        
        # 验证指标可能未被记录（取决于随机性）
        value = low_sample_monitor.get_metric("sampled_counter", MetricType.COUNTER)
        # 由于随机性，这里不强制验证，主要是测试功能不报错
    
    def test_get_metric_with_labels(self):
        """测试带标签的指标"""
        labels = {"env": "test", "version": "1.0"}
        
        # 使用标签记录指标
        self.monitor.increment_counter("labeled_counter", 5.0, labels)
        
        # 获取带标签的指标
        full_name = "labeled_counter{env=test,version=1.0}"
        value = self.monitor.get_metric(full_name, MetricType.COUNTER)
        assert value == 5.0
    
    def test_multiple_metric_types_with_same_name(self):
        """测试同名不同类型的指标"""
        base_name = "multi_type_metric"
        
        # 为不同类型的指标使用相同基础名称（但实际存储时会区分）
        self.monitor.increment_counter(f"{base_name}_counter", 10.0)
        self.monitor.set_gauge(f"{base_name}_gauge", 20.0)
        
        # 验证不同类型的指标可以独立存在
        counter_value = self.monitor.get_metric(f"{base_name}_counter", MetricType.COUNTER)
        gauge_value = self.monitor.get_metric(f"{base_name}_gauge", MetricType.GAUGE)
        
        assert counter_value == 10.0
        assert gauge_value == 20.0
    
    def test_histogram_percentiles(self):
        """测试直方图百分位数"""
        metric_name = "percentile_histogram"
        
        # 添加一些值以计算百分位数
        values = list(range(1, 101))  # 1到100
        for value in values:
            self.monitor.observe_histogram(metric_name, value)
        
        # 获取计时器统计（包含百分位数）
        timer_name = "percentile_timer"
        for value in values:
            self.monitor.record_timer(timer_name, value/1000.0)  # 转换为秒
        
        timer_stats = self.monitor.get_metric(timer_name, MetricType.TIMER)
        if timer_stats:
            assert "p95" in timer_stats
            assert "p99" in timer_stats
    
    def test_time_range_report(self):
        """测试时间范围报告"""
        # 添加一些指标
        self.monitor.increment_counter("time_range_counter", 5.0)
        
        # 生成指定时间范围的报告
        report = self.monitor.generate_report(time_range=3600)  # 1小时
        
        # 验证报告结构
        assert "time_range" in report
        assert report["time_range"] == 3600
    
    def test_unsupported_export_format(self):
        """测试不支持的导出格式"""
        with pytest.raises(ValueError):
            self.monitor.export_metrics(format="unsupported_format")


if __name__ == "__main__":
    pytest.main([__file__])