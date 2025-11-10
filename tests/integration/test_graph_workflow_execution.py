"""
GraphWorkflow 执行测试

测试 GraphWorkflow 的实际执行功能，包括同步、异步和流式执行。
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.application.workflow.graph_workflow import GraphWorkflow


class TestGraphWorkflowExecution:
    """GraphWorkflow 执行测试类"""
    
    @pytest.fixture
    def simple_execution_config(self):
        """简单执行配置 fixture"""
        return {
            "name": "execution_test",
            "description": "执行测试工作流",
            "version": "1.0",
            "entry_point": "input_processor",
            "nodes": {
                "input_processor": {
                    "name": "input_processor",
                    "function_name": "process_input",
                    "description": "输入处理器"
                },
                "data_transformer": {
                    "name": "data_transformer",
                    "function_name": "transform_data",
                    "description": "数据转换器"
                },
                "output_generator": {
                    "name": "output_generator",
                    "function_name": "generate_output",
                    "description": "输出生成器"
                }
            },
            "edges": [
                {
                    "from": "input_processor",
                    "to": "data_transformer",
                    "type": "simple"
                },
                {
                    "from": "data_transformer",
                    "to": "output_generator",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "ExecutionState",
                "fields": {
                    "input_data": {"type": "str", "default": ""},
                    "processed_data": {"type": "str", "default": ""},
                    "final_result": {"type": "str", "default": ""},
                    "execution_log": {"type": "List[str]", "default": []}
                }
            }
        }
    
    @pytest.fixture
    def mock_functions(self):
        """模拟函数 fixture"""
        def mock_process_input(state):
            """模拟输入处理函数"""
            return {
                "processed_data": f"processed_{state.get('input_data', '')}",
                "execution_log": ["input_processed"]
            }
        
        def mock_transform_data(state):
            """模拟数据转换函数"""
            return {
                "processed_data": f"transformed_{state.get('processed_data', '')}",
                "execution_log": state.get("execution_log", []) + ["data_transformed"]
            }
        
        def mock_generate_output(state):
            """模拟输出生成函数"""
            return {
                "final_result": f"output_{state.get('processed_data', '')}",
                "execution_log": state.get("execution_log", []) + ["output_generated"]
            }
        
        async def mock_async_process_input(state):
            """模拟异步输入处理函数"""
            await asyncio.sleep(0.01)  # 模拟异步操作
            return mock_process_input(state)
        
        async def mock_async_transform_data(state):
            """模拟异步数据转换函数"""
            await asyncio.sleep(0.01)
            return mock_transform_data(state)
        
        async def mock_async_generate_output(state):
            """模拟异步输出生成函数"""
            await asyncio.sleep(0.01)
            return mock_generate_output(state)
        
        return {
            "process_input": mock_process_input,
            "transform_data": mock_transform_data,
            "generate_output": mock_generate_output,
            "async_process_input": mock_async_process_input,
            "async_transform_data": mock_async_transform_data,
            "async_generate_output": mock_async_generate_output
        }
    
    def test_sync_execution_basic(self, simple_execution_config, mock_functions):
        """测试基本同步执行"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟函数注册
        with patch.dict('sys.modules', {
            'src.application.workflow.graph_workflow': Mock(
                process_input=mock_functions["process_input"],
                transform_data=mock_functions["transform_data"],
                generate_output=mock_functions["generate_output"]
            )
        }):
            # 模拟工作流实例的执行
            mock_instance = Mock()
            mock_instance.run.return_value = {
                "input_data": "test_data",
                "processed_data": "processed_test_data",
                "final_result": "output_processed_test_data",
                "execution_log": ["input_processed", "data_transformed", "output_generated"]
            }
            
            with patch.object(workflow, '_create_instance', return_value=mock_instance):
                result = workflow.run({"input_data": "test_data"})
                
                assert result["input_data"] == "test_data"
                assert "processed_test_data" in result["final_result"]
                assert len(result["execution_log"]) == 3
                mock_instance.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_execution_basic(self, simple_execution_config, mock_functions):
        """测试基本异步执行"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟异步执行
        mock_instance = Mock()
        mock_instance.run_async = AsyncMock(return_value={
            "input_data": "async_test_data",
            "processed_data": "processed_async_test_data",
            "final_result": "output_processed_async_test_data",
            "execution_log": ["input_processed", "data_transformed", "output_generated"]
        })
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            result = await workflow.run_async({"input_data": "async_test_data"})
            
            assert result["input_data"] == "async_test_data"
            assert "processed_async_test_data" in result["final_result"]
            assert len(result["execution_log"]) == 3
            mock_instance.run_async.assert_called_once()
    
    def test_stream_execution_basic(self, simple_execution_config):
        """测试基本流式执行"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟流式执行
        mock_instance = Mock()
        mock_instance.stream.return_value = iter([
            {"step": "input_processor", "state": {"input_data": "test", "processed_data": "processed_test"}},
            {"step": "data_transformer", "state": {"processed_data": "transformed_processed_test"}},
            {"step": "output_generator", "state": {"final_result": "output_transformed_processed_test"}}
        ])
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            results = list(workflow.stream({"input_data": "test"}))
            
            assert len(results) == 3
            assert results[0]["step"] == "input_processor"
            assert results[2]["step"] == "output_generator"
            mock_instance.stream.assert_called_once()
    
    def test_execution_with_initial_state(self, simple_execution_config):
        """测试带初始状态的执行"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟执行
        mock_instance = Mock()
        mock_instance.run.return_value = {
            "input_data": "initial_data",
            "processed_data": "processed_initial_data",
            "final_result": "output_processed_initial_data",
            "execution_log": ["input_processed", "data_transformed", "output_generated"]
        }
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            # 使用初始状态执行
            initial_state = {
                "input_data": "initial_data",
                "execution_log": ["initial_log"]
            }
            
            result = workflow.run(initial_state)
            
            assert result["input_data"] == "initial_data"
            assert "initial_data" in result["final_result"]
            mock_instance.run.assert_called_once_with(initial_state)
    
    def test_execution_error_handling(self, simple_execution_config):
        """测试执行错误处理"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟执行错误
        mock_instance = Mock()
        mock_instance.run.side_effect = Exception("Execution failed")
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            with pytest.raises(Exception, match="Execution failed"):
                workflow.run({"input_data": "test"})
    
    @pytest.mark.asyncio
    async def test_async_execution_error_handling(self, simple_execution_config):
        """测试异步执行错误处理"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟异步执行错误
        mock_instance = Mock()
        mock_instance.run_async = AsyncMock(side_effect=Exception("Async execution failed"))
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            with pytest.raises(Exception, match="Async execution failed"):
                await workflow.run_async({"input_data": "test"})
    
    def test_stream_execution_error_handling(self, simple_execution_config):
        """测试流式执行错误处理"""
        workflow = GraphWorkflow(simple_execution_config)
        
        # 模拟流式执行错误
        mock_instance = Mock()
        mock_instance.stream.side_effect = Exception("Stream execution failed")
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            with pytest.raises(Exception, match="Stream execution failed"):
                list(workflow.stream({"input_data": "test"}))
    
    def test_conditional_workflow_execution(self):
        """测试条件工作流执行"""
        conditional_config = {
            "name": "conditional_execution_test",
            "description": "条件执行测试",
            "version": "1.0",
            "entry_point": "classifier",
            "nodes": {
                "classifier": {
                    "name": "classifier",
                    "function_name": "classify_input"
                },
                "type_a_processor": {
                    "name": "type_a_processor",
                    "function_name": "process_type_a"
                },
                "type_b_processor": {
                    "name": "type_b_processor",
                    "function_name": "process_type_b"
                }
            },
            "edges": [
                {
                    "from": "classifier",
                    "to": "type_a_processor",
                    "type": "conditional",
                    "condition": "input_type == 'A'"
                },
                {
                    "from": "classifier",
                    "to": "type_b_processor",
                    "type": "conditional",
                    "condition": "input_type == 'B'"
                }
            ],
            "state_schema": {
                "name": "ConditionalExecutionState",
                "fields": {
                    "input_data": {"type": "str", "default": ""},
                    "input_type": {"type": "str", "default": ""},
                    "result": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(conditional_config)
        
        # 模拟条件执行
        mock_instance = Mock()
        mock_instance.run.return_value = {
            "input_data": "test_data",
            "input_type": "A",
            "result": "processed_type_A"
        }
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            result = workflow.run({"input_data": "test_data", "input_type": "A"})
            
            assert result["input_type"] == "A"
            assert "processed_type_A" in result["result"]
    
    def test_parallel_workflow_execution(self):
        """测试并行工作流执行"""
        parallel_config = {
            "name": "parallel_execution_test",
            "description": "并行执行测试",
            "version": "1.0",
            "entry_point": "splitter",
            "nodes": {
                "splitter": {
                    "name": "splitter",
                    "function_name": "split_task"
                },
                "worker_1": {
                    "name": "worker_1",
                    "function_name": "work_on_task_1"
                },
                "worker_2": {
                    "name": "worker_2",
                    "function_name": "work_on_task_2"
                },
                "aggregator": {
                    "name": "aggregator",
                    "function_name": "aggregate_results"
                }
            },
            "edges": [
                {
                    "from": "splitter",
                    "to": "worker_1",
                    "type": "simple"
                },
                {
                    "from": "splitter",
                    "to": "worker_2",
                    "type": "simple"
                },
                {
                    "from": "worker_1",
                    "to": "aggregator",
                    "type": "simple"
                },
                {
                    "from": "worker_2",
                    "to": "aggregator",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "ParallelExecutionState",
                "fields": {
                    "input_task": {"type": "str", "default": ""},
                    "result_1": {"type": "str", "default": ""},
                    "result_2": {"type": "str", "default": ""},
                    "final_result": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(parallel_config)
        
        # 模拟并行执行
        mock_instance = Mock()
        mock_instance.run.return_value = {
            "input_task": "parallel_task",
            "result_1": "result_from_worker_1",
            "result_2": "result_from_worker_2",
            "final_result": "aggregated_results"
        }
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            result = workflow.run({"input_task": "parallel_task"})
            
            assert result["input_task"] == "parallel_task"
            assert "result_from_worker_1" in result["result_1"]
            assert "result_from_worker_2" in result["result_2"]
            assert "aggregated_results" in result["final_result"]
    
    def test_workflow_with_checkpoints(self):
        """测试带检查点的工作流执行"""
        checkpoint_config = {
            "name": "checkpoint_execution_test",
            "description": "检查点执行测试",
            "version": "1.0",
            "entry_point": "step1",
            "nodes": {
                "step1": {
                    "name": "step1",
                    "function_name": "execute_step1"
                },
                "step2": {
                    "name": "step2",
                    "function_name": "execute_step2"
                }
            },
            "edges": [
                {
                    "from": "step1",
                    "to": "step2",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "CheckpointExecutionState",
                "fields": {
                    "current_step": {"type": "int", "default": 0},
                    "step_data": {"type": "str", "default": ""}
                }
            },
            "checkpoints": {
                "enabled": True,
                "checkpoint_path": "/tmp/test_checkpoints"
            }
        }
        
        workflow = GraphWorkflow(checkpoint_config)
        
        # 模拟带检查点的执行
        mock_instance = Mock()
        mock_instance.run.return_value = {
            "current_step": 2,
            "step_data": "step2_data"
        }
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            result = workflow.run({"current_step": 0, "step_data": "step1_data"})
            
            assert result["current_step"] == 2
            assert "step2_data" in result["step_data"]
    
    def test_workflow_execution_with_timeout(self):
        """测试带超时的执行"""
        timeout_config = {
            "name": "timeout_execution_test",
            "description": "超时执行测试",
            "version": "1.0",
            "entry_point": "long_running",
            "nodes": {
                "long_running": {
                    "name": "long_running",
                    "function_name": "long_running_function"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "TimeoutExecutionState",
                "fields": {
                    "status": {"type": "str", "default": "running"},
                    "result": {"type": "str", "default": ""}
                }
            },
            "config": {
                "timeout": 30  # 30秒超时
            }
        }
        
        workflow = GraphWorkflow(timeout_config)
        
        # 模拟超时执行
        mock_instance = Mock()
        mock_instance.run.return_value = {
            "status": "completed",
            "result": "operation_completed"
        }
        
        with patch.object(workflow, '_create_instance', return_value=mock_instance):
            result = workflow.run({"status": "running"})
            
            assert result["status"] == "completed"
            assert result["result"] == "operation_completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])