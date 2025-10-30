# LLM API 重试与超时配置方案

## 1. 现状分析

### 1.1 当前配置情况

通过分析当前代码库，发现LLM API的重试和超时配置存在以下现状：

#### 1.1.1 配置位置
- **LLM配置文件中**：在 `configs/llms/` 目录下的配置文件中已经定义了基础的 `timeout` 和 `max_retries` 参数
- **客户端配置类**：`LLMClientConfig` 类中定义了 `timeout` 和 `max_retries` 字段
- **重试钩子**：`SmartRetryHook` 类提供了丰富的重试策略配置

#### 1.1.2 当前配置项
```yaml
# 在 configs/llms/_group.yaml 中
openai_group:
  parameters:
    timeout: 30
    max_retries: 3

gemini_group:
  parameters:
    timeout: 30
    max_retries: 3

anthropic_group:
  parameters:
    timeout: 30
    max_retries: 3
```

#### 1.1.3 重试钩子配置
```python
# SmartRetryHook 支持的重试参数
max_retries: int = 3           # 最大重试次数
base_delay: float = 1.0        # 基础延迟时间（秒）
max_delay: float = 60.0        # 最大延迟时间（秒）
jitter: bool = True            # 是否添加随机抖动
exponential_base: float = 2.0  # 指数退避基数
```

### 1.2 存在的问题

1. **配置分散**：重试策略参数分散在多个地方，缺乏统一管理
2. **功能不完整**：缺少细粒度的重试策略配置（如退避策略、抖动配置等）
3. **缺乏全局配置**：没有全局的重试和超时配置选项
4. **配置验证不足**：缺少对配置值的完整验证

## 2. 配置方案设计

### 2.1 配置项分类建议

#### 2.1.1 作为LLM配置项的理由
- **紧密相关**：重试和超时是LLM API调用的核心特性
- **模型差异**：不同LLM提供商对重试和超时的处理方式不同
- **性能优化**：可以根据模型特性调整重试策略
- **现有架构**：当前配置系统已经支持这些参数

#### 2.1.2 建议的配置结构

```yaml
# 建议的配置结构
retry_config:
  max_retries: 3                    # 最大重试次数
  base_delay: 1.0                   # 基础延迟时间（秒）【第一次重试前】
  max_delay: 60.0                   # 最大延迟时间（秒）【总的重试次数】
  jitter: true                      # 是否添加随机抖动【1+-0.2作为实际延迟时间的因子，避免同时重试】
  exponential_base: 2.0             # 指数退避基数【每次重试延迟翻倍】
  retry_on_status_codes:            # 需要重试的HTTP状态码
    - 429  # 频率限制
    - 500  # 服务器内部错误
    - 502  # 网关错误
    - 503  # 服务不可用
    - 504  # 网关超时
  retry_on_errors:                  # 需要重试的错误类型
    - "timeout"
    - "rate_limit"
    - "service_unavailable"

timeout_config:
  request_timeout: 30               # 请求超时时间（秒）【总时间，包括连接建立、读取、写入】
  connect_timeout: 10               # 连接超时时间（秒）【等待建立TCP连接】
  read_timeout: 30                  # 读取超时时间（秒）【接收数据】
  write_timeout: 30                 # 写入超时时间（秒）【发送数据】
```

### 2.2 配置层级设计

#### 2.2.1 全局配置（global.yaml）
```yaml
# configs/global.yaml
llm:
  default_timeout: 30
  default_max_retries: 3
  retry_config:
    base_delay: 1.0
    max_delay: 60.0
    jitter: true
    exponential_base: 2.0
```

#### 2.2.2 模型组配置（_group.yaml）
```yaml
# configs/llms/_group.yaml
openai_group:
  parameters:
    timeout: 30
    max_retries: 3
  retry_config:
    base_delay: 1.0
    max_delay: 30.0  # OpenAI通常响应较快，设置较小的最大延迟
    jitter: true
    exponential_base: 2.0
```

#### 2.2.3 具体模型配置
```yaml
# configs/llms/provider/openai/openai-gpt4.yaml
parameters:
  timeout: 60  # GPT-4可能需要更长的超时时间
  max_retries: 5
retry_config:
  base_delay: 2.0  # GPT-4频率限制更严格，增加基础延迟
  max_delay: 120.0
  jitter: true
  exponential_base: 2.0
```

