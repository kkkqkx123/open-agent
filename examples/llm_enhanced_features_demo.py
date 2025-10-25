"""LLM模块增强功能演示"""

import logging
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入增强的LLM组件
from src.infrastructure.llm.config_manager import LLMConfigManager, get_global_config_manager
from src.infrastructure.llm.hooks import (
    SmartRetryHook,
    StructuredLoggingHook,
    MetricsHook,
    CompositeHook
)
from src.infrastructure.llm.error_handler import (
    ErrorContext,
    get_global_error_stats_manager
)
from src.infrastructure.llm.factory import get_global_factory


def demo_enhanced_config_management():
    """演示增强的配置管理"""
    print("=== 配置管理演示 ===")
    
    # 创建配置管理器
    config_manager = LLMConfigManager(
        config_dir=Path("configs/llms"),
        enable_hot_reload=True,
        validation_enabled=True
    )
    
    # 获取配置状态
    status = config_manager.get_config_status()
    print(f"配置状态: {status}")
    
    # 列出可用模型
    available_models = config_manager.list_available_models()
    print(f"可用模型: {available_models}")
    
    # 获取特定模型配置
    if available_models:
        model_type, model_name = available_models[0].split(":")
        client_config = config_manager.get_client_config(model_type, model_name)
        if client_config:
            print(f"模型配置: {client_config.model_name} - {client_config.model_type}")
    
    return config_manager


def demo_enhanced_error_handling():
    """演示增强的错误处理"""
    print("\n=== 错误处理演示 ===")
    
    # 创建错误上下文
    error_context = ErrorContext(
        model_name="gpt-4",
        model_type="openai",
        request_id="demo-123"
    )
    
    # 设置请求上下文
    error_context.set_request_context(
        parameters={"temperature": 0.7, "max_tokens": 100},
        messages=["Hello", "How are you?"]
    )
    
    # 添加错误到错误链
    try:
        raise Exception("模拟网络错误")
    except Exception as e:
        error_context.add_error_to_chain(e, "网络请求阶段")
    
    # 添加重试和降级信息
    error_context.add_retry_attempt(2)
    error_context.add_fallback_attempt("gpt-3.5-turbo")
    
    # 设置性能指标
    error_context.set_performance_metrics(
        response_time=5.2,
        token_usage={"prompt_tokens": 20, "completion_tokens": 30}
    )
    
    # 获取错误摘要
    summary = error_context.get_error_summary()
    print(f"错误摘要: {summary}")
    
    # 记录到全局错误统计
    error_stats_manager = get_global_error_stats_manager()
    error_stats_manager.record_error(error_context)
    
    # 获取错误统计
    stats = error_stats_manager.get_statistics()
    print(f"错误统计: 总错误数={stats.total_errors}, 重试成功率={stats.get_retry_success_rate():.1%}")


def demo_enhanced_hooks():
    """演示增强的钩子功能"""
    print("\n=== 钩子功能演示 ===")
    
    # 创建智能重试钩子
    retry_hook = SmartRetryHook(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=True
    )
    
    # 创建结构化日志钩子
    logging_hook = StructuredLoggingHook(
        logger_name="llm.demo",
        include_sensitive_data=False
    )
    
    # 创建增强指标钩子
    metrics_hook = MetricsHook(
        enable_performance_tracking=True,
        enable_detailed_metrics=True,
        max_history_size=100
    )
    
    # 创建组合钩子
    composite_hook = CompositeHook([
        retry_hook,
        logging_hook,
        metrics_hook
    ])
    
    print("钩子配置完成:")
    print(f"- 智能重试: 最大重试{retry_hook.max_retries}次")
    print(f"- 结构化日志: {logging_hook.logger.name}")
    print(f"- 性能追踪: {metrics_hook.enable_performance_tracking}")
    
    return composite_hook


def demo_performance_monitoring():
    """演示性能监控"""
    print("\n=== 性能监控演示 ===")
    
    # 导入必要的模块
    from src.infrastructure.llm.models import LLMResponse, TokenUsage
    from datetime import datetime
    from langchain_core.messages import AIMessage
    
    # 创建指标钩子
    metrics_hook = MetricsHook(
        enable_performance_tracking=True,
        enable_detailed_metrics=True
    )
    
    # 模拟一些调用数据
    for i in range(5):
        # 模拟调用前记录
        metrics_hook.before_call(
            messages=[f"Message {i}"],
            parameters={"temperature": 0.7}
        )
        
        # 模拟成功调用
        mock_response = LLMResponse(
            content=f"模拟响应 {i}",
            message=AIMessage(content=f"模拟响应 {i}"),
            token_usage=TokenUsage(
                prompt_tokens=50 + i * 5,
                completion_tokens=50 + i * 5,
                total_tokens=100 + i * 10
            ),
            model='gpt-4',
            response_time=1.5 + i * 0.2,
            timestamp=datetime.now()
        )
        
        metrics_hook.after_call(
            response=mock_response,
            messages=[f"Message {i}"],
            parameters={"temperature": 0.7}
        )
    
    # 获取指标
    metrics = metrics_hook.get_metrics()
    print(f"性能指标:")
    print(f"- 总调用数: {metrics['total_calls']}")
    print(f"- 成功率: {metrics['success_rate']:.1%}")
    print(f"- 平均响应时间: {metrics['average_response_time']:.2f}s")
    print(f"- 平均Token数: {metrics['average_tokens_per_call']:.0f}")
    
    # 获取健康状态
    health = metrics_hook.get_health_status()
    print(f"- 健康状态: {health['status']}")
    if health['recommendations']:
        print(f"- 建议: {', '.join(health['recommendations'])}")


def demo_config_validation():
    """演示配置验证"""
    print("\n=== 配置验证演示 ===")
    
    from src.infrastructure.llm.config_manager import ConfigValidator, ConfigValidationRule
    
    # 创建验证器
    validator = ConfigValidator()
    
    # 添加自定义验证规则
    validator.add_rule(ConfigValidationRule(
        field_path="custom_field",
        required=False,
        field_type=str,
        custom_validator=lambda x: len(x) >= 3,
        error_message="custom_field长度必须至少3个字符"
    ))
    
    # 测试有效配置
    valid_config = {
        "model_type": "openai",
        "model_name": "gpt-4",
        "temperature": 0.7,
        "timeout": 30,
        "custom_field": "valid"
    }
    
    errors = validator.validate_config(valid_config)
    print(f"有效配置验证结果: {'通过' if not errors else f'失败 - {errors}'}")
    
    # 测试无效配置
    invalid_config = {
        "model_type": "invalid_type",
        "temperature": 3.0,  # 超出范围
        "timeout": -1,      # 负数
        "custom_field": "ab"  # 长度不足
    }
    
    errors = validator.validate_config(invalid_config)
    print(f"无效配置验证结果: 发现 {len(errors)} 个错误")
    for error in errors[:3]:  # 只显示前3个错误
        print(f"  - {error}")


def main():
    """主演示函数"""
    print("LLM模块增强功能演示")
    print("=" * 50)
    
    try:
        # 配置管理演示
        config_manager = demo_enhanced_config_management()
        
        # 错误处理演示
        demo_enhanced_error_handling()
        
        # 钩子功能演示
        composite_hook = demo_enhanced_hooks()
        
        # 性能监控演示
        demo_performance_monitoring()
        
        # 配置验证演示
        demo_config_validation()
        
        print("\n=== 演示完成 ===")
        print("所有增强功能已成功演示！")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()