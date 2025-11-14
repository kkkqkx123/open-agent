"""端到端测试：使用base_workflow.yaml和silicon-Qwen2.5-7B模型

测试完整的工作流构建和执行流程，包括：
1. 加载base_workflow.yaml配置
2. 配置silicon-Qwen2.5-7B模型
3. 构建工作流图
4. 执行工作流并验证结果
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.graph.config import GraphConfig
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.registry import get_global_registry
from src.infrastructure.graph.builtin_functions import get_builtin_node_function
from infrastructure.config.loader.yaml_loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer
from src.application.workflow.universal_loader import UniversalWorkflowLoader
from src.application.workflow.runner import WorkflowRunner


class TestBaseWorkflowWithQwen:
    """测试基础工作流与Qwen模型的集成(该工作流不会实际调用llm api)"""

    @pytest.fixture
    def workflow_config_path(self) -> str:
        """工作流配置文件路径"""
        return str(project_root / "configs" / "workflows" / "base_workflow.yaml")

    @pytest.fixture
    def llm_config_path(self) -> str:
        """LLM配置文件路径"""
        return str(project_root / "configs" / "llms" / "provider" / "siliconflow" / "silicon-Qwen2.5-7B.yaml")

    @pytest.fixture
    def graph_config(self, workflow_config_path: str) -> GraphConfig:
        """加载图配置"""
        import yaml
        
        with open(workflow_config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 转换为GraphConfig对象
        return GraphConfig.from_dict(config_data)

    @pytest.fixture
    def graph_builder(self) -> GraphBuilder:
        """创建图构建器"""
        node_registry = get_global_registry()
        return GraphBuilder(node_registry=node_registry)

    def test_load_workflow_config(self, workflow_config_path: str, graph_config: GraphConfig):
        """测试工作流配置加载"""
        # 验证配置基本信息
        assert graph_config.name == "base_workflow"
        assert graph_config.description == "基础工作流配置"
        assert graph_config.version == "1.0.0"
        
        # 验证状态模式
        assert graph_config.state_schema.name == "BaseWorkflowState"
        assert "messages" in graph_config.state_schema.fields
        assert "input" in graph_config.state_schema.fields
        assert "output" in graph_config.state_schema.fields
        assert "errors" in graph_config.state_schema.fields
        
        # 验证节点配置
        assert "start_node" in graph_config.nodes
        assert "end_node" in graph_config.nodes
        assert graph_config.nodes["start_node"].function_name == "start_node"
        assert graph_config.nodes["end_node"].function_name == "end_node"
        
        # 验证边配置
        assert len(graph_config.edges) == 1
        edge = graph_config.edges[0]
        assert edge.from_node == "start_node"
        assert edge.to_node == "end_node"
        
        # 验证入口点
        assert graph_config.entry_point == "start_node"

    def test_build_graph(self, graph_config: GraphConfig, graph_builder: GraphBuilder):
        """测试图构建"""
        # 构建图
        graph = graph_builder.build_graph(graph_config)
        
        # 验证图构建成功
        assert graph is not None
        
        # 验证节点函数存在
        start_node_func = graph_builder._get_node_function(graph_config.nodes["start_node"])
        end_node_func = graph_builder._get_node_function(graph_config.nodes["end_node"])
        
        assert start_node_func is not None
        assert end_node_func is not None

    def test_register_custom_functions(self, graph_builder: GraphBuilder):
        """测试注册自定义函数"""
        # 定义自定义节点函数
        def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义开始节点函数"""
            messages = state.get("messages", [])
            messages.append({
                "role": "system",
                "content": "工作流开始执行"
            })
            
            return {
                **state,
                "messages": messages,
                "output": "工作流已开始"
            }

        def end_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义结束节点函数"""
            messages = state.get("messages", [])
            messages.append({
                "role": "system",
                "content": "工作流执行完成"
            })
            
            return {
                **state,
                "messages": messages,
                "output": "工作流已完成"
            }

        # 注册自定义函数
        from src.infrastructure.graph.function_registry import FunctionType
        graph_builder.register_function("start_node", start_node, FunctionType.NODE_FUNCTION)
        graph_builder.register_function("end_node", end_node, FunctionType.NODE_FUNCTION)
        
        # 验证函数注册成功
        assert graph_builder.validate_function_exists("start_node", FunctionType.NODE_FUNCTION)
        assert graph_builder.validate_function_exists("end_node", FunctionType.NODE_FUNCTION)

    def test_workflow_execution_with_universal_loader(self, workflow_config_path: str):
        """测试使用通用加载器执行工作流"""
        # 创建通用加载器
        loader = UniversalWorkflowLoader()
        
        # 注册自定义节点函数
        def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义开始节点函数"""
            messages = state.get("messages", [])
            input_text = state.get("input", "")
            
            messages.append({
                "role": "system",
                "content": f"工作流开始执行，输入: {input_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"处理输入: {input_text}"
            }

        def end_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义结束节点函数"""
            messages = state.get("messages", [])
            output_text = state.get("output", "")
            
            messages.append({
                "role": "system",
                "content": f"工作流执行完成，输出: {output_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"最终输出: {output_text}"
            }

        # 注册函数
        from src.application.workflow.universal_loader import FunctionType
        loader.register_function("start_node", start_node, FunctionType.NODE_FUNCTION)
        loader.register_function("end_node", end_node, FunctionType.NODE_FUNCTION)
        
        # 加载工作流
        workflow = loader.load_from_file(workflow_config_path)
        
        # 执行工作流
        initial_state = {
            "input": "测试输入",
            "messages": []
        }
        
        result = workflow.run(initial_state)
        
        # 验证执行结果
        assert result is not None
        assert "messages" in result
        assert "output" in result
        assert len(result["messages"]) >= 2  # 至少有开始和结束消息
        assert "工作流开始执行" in result["messages"][0]["content"]
        assert "工作流执行完成" in result["messages"][-1]["content"]
        assert "最终输出: 处理输入: 测试输入" == result["output"]

    def test_workflow_execution_with_runner(self, workflow_config_path: str):
        """测试使用工作流运行器执行工作流"""
        # 创建工作流运行器
        runner = WorkflowRunner()
        
        # 注册自定义节点函数
        def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义开始节点函数"""
            messages = state.get("messages", [])
            input_text = state.get("input", "")
            
            messages.append({
                "role": "system",
                "content": f"工作流开始执行，输入: {input_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"处理输入: {input_text}"
            }

        def end_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义结束节点函数"""
            messages = state.get("messages", [])
            output_text = state.get("output", "")
            
            messages.append({
                "role": "system",
                "content": f"工作流执行完成，输出: {output_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"最终输出: {output_text}"
            }

        # 注册函数
        from src.application.workflow.universal_loader import FunctionType
        runner.loader.register_function("start_node", start_node, FunctionType.NODE_FUNCTION)
        runner.loader.register_function("end_node", end_node, FunctionType.NODE_FUNCTION)
        
        # 执行工作流
        initial_data = {
            "input": "使用Runner测试输入",
            "messages": []
        }
        
        result = runner.run_workflow(workflow_config_path, initial_data)
        
        # 验证执行结果
        assert result.success is True
        assert result.result is not None
        assert "messages" in result.result
        assert "output" in result.result
        assert len(result.result["messages"]) >= 2
        assert "工作流开始执行" in result.result["messages"][0]["content"]
        assert "工作流执行完成" in result.result["messages"][-1]["content"]
        assert "最终输出: 处理输入: 使用Runner测试输入" == result.result["output"]
        assert result.execution_time is not None
        assert result.execution_time > 0

    def test_workflow_validation(self, workflow_config_path: str):
        """测试工作流配置验证"""
        # 创建工作流运行器
        runner = WorkflowRunner()
        
        # 验证配置
        validation_result = runner.validate_workflow_config(workflow_config_path)
        
        # 验证验证结果
        assert validation_result is not None
        assert "config_path" in validation_result
        assert "is_valid" in validation_result
        assert "errors" in validation_result
        assert "warnings" in validation_result
        assert "summary" in validation_result

    def test_workflow_with_llm_integration(self, workflow_config_path: str, llm_config_path: str):
        """测试工作流与LLM集成"""
        # 创建通用加载器
        loader = UniversalWorkflowLoader()
        
        # 注册自定义节点函数，模拟LLM调用
        def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义开始节点函数，模拟LLM调用"""
            messages = state.get("messages", [])
            input_text = state.get("input", "")
            
            # 模拟LLM响应
            llm_response = f"Qwen2.5-7B模型响应: 收到输入 '{input_text}'，正在处理..."
            
            messages.append({
                "role": "user",
                "content": input_text
            })
            
            messages.append({
                "role": "assistant",
                "content": llm_response
            })
            
            return {
                **state,
                "messages": messages,
                "output": llm_response
            }

        def end_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义结束节点函数"""
            messages = state.get("messages", [])
            output_text = state.get("output", "")
            
            # 模拟最终LLM响应
            final_response = f"Qwen2.5-7B模型最终输出: {output_text}"
            
            messages.append({
                "role": "assistant",
                "content": final_response
            })
            
            return {
                **state,
                "messages": messages,
                "output": final_response
            }

        # 注册函数
        from src.application.workflow.universal_loader import FunctionType
        loader.register_function("start_node", start_node, FunctionType.NODE_FUNCTION)
        loader.register_function("end_node", end_node, FunctionType.NODE_FUNCTION)
        
        # 加载工作流
        workflow = loader.load_from_file(workflow_config_path)
        
        # 执行工作流
        initial_state = {
            "input": "请解释什么是人工智能",
            "messages": []
        }
        
        result = workflow.run(initial_state)
        
        # 验证执行结果
        assert result is not None
        assert "messages" in result
        assert "output" in result
        assert len(result["messages"]) >= 3  # 用户输入、LLM响应、最终输出
        assert "Qwen2.5-7B模型响应" in result["messages"][1]["content"]
        assert "Qwen2.5-7B模型最终输出" in result["output"]

    def test_error_handling(self, workflow_config_path: str):
        """测试错误处理"""
        # 创建工作流运行器
        runner = WorkflowRunner()
        
        # 注册会抛出异常的节点函数
        def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """会抛出异常的节点函数"""
            raise ValueError("测试错误处理")
        
        # 注册错误函数
        from src.application.workflow.universal_loader import FunctionType
        runner.loader.register_function("start_node", error_node, FunctionType.NODE_FUNCTION)
        
        # 执行工作流
        initial_data = {
            "input": "测试错误处理",
            "messages": []
        }
        
        result = runner.run_workflow(workflow_config_path, initial_data)
        
        # 验证错误处理
        assert result.success is False
        assert result.error is not None
        assert "测试错误处理" in result.error

    def test_stream_execution(self, workflow_config_path: str):
        """测试流式执行"""
        # 创建通用加载器
        loader = UniversalWorkflowLoader()
        
        # 注册自定义节点函数
        def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义开始节点函数"""
            messages = state.get("messages", [])
            input_text = state.get("input", "")
            
            messages.append({
                "role": "system",
                "content": f"流式执行开始，输入: {input_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"流式处理: {input_text}"
            }

        def end_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """自定义结束节点函数"""
            messages = state.get("messages", [])
            output_text = state.get("output", "")
            
            messages.append({
                "role": "system",
                "content": f"流式执行完成，输出: {output_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"流式最终输出: {output_text}"
            }

        # 注册函数
        from src.application.workflow.universal_loader import FunctionType
        loader.register_function("start_node", start_node, FunctionType.NODE_FUNCTION)
        loader.register_function("end_node", end_node, FunctionType.NODE_FUNCTION)
        
        # 加载工作流
        workflow = loader.load_from_file(workflow_config_path)
        
        # 流式执行工作流
        initial_state = {
            "input": "流式测试输入",
            "messages": []
        }
        
        results = list(workflow.stream(initial_state))
        
        # 验证流式执行结果
        assert len(results) >= 2  # 至少有开始和结束步骤
        assert "messages" in results[0]
        assert "output" in results[-1]
        assert "流式执行开始" in results[0]["messages"][0]["content"]
        assert "流式最终输出" in results[-1]["output"]


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])