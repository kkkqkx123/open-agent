# Token处理模块测试

这个目录包含了`src/services/llm/token_processing`模块的全面测试套件。

## 测试结构

```
tests/services/llm/token_processing/
├── __init__.py                    # 测试模块初始化
├── pytest.ini                     # pytest配置文件
├── README.md                       # 本文件
├── run_tests.py                    # 测试运行脚本
├── test_token_types.py              # TokenUsage数据类型测试
├── test_base_implementation.py      # 基础实现类测试
├── test_hybrid_processor.py        # 混合处理器测试
├── test_conversation_tracker.py     # 对话跟踪器测试
└── test_integration.py             # 集成测试
```

## 测试覆盖范围

### 1. TokenUsage数据类型测试 (`test_token_types.py`)
- ✅ 默认初始化
- ✅ 自定义初始化
- ✅ 属性方法（is_from_api, is_from_local）
- ✅ 数据操作（add, copy）
- ✅ 序列化（to_dict, from_dict）
- ✅ 边界情况处理

### 2. 基础实现类测试 (`test_base_implementation.py`)
- ✅ BaseTokenProcessor默认行为
- ✅ CachedTokenProcessor缓存功能
- ✅ DegradationTokenProcessor降级策略
- ✅ 统计信息跟踪
- ✅ 错误处理

### 3. 混合处理器测试 (`test_hybrid_processor.py`)
- ✅ 初始化配置
- ✅ 本地计算优先模式
- ✅ API计算优先模式
- ✅ 降级策略触发
- ✅ 缓存机制
- ✅ 对话跟踪集成
- ✅ 错误处理和恢复

### 4. 对话跟踪器测试 (`test_conversation_tracker.py`)
- ✅ 会话管理（开始/结束）
- ✅ 消息添加和跟踪
- ✅ 统计信息计算
- ✅ 历史记录管理
- ✅ 数据导出（JSON/文本/CSV）
- ✅ 内存限制和清理

### 5. 集成测试 (`test_integration.py`)
- ✅ 组件间协同工作
- ✅ 端到端场景测试
- ✅ 性能监控
- ✅ 并发安全性
- ✅ 配置灵活性
- ✅ 内存管理

## 运行测试

### 方法1：使用测试脚本（推荐）

```bash
# 运行所有测试
python tests/services/llm/token_processing/run_tests.py

# 运行测试并生成覆盖率报告
python tests/services/llm/token_processing/run_tests.py --coverage
```

### 方法2：使用pytest直接

```bash
# 运行所有测试
pytest tests/services/llm/token_processing/ -v

# 运行特定测试文件
pytest tests/services/llm/token_processing/test_token_types.py -v

# 运行特定测试类
pytest tests/services/llm/token_processing/test_token_types.py::TestTokenUsage -v

# 运行特定测试方法
pytest tests/services/llm/token_processing/test_token_types.py::TestTokenUsage::test_default_initialization -v
```

### 方法3：运行覆盖率测试

```bash
# 安装覆盖率工具（如果尚未安装）
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/services/llm/token_processing/ --cov=src/services/llm/token_processing --cov-report=html
```

## 测试配置

测试配置在`pytest.ini`文件中定义：

- **详细输出**：显示详细的测试结果
- **短回溯**：简洁的错误信息
- **严格标记**：严格的标记检查
- **颜色输出**：彩色终端输出
- **持续时间**：显示最慢的测试
- **警告过滤**：过滤已知的弃用警告

## 预期结果

所有测试应该通过。如果任何测试失败，请检查：

1. **依赖项**：确保所有必需的依赖项已安装
2. **Python路径**：确保模块路径正确设置
3. **版本兼容性**：确保Python版本兼容（3.8+）
4. **环境变量**：检查是否需要特定的环境变量

## 测试标记

测试使用以下标记进行分类：

- `unit`：单元测试
- `integration`：集成测试
- `slow`：运行时间较长的测试

运行特定标记的测试：

```bash
# 只运行单元测试
pytest tests/services/llm/token_processing/ -m unit -v

# 只运行集成测试
pytest tests/services/llm/token_processing/ -m integration -v

# 排除慢速测试
pytest tests/services/llm/token_processing/ -m "not slow" -v
```

## 持续集成

这些测试设计为在CI/CD环境中运行：

```yaml
# GitHub Actions示例
- name: Run Token Processing Tests
  run: |
    python tests/services/llm/token_processing/run_tests.py
```

## 覆盖率目标

- **整体覆盖率**：≥ 90%
- **分支覆盖率**：≥ 85%
- **关键路径覆盖率**：100%

## 故障排除

### 常见问题

1. **导入错误**：
   ```
   ModuleNotFoundError: No module named 'src.services.llm.token_processing'
   ```
   **解决方案**：从项目根目录运行测试，或设置PYTHONPATH

2. **类型错误**：
   ```
   TypeError: 'NoneType' object is not callable
   ```
   **解决方案**：检查mock对象设置，确保正确的方法签名

3. **异步问题**：
   ```
   RuntimeError: This event loop is already running
   ```
   **解决方案**：使用pytest-asyncio或适当的async/await

### 调试技巧

1. **使用pdb调试**：
   ```bash
   pytest tests/services/llm/token_processing/test_token_types.py::TestTokenUsage::test_default_initialization -s --pdb
   ```

2. **显示本地变量**：
   ```bash
   pytest tests/services/llm/token_processing/ -v -l
   ```

3. **只运行失败的测试**：
   ```bash
   pytest tests/services/llm/token_processing/ --lf
   ```

## 贡献指南

添加新测试时：

1. **遵循命名约定**：`test_<功能>.py`
2. **使用描述性名称**：`test_<具体场景>`
3. **添加文档字符串**：解释测试目的
4. **使用适当的断言**：提供清晰的错误信息
5. **模拟外部依赖**：使用unittest.mock
6. **清理测试数据**：使用teardown方法

## 性能基准

测试套件还包括性能基准测试：

- **Token计算速度**：每秒处理的token数
- **内存使用**：峰值和平均内存消耗
- **缓存效率**：命中率和内存使用
- **并发性能**：多线程处理能力

运行性能测试：

```bash
pytest tests/services/llm/token_processing/test_integration.py::TestTokenProcessingIntegration::test_performance_monitoring -v -s