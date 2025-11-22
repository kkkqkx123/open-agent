"""
历史管理模块完整使用示例

演示如何在新架构中使用历史管理功能，包括：
1. 服务注册和配置
2. 历史记录钩子集成
3. Token追踪和成本计算
4. 统计分析和报告
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# 导入相关模块
from src.services.container import container
from src.services.history.di_config import register_history_services
from src.services.history.hooks import HistoryRecordingHook
from src.services.history.statistics_service import HistoryStatisticsService
from src.services.history.cost_calculator import CostCalculator
from src.services.history.token_tracker import WorkflowTokenTracker
from src.interfaces.history import IHistoryManager, ICostCalculator
from src.services.llm.token_calculation_service import TokenCalculationService
from src.core.history.entities import TokenSource

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoryManagementExample:
    """历史管理示例类"""
    
    def __init__(self):
        """初始化示例"""
        self.container = container
        self.workflow_id = f"example_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def setup_services(self):
        """设置服务"""
        logger.info("开始设置历史管理服务...")
        
        # 配置
        config = self._get_config()
        
        # 注册服务
        register_history_services(self.container, config)
        
        logger.info("历史管理服务设置完成")
    
    def _get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            "history": {
                "enabled": True,
                "storage": {
                    "type": "memory"  # 使用内存存储进行演示
                },
                "token_calculation": {
                    "default_provider": "openai"
                },
                "pricing": {
                    # OpenAI模型定价
                    "gpt-4": {
                        "input_price": 0.03,
                        "output_price": 0.06,
                        "currency": "USD",
                        "provider": "openai"
                    },
                    "gpt-3.5-turbo": {
                        "input_price": 0.0015,
                        "output_price": 0.002,
                        "currency": "USD",
                        "provider": "openai"
                    },
                    # Gemini模型定价
                    "gemini-pro": {
                        "input_price": 0.0005,
                        "output_price": 0.0015,
                        "currency": "USD",
                        "provider": "google"
                    }
                },
                "token_tracker": {
                    "cache_ttl": 300
                },
                "manager": {
                    "enable_async_batching": True,
                    "batch_size": 5,
                    "batch_timeout": 1.0
                },
                "hook": {
                    "auto_register": True,
                    "workflow_context": {}
                }
            }
        }
    
    async def demonstrate_basic_usage(self):
        """演示基本使用"""
        logger.info("演示基本历史记录功能...")
        
        # 获取服务
        history_manager = self.container.get(IHistoryManager)
        cost_calculator = self.container.get(ICostCalculator)
        
        # 模拟Token使用记录
        from src.core.history.entities import TokenUsageRecord
        
        token_record = TokenUsageRecord(
            record_id="demo_token_001",
            session_id="demo_session",
            workflow_id=self.workflow_id,
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            source=TokenSource.API,
            confidence=1.0,
            metadata={"demo": True}
        )
        
        # 记录Token使用
        await history_manager.record_token_usage(token_record)
        
        # 计算成本
        cost_record = cost_calculator.calculate_cost(token_record)
        await history_manager.record_cost(cost_record)
        
        logger.info(f"记录Token使用: {token_record.total_tokens} tokens")
        logger.info(f"计算成本: ${cost_record.total_cost:.6f}")
    
    async def demonstrate_cost_calculation(self):
        """演示成本计算"""
        logger.info("演示成本计算功能...")
        
        cost_calculator = self.container.get(ICostCalculator)
        
        # 获取模型定价
        pricing = cost_calculator.get_model_pricing("gpt-4")
        logger.info(f"GPT-4定价: {pricing}")
        
        # 估算成本
        estimation = cost_calculator.estimate_cost(
            model="gpt-4",
            estimated_input_tokens=200,
            estimated_output_tokens=100
        )
        logger.info(f"成本估算: {estimation}")
        
        # 更新定价
        cost_calculator.update_pricing(
            model_name="custom-model",
            input_price=0.01,
            output_price=0.02,
            currency="USD",
            provider="custom"
        )
        
        # 列出支持的模型
        models = cost_calculator.list_supported_models()
        logger.info(f"支持的模型数量: {len(models)}")
    
    async def demonstrate_token_tracking(self):
        """演示Token追踪"""
        logger.info("演示Token追踪功能...")
        
        token_tracker = self.container.get(WorkflowTokenTracker)
        
        # 追踪多个Token使用记录
        models_and_tokens = [
            ("gpt-4", "openai", 150, 75),
            ("gpt-3.5-turbo", "openai", 100, 50),
            ("gemini-pro", "google", 80, 40),
            ("gpt-4", "openai", 200, 100),
        ]
        
        for model, provider, prompt_tokens, completion_tokens in models_and_tokens:
            await token_tracker.track_workflow_token_usage(
                workflow_id=self.workflow_id,
                model=model,
                provider=provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                source=TokenSource.API,
                confidence=1.0,
                metadata={"demo": True}
            )
        
        # 获取工作流统计
        stats = await token_tracker.get_workflow_statistics(self.workflow_id)
        logger.info(f"工作流统计: 总Token={stats.total_tokens}, 总成本=${stats.total_cost:.6f}")
        
        # 获取多模型统计
        multi_stats = await token_tracker.get_multi_model_statistics(self.workflow_id)
        for model, model_stats in multi_stats.items():
            logger.info(f"模型 {model}: Token={model_stats.total_tokens}, 成本=${model_stats.total_cost:.6f}")
        
        # 获取使用趋势
        trends = await token_tracker.get_model_usage_trends(self.workflow_id, days=7)
        logger.info(f"使用趋势数据点数量: {len(trends)}")
    
    async def demonstrate_statistics(self):
        """演示统计分析"""
        logger.info("演示统计分析功能...")
        
        stats_service = self.container.get(HistoryStatisticsService)
        
        # 获取工作流汇总
        summary = await stats_service.get_workflow_token_summary(self.workflow_id)
        logger.info(f"工作流汇总: 总Token={summary.total_tokens}, 总成本=${summary.total_cost:.6f}")
        logger.info(f"使用的模型: {summary.models_used}")
        logger.info(f"最常用模型: {summary.most_used_model}")
        
        # 获取成本分析
        cost_analysis = await stats_service.get_cost_analysis(self.workflow_id)
        logger.info(f"成本分析: 总成本=${cost_analysis['total_cost']:.6f}")
        logger.info(f"平均每请求成本: ${cost_analysis['avg_cost_per_request']:.6f}")
        
        # 获取效率指标
        efficiency = await stats_service.get_efficiency_metrics(self.workflow_id)
        logger.info(f"效率指标: 平均每请求Token={efficiency['avg_tokens_per_request']:.1f}")
        
        # 模拟跨工作流对比
        workflow_ids = [self.workflow_id, f"{self.workflow_id}_2", f"{self.workflow_id}_3"]
        
        # 为其他工作流添加一些数据
        for i, wf_id in enumerate(workflow_ids[1:], 1):
            token_tracker = self.container.get(WorkflowTokenTracker)
            await token_tracker.track_workflow_token_usage(
                workflow_id=wf_id,
                model="gpt-3.5-turbo",
                provider="openai",
                prompt_tokens=50 * i,
                completion_tokens=25 * i,
                source=TokenSource.API
            )
        
        # 获取跨工作流对比
        comparison = await stats_service.get_cross_workflow_comparison(
            workflow_ids, metric="total_tokens"
        )
        logger.info(f"跨工作流对比: {comparison['summary']}")
    
    async def demonstrate_history_hook(self):
        """演示历史记录钩子"""
        logger.info("演示历史记录钩子功能...")
        
        # 获取历史记录钩子
        history_hook = self.container.get(HistoryRecordingHook)
        
        # 更新工作流上下文
        history_hook.set_workflow_context({
            "workflow_id": self.workflow_id,
            "workflow_name": "demo_workflow",
            "user_id": "demo_user",
            "environment": "development"
        })
        
        # 模拟LLM调用
        from langchain_core.messages import HumanMessage, AIMessage
        
        messages = [
            HumanMessage(content="你好，请介绍一下Python编程语言"),
            AIMessage(content="Python是一种高级编程语言，具有简洁易读的语法...")
        ]
        
        # 模拟调用前钩子
        history_hook.before_call(
            messages=messages,
            parameters={"temperature": 0.7, "max_tokens": 100},
            model_info={"name": "gpt-4", "type": "openai"},
            session_id="demo_session"
        )
        
        # 模拟调用后钩子
        from src.interfaces.llm import LLMResponse
        
        response = LLMResponse(
            content="Python是一种高级编程语言...",
            model="gpt-4",
            finish_reason="stop",
            metadata={"response_time": 1.5}
        )
        
        history_hook.after_call(
            response=response,
            messages=messages,
            parameters={"temperature": 0.7, "max_tokens": 100},
            model_info={"name": "gpt-4", "type": "openai"},
            session_id="demo_session"
        )
        
        # 检查待处理请求
        pending_count = history_hook.get_pending_request_count()
        logger.info(f"待处理请求数量: {pending_count}")
        
        # 清除待处理请求
        cleared_count = history_hook.clear_pending_requests()
        logger.info(f"清除了 {cleared_count} 个待处理请求")
    
    async def demonstrate_advanced_features(self):
        """演示高级功能"""
        logger.info("演示高级功能...")
        
        history_manager = self.container.get(IHistoryManager)
        
        # 获取存储信息
        storage_info = await history_manager.get_storage_info()
        logger.info(f"存储信息: {storage_info}")
        
        # 获取批处理状态
        batch_status = history_manager.get_batch_status()
        logger.info(f"批处理状态: {batch_status}")
        
        # 强制处理批次
        await history_manager.flush_batch()
        
        # 模拟清理旧记录（干运行）
        cleanup_result = await history_manager.cleanup_old_records(
            older_than=datetime.now() - timedelta(days=30),
            dry_run=True
        )
        logger.info(f"清理预览: {cleanup_result}")
    
    async def run_all_demonstrations(self):
        """运行所有演示"""
        try:
            # 设置服务
            await self.setup_services()
            
            # 基本使用
            await self.demonstrate_basic_usage()
            
            # 成本计算
            await self.demonstrate_cost_calculation()
            
            # Token追踪
            await self.demonstrate_token_tracking()
            
            # 统计分析
            await self.demonstrate_statistics()
            
            # 历史记录钩子
            await self.demonstrate_history_hook()
            
            # 高级功能
            await self.demonstrate_advanced_features()
            
            logger.info("所有演示完成！")
            
        except Exception as e:
            logger.error(f"演示过程中发生错误: {e}")
            raise


async def main():
    """主函数"""
    example = HistoryManagementExample()
    await example.run_all_demonstrations()


if __name__ == "__main__":
    asyncio.run(main())