# 历史管理模块迁移指南

本文档详细说明了如何从旧架构的 `src/infrastructure/history` 迁移到新架构的历史管理系统。

## 迁移概述

### 旧架构 vs 新架构

| 旧架构组件 | 新架构位置 | 状态 |
|-----------|-----------|------|
| `HistoryRecordingHook` | `src/services/history/hooks.py` | ✅ 已迁移 |
| `TokenUsageTracker` | `src/services/history/token_tracker.py` | ✅ 已迁移 |
| `SessionContext` | `src/application/history/__init__.py` | ✅ 已迁移 |
| `FileHistoryStorage` | `src/adapters/storage/adapters/file.py` | ✅ 已迁移 |
| `MemoryHistoryStorage` | `src/adapters/storage/adapters/memory.py` | ✅ 已迁移 |
| `service_registration.py` | `src/services/history/di_config.py` | ✅ 已迁移 |

### 新增功能

1. **核心历史模块** (`src/core/history/`)
   - 统一的实体定义
   - 标准化接口
   - 基础实现类

2. **增强的Token追踪**
   - 基于LLM模块的精确计算
   - 工作流和模型维度统计
   - 缓存优化

3. **成本计算器**
   - 多模型定价支持
   - 动态定价更新
   - 成本分析功能

4. **统计服务**
   - 丰富的查询功能
   - 趋势分析
   - 跨工作流对比

## 迁移步骤

### 1. 更新依赖注入配置

```python
# 在你的应用初始化代码中
from src.services.history.di_config import register_history_services

# 注册历史管理服务
register_history_services(container, config)
```

### 2. 配置历史管理

```yaml
# configs/history.yaml
history:
  enabled: true
  storage:
    type: file  # file, memory, sqlite
    path: "./history"
  token_calculation:
    default_provider: openai
  pricing:
    # 自定义定价配置
    gpt-4-custom:
      input_price: 0.025
      output_price: 0.05
      currency: USD
      provider: openai
  token_tracker:
    cache_ttl: 300  # 5分钟
  manager:
    enable_async_batching: true
    batch_size: 10
    batch_timeout: 1.0
  hook:
    auto_register: true
    workflow_context: {}
```

### 3. 集成到LLM管理器

```python
from src.services.history.hooks import HistoryRecordingHook

# 获取服务实例
history_manager = container.get(IHistoryManager)
token_service = container.get(TokenCalculationService)
cost_calculator = container.get(ICostCalculator)

# 创建历史记录钩子
history_hook = HistoryRecordingHook(
    history_manager=history_manager,
    token_calculation_service=token_service,
    cost_calculator=cost_calculator,
    workflow_context={"workflow_id": "my_workflow"}
)

# 添加到LLM管理器
llm_manager.add_history_hook(history_hook)
```

### 4. 使用新的Token追踪

```python
from src.services.history.token_tracker import WorkflowTokenTracker

# 获取Token追踪器
token_tracker = container.get(ITokenTracker)

# 追踪Token使用
await token_tracker.track_workflow_token_usage(
    workflow_id="my_workflow",
    model="gpt-4",
    provider="openai",
    prompt_tokens=100,
    completion_tokens=50,
    source=TokenSource.API,
    confidence=1.0
)

# 获取统计信息
stats = await token_tracker.get_workflow_statistics("my_workflow")
print(f"总Token: {stats.total_tokens}")
print(f"总成本: {stats.total_cost}")
```

### 5. 使用统计服务

```python
from src.services.history.statistics_service import HistoryStatisticsService

# 获取统计服务
stats_service = container.get(HistoryStatisticsService)

# 获取工作流汇总
summary = await stats_service.get_workflow_token_summary("my_workflow")

# 获取跨工作流对比
comparison = await stats_service.get_cross_workflow_comparison(
    ["workflow1", "workflow2", "workflow3"],
    metric="total_cost"
)

# 获取使用趋势
trends = await stats_service.get_model_usage_trends("my_workflow", days=7)
```

## 使用示例

### 基本使用

```python
import asyncio
from src.services.container import ServiceContainer
from src.services.history.di_config import register_history_services

async def main():
    # 创建容器
    container = ServiceContainer()
    
    # 配置
    config = {
        "history": {
            "enabled": True,
            "storage": {"type": "memory"},
            "pricing": {
                "gpt-3.5-turbo": {
                    "input_price": 0.0015,
                    "output_price": 0.002,
                    "currency": "USD"
                }
            }
        }
    }
    
    # 注册服务
    register_history_services(container, config)
    
    # 获取服务
    history_manager = container.get(IHistoryManager)
    cost_calculator = container.get(ICostCalculator)
    
    # 使用服务
    # ... 你的业务逻辑

if __name__ == "__main__":
    asyncio.run(main())
```

### 工作流集成

