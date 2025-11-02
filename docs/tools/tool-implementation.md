基于我的分析，我发现了以下需要修改的地方：

## 分析结果

### 1. metadata 的当前作用
- **存储工具调用信息**：`metadata["tool_calls"]` 用于存储工具调用列表
- **存储工具调用 ID**：`metadata["tool_call_id"]` 用于存储工具调用的 ID
- **其他元数据**：存储各种额外的消息信息

### 2. 需要修改的关键文件

#### **MessageAdapter** (`src/infrastructure/graph/adapters/message_adapter.py`)
- `extract_tool_calls` 方法：从 metadata 中提取工具调用
- `add_tool_calls_to_message` 方法：向 metadata 中添加工具调用
- `from_graph_message` 方法：需要处理 LangChain 消息的 tool_calls 属性

#### **其他节点文件**
- `llm_node.py`、`analysis_node.py` 等：需要更新以支持新的工具调用格式
