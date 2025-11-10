"""
GraphWorkflow 测试 README

GraphWorkflow 集成测试文档和说明。
"""

# GraphWorkflow 集成测试

本目录包含 GraphWorkflow 的端到端集成测试，用于验证工作流的完整功能。

## 测试结构

```
tests/integration/
├── test_graph_workflow_integration.py  # 主要集成测试
├── test_graph_workflow_config.py        # 配置相关测试
├── test_graph_workflow_execution.py     # 执行相关测试
└── test_runner.py                       # 测试运行器
```

## 测试内容

### 1. 主要集成测试 (`test_graph_workflow_integration.py`)

- **配置加载测试**: 验证从不同来源（字典、YAML、JSON）加载配置
- **工作流创建测试**: 验证 GraphWorkflow 和 SimpleGraphWorkflow 创建
- **验证测试**: 测试配置验证功能
- **信息获取测试**: 测试获取节点、边、状态模式等信息
- **错误处理测试**: 测试各种错误情况的处理
- **条件工作流测试**: 测试条件分支工作流
- **执行接口测试**: 测试同步、异步、流式执行接口

### 2. 配置测试 (`test_graph_workflow_config.py`)

- **最小配置测试**: 验证最小有效配置
- **完整配置测试**: 验证包含所有可选字段的配置
- **复杂状态模式测试**: 测试复杂的状态字段定义
- **多节点多边形测试**: 测试复杂的工作流结构
- **条件边测试**: 测试条件边的配置
- **配置验证错误测试**: 测试各种配置错误
- **文件加载测试**: 测试从文件加载配置
- **循环配置测试**: 测试包含循环的工作流配置
- **并行结构测试**: 测试并行工作流配置
- **配置导出导入一致性测试**: 验证配置导出的正确性

### 3. 执行测试 (`test_graph_workflow_execution.py`)

- **同步执行测试**: 测试基本同步执行功能
- **异步执行测试**: 测试异步执行功能
- **流式执行测试**: 测试流式执行功能
- **初始状态测试**: 测试带初始状态的执行
- **错误处理测试**: 测试执行过程中的错误处理
- **条件工作流执行测试**: 测试条件分支的实际执行
- **并行工作流执行测试**: 测试并行结构的执行
- **检查点执行测试**: 测试带检查点的执行
- **超时执行测试**: 测试带超时的执行

## 运行测试

### 使用测试运行器

```bash
# 运行所有测试
python tests/integration/test_runner.py run

# 生成完整报告（包含覆盖率）
python tests/integration/test_runner.py report

# 运行特定测试
python tests/integration/test_runner.py specific test_create_workflow_from_dict

# 显示帮助
python tests/integration/test_runner.py help
```

### 使用 pytest 直接运行

```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/integration/test_graph_workflow_integration.py -v

# 运行特定测试用例
pytest tests/integration/test_graph_workflow_integration.py::TestGraphWorkflowIntegration::test_create_workflow_from_dict -v

# 生成 HTML 报告
pytest tests/integration/ -v --html=reports/integration_tests.html --self-contained-html

# 生成覆盖率报告
pytest tests/integration/ --cov=src/application/workflow/ --cov-report=html:reports/coverage
```

## 依赖项

运行测试需要以下依赖：

```bash
pip install pytest pytest-html pytest-cov pytest-asyncio
```

## 测试数据

测试使用以下配置文件：

- `configs/workflows/examples/simple_data_processing.yaml` - 简单数据处理工作流
- `configs/workflows/examples/conditional_routing.yaml` - 条件分支工作流
- `configs/workflows/examples/iterative_processing.yaml` - 迭代处理工作流
- `configs/workflows/examples/llm_conversation.yaml` - LLM 对话工作流
- `configs/workflows/examples/parallel_processing.yaml` - 并行处理工作流

## 输出

测试运行后会在以下位置生成报告：

- `reports/graph_workflow_integration_tests.html` - 集成测试 HTML 报告
- `reports/graph_workflow_complete_report.html` - 完整测试报告
- `reports/coverage/index.html` - 覆盖率报告
- `reports/graph_workflow_test_results.json` - JSON 格式测试结果

## 测试覆盖率

测试覆盖以下模块：

- `src/application/workflow/graph_workflow.py` - GraphWorkflow 基类
- `src/application/workflow/universal_loader.py` - 通用工作流加载器
- `src/infrastructure/graph/config.py` - 图配置相关
- `src/infrastructure/graph/builder.py` - 图构建器

## 最佳实践

1. **测试独立性**: 每个测试应该独立运行，不依赖其他测试的结果
2. **模拟外部依赖**: 使用 mock 来模拟外部函数和依赖
3. **错误场景覆盖**: 不仅要测试成功场景，还要测试各种错误情况
4. **配置完整性**: 测试各种配置组合，确保配置验证的完整性
5. **执行模式**: 测试同步、异步、流式三种执行模式

## 扩展测试

要添加新的集成测试：

1. 在相应的测试文件中添加新的测试类或方法
2. 遵循现有的测试命名约定和结构
3. 确保测试覆盖新的功能点
4. 更新此 README 文档

## 问题排查

如果测试失败：

1. 检查依赖项是否正确安装
2. 确认测试文件路径正确
3. 查看控制台输出的详细错误信息
4. 检查 HTML 报告中的失败详情
5. 验证配置文件是否存在且格式正确

## 持续集成

建议在 CI/CD 流程中包含这些集成测试，确保代码变更不会破坏现有功能。