## 3. 技术实现方案

### 3.1 配置模型扩展

#### 3.1.1 扩展 LLMConfig 类
```python
@dataclass
class RetryTimeoutConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    exponential_base: float = 2.0
    retry_on_status_codes: List[int] = field(
    default_factory=lambda: [429, 500, 502, 503, 504]
    )
    retry_on_errors: List[str] = field(
    default_factory=lambda: ["timeout", "rate_limit", "service_unavailable"]
    )

@dataclass
class TimeoutConfig:
    """超时配置"""
    request_timeout: int = 30
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30

@dataclass
class LLMConfig:
    """扩展LLM配置"""
    # 现有字段...
    timeout_config: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry_config: RetryTimeoutConfig = field(default_factory=RetryTimeoutConfig)
```

### 3.2 配置验证规则

#### 3.2.1 验证规则定义
```python
# 在 config_manager.py 中添加验证规则
validation_rules = [
    ConfigValidationRule(
        field_path="retry_config.max_retries",
        required=False,
        field_type=int,
        min_value=0,
        max_value=10,
        error_message="最大重试次数必须是0-10之间的整数"
    ),
    ConfigValidationRule(
        field_path="retry_config.base_delay",
        required=False,
        field_type=float,
        min_value=0.1,
        max_value=300.0,
        error_message="基础延迟时间必须在0.1-300秒之间"
    ),
    ConfigValidationRule(
        field_path="timeout_config.request_timeout",
        required=False,
        field_type=int,
        min_value=1,
        max_value=300,
        error_message="请求超时时间必须在1-300秒之间"
    )
]
```

### 3.3 配置继承机制

#### 3.3.1 配置合并策略
- **全局配置**：提供默认值
- **模型组配置**：继承并覆盖全局配置
- **具体模型配置**：继承并覆盖模型组配置
- **运行时配置**：最高优先级，覆盖所有配置

## 4. 向后兼容性

### 4.1 现有配置兼容

保持对现有配置的完全兼容：
```python
# 如果新配置不存在，使用旧配置
if hasattr(config, 'retry_config'):
    retry_config = config.retry_config
else:
    retry_config = RetryTimeoutConfig(
        max_retries=config.max_retries,
        base_delay=1.0,  # 默认值
        max_delay=60.0,  # 默认值
        jitter=True      # 默认值
    )
```

### 4.2 配置迁移工具

提供配置迁移脚本，将旧配置转换为新格式：
```python
def migrate_legacy_config(old_config: Dict) -> Dict:
    """迁移旧配置到新格式"""
    new_config = old_config.copy()
    
    # 迁移重试配置
    if 'max_retries' in old_config.get('parameters', {}):
        new_config.setdefault('retry_config', {})
        new_config['retry_config']['max_retries'] = old_config['parameters']['max_retries']
    
    # 迁移超时配置
    if 'timeout' in old_config.get('parameters', {}):
        new_config.setdefault('timeout_config', {})
        new_config['timeout_config']['request_timeout'] = old_config['parameters']['timeout']
    
    return new_config
```

## 5. 实施计划

### 5.1 第一阶段：配置模型扩展
1. 扩展 `LLMConfig` 类，添加 `RetryTimeoutConfig` 和 `TimeoutConfig`
2. 更新配置加载逻辑，支持新配置结构
3. 添加配置验证规则

### 5.2 第二阶段：客户端集成
1. 更新 `LLMClientConfig.from_llm_config` 方法
2. 修改客户端实现，使用新的配置结构
3. 更新重试钩子，支持细粒度配置

### 5.3 第三阶段：配置更新
1. 更新现有配置文件，添加新配置项
2. 提供配置迁移工具
3. 更新文档和示例

### 5.4 第四阶段：测试验证
1. 编写单元测试，验证配置加载和验证
2. 集成测试，验证重试和超时行为
3. 性能测试，验证配置对性能的影响

## 6. 总结

将重试和超时配置作为LLM配置的一部分是最合理的选择，原因如下：

1. **架构一致性**：符合现有的配置系统设计
2. **灵活性**：支持不同模型的不同配置需求
3. **向后兼容**：可以平滑迁移现有配置
4. **可扩展性**：便于未来添加更多重试和超时相关配置

通过这个方案，可以为用户提供更精细化的LLM API调用控制，同时保持系统的稳定性和向后兼容性。