```python
from src.services.history.hooks import HistoryRecordingHook
from src.services.llm.manager import LLMManager

class WorkflowManager:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 设置历史记录钩子
        self._setup_history_hook()
    
    def _setup_history_hook(self):
        """设置历史记录钩子"""
        # 从容器获取服务
        history_hook = container.get(HistoryRecordingHook)
        
        # 更新工作流上下文
        history_hook.set_workflow_context({
            "workflow_id": self.workflow_id,
            "workflow_name": "my_workflow",
            "start_time": datetime.now().isoformat()
        })
        
        # 添加到LLM管理器
        self.llm_manager.add_history_hook(history_hook)
    
    async def process_request(self, messages):
        """处理请求"""
        response = await self.llm_manager.execute_with_fallback(
            messages=messages,
            task_type="chat",
            session_id=self.workflow_id
        )
        return response
```

### 成本监控

```python
from src.services.history.statistics_service import HistoryStatisticsService

class CostMonitor:
    def __init__(self, stats_service: HistoryStatisticsService):
        self.stats_service = stats_service
    
    async def get_daily_cost_report(self, workflow_id: str):
        """获取每日成本报告"""
        cost_analysis = await self.stats_service.get_cost_analysis(
            workflow_id=workflow_id,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now()
        )
        
        return {
            "total_cost": cost_analysis["total_cost"],
            "total_requests": cost_analysis["total_requests"],
            "avg_cost_per_request": cost_analysis["avg_cost_per_request"],
            "model_breakdown": cost_analysis["model_breakdown"]
        }
    
    async def get_cost_trends(self, workflow_id: str, days: int = 7):
        """获取成本趋势"""
        trends = await self.stats_service.get_model_usage_trends(
            workflow_id=workflow_id,
            days=days
        )
        
        # 提取成本趋势
        cost_trends = {}
        for date, data in trends["data"].items():
            cost_trends[date] = data["total_cost"]
        
        return cost_trends
```

## 配置选项详解

### 存储配置

```yaml
history:
  storage:
    type: file  # 存储类型
    path: "./history"  # 文件存储路径
    # SQLite配置
    db_path: "./history.db"  # SQLite数据库路径
```

### Token计算配置

```yaml
history:
  token_calculation:
    default_provider: openai  # 默认提供商
    # 提供商特定配置
    providers:
      openai:
        model_mapping:
          "gpt-4": "gpt-4"
          "gpt-4-turbo": "gpt-4-turbo"
      anthropic:
        model_mapping:
          "claude-3": "claude-3-opus-20240229"
```

### 定价配置

```yaml
history:
  pricing:
    # OpenAI模型定价
    "gpt-4":
      input_price: 0.03
      output_price: 0.06
      currency: USD
      provider: openai
    
    # 自定义模型定价
    "custom-model":
      input_price: 0.01
      output_price: 0.02
      currency: USD
      provider: custom
```

### 性能配置

```yaml
history:
  token_tracker:
    cache_ttl: 300  # 缓存生存时间（秒）
  
  manager:
    enable_async_batching: true  # 启用异步批处理
    batch_size: 10  # 批处理大小
    batch_timeout: 1.0  # 批处理超时（秒）
```

## 故障排除

### 常见问题

1. **历史记录未保存**
   - 检查 `history.enabled` 配置
   - 确认存储路径权限
   - 查看日志中的错误信息

2. **Token计算不准确**
   - 确认模型名称正确
   - 检查提供商配置
   - 验证Token计算服务初始化

3. **成本计算错误**
   - 检查定价配置格式
   - 确认货币单位一致
   - 验证Token数量字段

4. **性能问题**
   - 调整批处理大小
   - 增加缓存TTL
   - 考虑使用SQLite存储

### 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger("src.services.history").setLevel(logging.DEBUG)

# 检查服务状态
history_manager = container.get(IHistoryManager)
storage_info = await history_manager.get_storage_info()
print(f"存储信息: {storage_info}")

# 检查批处理状态
batch_status = history_manager.get_batch_status()
print(f"批处理状态: {batch_status}")
```

## 最佳实践

1. **合理配置缓存**
   - 根据使用频率调整TTL
   - 监控缓存命中率
   - 定期清理过期缓存

2. **优化存储性能**
   - 高频场景使用SQLite
   - 定期清理旧记录
   - 考虑数据压缩

3. **监控成本**
   - 设置成本预警
   - 定期分析使用模式
   - 优化模型选择策略

4. **错误处理**
   - 实现降级机制
   - 记录详细错误日志
   - 提供恢复策略

## 迁移检查清单

- [ ] 更新依赖注入配置
- [ ] 配置历史管理参数
- [ ] 集成历史记录钩子
- [ ] 测试Token追踪功能
- [ ] 验证成本计算准确性
- [ ] 配置存储后端
- [ ] 设置监控和告警
- [ ] 编写单元测试
- [ ] 性能测试
- [ ] 文档更新

## 后续计划

1. **性能优化**
   - 实现更高效的缓存策略
   - 优化批量操作
   - 支持分布式存储

2. **功能扩展**
   - 添加更多统计维度
   - 支持实时监控
   - 集成外部监控系统

3. **易用性改进**
   - 提供更多预设配置
   - 简化API接口
   - 增强错误提示

通过遵循本指南，您可以顺利迁移到新的历史管理系统，并充分利用其提供的强大功能。