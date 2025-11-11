# DeepAPI Engine 使用指南

## 1. 快速开始

### 1.1 安装依赖

```bash
pip install openai aiohttp
```

### 1.2 基础使用示例

**Deep Think Engine 基础使用:**
```python
import asyncio
from engine import DeepThinkEngine
from models import MessageContent

async def main():
    # 创建引擎实例
    engine = DeepThinkEngine(
        api_key="your-openai-api-key",
        model="gpt-4",
        problem_statement=MessageContent(
            text="如何优化一个大型Python项目的性能？",
            content_type="text"
        )
    )
    
    # 运行引擎
    result = await engine.run()
    
    # 获取结果
    print(f"最终答案: {result.final_answer}")
    print(f"思考过程: {result.thinking_process}")
    print(f"验证次数: {result.verification_count}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Ultra Think Engine 基础使用:**
```python
import asyncio
from engine import UltraThinkEngine
from models import MessageContent

async def main():
    # 创建引擎实例
    engine = UltraThinkEngine(
        api_key="your-openai-api-key",
        model="gpt-4",
        problem_statement=MessageContent(
            text="分析人工智能对教育行业的长期影响",
            content_type="text"
        ),
        parallel_run_agent=3  # 同时运行3个Agent
    )
    
    # 添加进度监控
    async def on_progress(event):
        print(f"进度: {event.type} - {event.data}")
    
    engine.on_agent_update = on_progress
    
    # 运行引擎
    result = await engine.run()
    
    # 获取结果
    print(f"综合答案: {result.synthesized_answer}")
    print(f"Agent数量: {len(result.agent_results)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. 配置选项详解

### 2.1 Deep Think Engine 配置

```python
# 完整配置示例
engine = DeepThinkEngine(
    # 必需参数
    api_key="your-api-key",
    model="gpt-4",
    problem_statement=MessageContent(text="问题描述", content_type="text"),
    
    # 可选参数
    conversation_history=[],  # 对话历史
    max_iterations=20,        # 最大迭代次数
    required_verifications=3,  # 所需验证次数
    max_errors=10,            # 最大错误次数
    enable_planning=True,     # 启用计划功能
    enable_parallel_check=True, # 启用并行验证
    
    # 模型阶段配置
    model_stages={
        "initial": "gpt-4",
        "improvement": "gpt-4",
        "verification": "gpt-4",
        "correction": "gpt-4",
        "summary": "gpt-4"
    }
)
```

### 2.2 Ultra Think Engine 配置

```python
# 完整配置示例
engine = UltraThinkEngine(
    # 必需参数
    api_key="your-api-key", 
    model="gpt-4",
    problem_statement=MessageContent(text="复杂问题", content_type="text"),
    
    # 可选参数
    conversation_history=[],    # 对话历史
    num_agents=None,           # Agent数量（None表示自动决定）
    parallel_run_agent=3,      # 并行Agent数量
    
    # 事件回调
    on_agent_update=None,      # Agent更新回调
    
    # 模型阶段配置
    model_stages={
        "planning": "gpt-4",
        "agent_config": "gpt-4", 
        "agent_thinking": "gpt-4",
        "synthesis": "gpt-4"
    }
)
```

## 3. 高级功能使用

### 3.1 自定义提示词

```python
from engine.prompts import DEEP_THINK_PROMPT, ULTRA_THINK_PROMPT

# 修改默认提示词
custom_prompt = DEEP_THINK_PROMPT.replace(
    "Think step by step", 
    "请按照以下步骤思考："
)

# 在引擎中使用自定义提示词
engine = DeepThinkEngine(
    api_key="your-key",
    model="gpt-4",
    problem_statement=MessageContent(text="问题", content_type="text")
)

# 注意：当前版本需要修改源码来使用自定义提示词
# 建议在 prompts.py 中创建新的提示词常量
```

### 3.2 多模态输入支持

```python
from models import MessageContent

# 文本输入
text_content = MessageContent(
    text="描述这张图片中的场景",
    content_type="text"
)

# 图像输入（需要扩展支持）
image_content = MessageContent(
    text="分析这张图片",
    content_type="image",
    image_url="https://example.com/image.jpg"
)

# 多模态组合
multi_content = MessageContent(
    text="基于以下文本和图片进行分析",
    content_type="multimodal",
    image_url="https://example.com/image.jpg"
)
```

### 3.3 进度监控和事件处理

```python
from models import ProgressEvent

async def detailed_progress_handler(event: ProgressEvent):
    """详细的进度事件处理器"""
    if event.type == "agent_update":
        agent_id = event.data.get("agent_id")
        status = event.data.get("status")
        progress = event.data.get("progress")
        
        print(f"Agent {agent_id}: {status} - {progress}%")
        
    elif event.type == "thinking":
        iteration = event.data.get("iteration")
        print(f"思考迭代: {iteration}")
        
    elif event.type == "verification":
        verification_count = event.data.get("verification_count")
        print(f"验证次数: {verification_count}")

# 使用自定义事件处理器
engine = UltraThinkEngine(
    api_key="your-key",
    model="gpt-4", 
    problem_statement=MessageContent(text="问题", content_type="text"),
    on_agent_update=detailed_progress_handler
)
```

## 4. 错误处理和调试

### 4.1 常见错误处理

```python
import asyncio
from engine import DeepThinkEngine
from models import MessageContent

async def safe_run():
    try:
        engine = DeepThinkEngine(
            api_key="invalid-key",  # 测试错误情况
            model="gpt-4",
            problem_statement=MessageContent(text="测试", content_type="text")
        )
        
        result = await engine.run()
        return result
        
    except Exception as e:
        print(f"引擎执行错误: {e}")
        
        # 根据错误类型处理
        if "API key" in str(e):
            print("请检查API密钥配置")
        elif "rate limit" in str(e):
            print("达到API调用限制，请稍后重试")
        elif "timeout" in str(e):
            print("请求超时，请检查网络连接")
        
        return None

# 运行安全执行
result = await safe_run()
```

### 4.2 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 自定义调试回调
def debug_callback(event):
    if event.type in ["thinking", "verification", "correction"]:
        print(f"DEBUG - {event.type}: {event.data}")

engine = DeepThinkEngine(
    api_key="your-key",
    model="gpt-4",
    problem_statement=MessageContent(text="调试测试", content_type="text")
)

# 注意：当前版本需要修改源码来添加调试回调
# 建议在引擎类中添加调试功能
```

## 5. 性能优化技巧

### 5.1 并发配置优化

```python
# Ultra Think Engine 并发优化
engine = UltraThinkEngine(
    api_key="your-key",
    model="gpt-4", 
    problem_statement=MessageContent(text="复杂分析", content_type="text"),
    
    # 根据API限制调整并发数
    parallel_run_agent=2,  # 保守设置，避免触发限流
    
    # 或者根据问题复杂度调整
    num_agents=4,  # 固定Agent数量
)
```

### 5.2 模型选择策略

```python
# 混合模型策略
engine = DeepThinkEngine(
    api_key="your-key",
    problem_statement=MessageContent(text="问题", content_type="text"),
    
    # 不同阶段使用不同模型
    model_stages={
        "initial": "gpt-3.5-turbo",      # 初步思考
        "improvement": "gpt-4",          # 改进阶段
        "verification": "gpt-3.5-turbo",  # 验证阶段
        "correction": "gpt-4",           # 修正阶段
        "summary": "gpt-4"              # 最终摘要
    }
)
```

### 5.3 缓存和重用

```python
# 对话历史缓存和重用
conversation_history = [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
]

engine = DeepThinkEngine(
    api_key="your-key",
    model="gpt-4",
    problem_statement=MessageContent(text="新问题", content_type="text"),
    conversation_history=conversation_history  # 重用历史
)
```

## 6. 集成到现有项目

### 6.1 Web 应用集成

```python
from fastapi import FastAPI, HTTPException
from engine import DeepThinkEngine
from models import MessageContent
import asyncio

app = FastAPI()

@app.post("/analyze")
async def analyze_question(question: str):
    """Web API 端点"""
    try:
        engine = DeepThinkEngine(
            api_key="your-key",
            model="gpt-4",
            problem_statement=MessageContent(
                text=question, 
                content_type="text"
            )
        )
        
        result = await engine.run()
        
        return {
            "answer": result.final_answer,
            "thinking_process": result.thinking_process,
            "verification_count": result.verification_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 6.2 命令行工具集成

```python
import argparse
import asyncio
from engine import DeepThinkEngine
from models import MessageContent

async def main():
    parser = argparse.ArgumentParser(description='Deep Think 命令行工具')
    parser.add_argument('question', help='要分析的问题')
    parser.add_argument('--api-key', required=True, help='OpenAI API密钥')
    parser.add_argument('--model', default='gpt-4', help='使用的模型')
    
    args = parser.parse_args()
    
    engine = DeepThinkEngine(
        api_key=args.api_key,
        model=args.model,
        problem_statement=MessageContent(
            text=args.question,
            content_type="text"
        )
    )
    
    result = await engine.run()
    
    print("=" * 50)
    print("最终答案:")
    print(result.final_answer)
    print("\n思考过程:")
    print(result.thinking_process)
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

## 7. 最佳实践

### 7.1 问题表述技巧

```python
# 好的问题表述
good_question = """
如何设计一个可扩展的微服务架构？请考虑以下方面：
1. 服务发现和注册
2. 负载均衡策略  
3. 数据一致性
4. 监控和日志
5. 安全性考虑
"""

# 避免的问题表述
bad_question = "微服务架构"  # 过于宽泛
```

### 7.2 参数调优建议

**简单问题:**
- `max_iterations=10`
- `required_verifications=2`
- `enable_parallel_check=False`

**复杂问题:**
- `max_iterations=25`
- `required_verifications=4`
- `enable_parallel_check=True`
- `parallel_run_agent=3`

### 7.3 资源管理

```python
# 使用上下文管理器管理资源
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def engine_session(api_key, model, question):
    engine = DeepThinkEngine(
        api_key=api_key,
        model=model,
        problem_statement=MessageContent(text=question, content_type="text")
    )
    
    try:
        yield engine
    finally:
        # 清理资源
        pass

# 使用示例
async with engine_session("your-key", "gpt-4", "问题") as engine:
    result = await engine.run()
```

## 8. 故障排除

### 8.1 常见问题解决

**问题:** API 调用超时
**解决:** 增加超时时间或检查网络连接

**问题:** 内存使用过高
**解决:** 减少 `max_iterations` 或 `parallel_run_agent`

**问题:** 验证失败次数过多
**解决:** 简化问题表述或增加 `max_errors`

### 8.2 性能监控

```python
import time
import asyncio

async def monitored_run(engine):
    start_time = time.time()
    
    result = await engine.run()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"执行时间: {execution_time:.2f}秒")
    print(f"API调用次数: {估计值}")  # 需要引擎提供统计信息
    
    return result
```

## 总结

本指南提供了 DeepAPI Engine 的全面使用说明，从基础使用到高级功能，涵盖了配置、优化、集成和故障排除等各个方面。根据具体需求选择合适的配置和优化策略，可以获得最佳的使用体验和性能表现。