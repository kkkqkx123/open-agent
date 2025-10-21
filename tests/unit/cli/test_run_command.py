"""运行命令实现单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from src.presentation.cli.run_command import RunCommand
from src.prompts.agent_state import AgentState, HumanMessage


class TestRunCommand:
    """运行命令测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.run_command = RunCommand(config_path="test_config.yaml", verbose=True)
    
    def test_init(self) -> None:
        """测试初始化"""
        cmd = RunCommand(config_path="test.yaml", verbose=False)
        assert cmd.config_path == "test.yaml"
        assert cmd.verbose is False
        assert hasattr(cmd, 'console')
    
    def test_init_with_defaults(self) -> None:
        """测试默认参数初始化"""
        cmd = RunCommand()
        assert cmd.config_path is None
        assert cmd.verbose is False
        assert hasattr(cmd, 'console')
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_load_agent_config_success(self, mock_container: Mock) -> None:
        """测试成功加载agent配置"""
        # 模拟配置加载器
        mock_config_loader = Mock()
        mock_config_loader.load.return_value = {"name": "test_agent"}
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_config_loader
        mock_container.return_value = mock_container_instance
        
        result = self.run_command._load_agent_config("agent.yaml")
        
        assert result == {"name": "test_agent"}
        mock_config_loader.load.assert_called_once_with("agent.yaml")
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_load_agent_config_failure(self, mock_container: Mock) -> None:
        """测试加载agent配置失败"""
        # 模拟配置加载器抛出异常
        mock_config_loader = Mock()
        mock_config_loader.load.side_effect = Exception("加载失败")
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_config_loader
        mock_container.return_value = mock_container_instance
        
        with patch.object(self.run_command.console, 'print') as mock_print:
            result = self.run_command._load_agent_config("agent.yaml")
            
            assert result is None
            mock_print.assert_called_once()
            # 验证警告消息
            call_args = mock_print.call_args[0][0]
            assert "警告" in call_args
    
    def test_load_agent_config_no_path(self) -> None:
        """测试没有提供agent配置路径"""
        result = self.run_command._load_agent_config(None)
        assert result is None
        
        result = self.run_command._load_agent_config("")
        assert result is None
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_execute_with_new_session(self, mock_container: Mock) -> None:
        """测试执行新会话"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.create_session.return_value = "session123"
        mock_session_manager.restore_session.return_value = (Mock(), Mock())
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        with patch.object(self.run_command, '_load_agent_config') as mock_load:
            with patch.object(self.run_command, '_display_session_info') as mock_display:
                with patch.object(self.run_command, '_run_interactive_loop') as mock_loop:
                    mock_load.return_value = {"name": "test_agent"}
                    
                    self.run_command.execute("workflow.yaml", "agent.yaml", None)
                    
                    mock_session_manager.create_session.assert_called_once_with(
                        workflow_config_path="workflow.yaml",
                        agent_config={"name": "test_agent"}
                    )
                    mock_display.assert_called_once_with("session123", "workflow.yaml")
                    mock_loop.assert_called_once()
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_execute_with_existing_session(self, mock_container: Mock) -> None:
        """测试执行现有会话"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.restore_session.return_value = (Mock(), Mock())
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        with patch.object(self.run_command, '_display_session_info') as mock_display:
            with patch.object(self.run_command, '_run_interactive_loop') as mock_loop:
                self.run_command.execute("workflow.yaml", None, "session123")
                
                mock_session_manager.restore_session.assert_called_once_with("session123")
                mock_session_manager.create_session.assert_not_called()
                mock_display.assert_called_once_with("session123", "workflow.yaml")
                mock_loop.assert_called_once()
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_execute_with_exception(self, mock_container: Mock) -> None:
        """测试执行时抛出异常"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.restore_session.side_effect = Exception("测试异常")
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        with patch.object(self.run_command.console, 'print') as mock_print:
            with pytest.raises(Exception, match="测试异常"):
                self.run_command.execute("workflow.yaml", None, "session123")
            
            # 验证错误消息被打印
            mock_print.assert_called()
            # 检查所有print调用，查找包含"执行失败"的消息
            found_error_message = False
            for call in mock_print.call_args_list:
                if call[0] and "执行失败" in str(call[0][0]):
                    found_error_message = True
                    break
            assert found_error_message, "未找到包含'执行失败'的错误消息"
    
    def test_display_session_info(self) -> None:
        """测试显示会话信息"""
        with patch.object(self.run_command.console, 'print') as mock_print:
            self.run_command._display_session_info("session123", "workflow.yaml")
            
            # 现在只调用一次print
            mock_print.assert_called_once()
            # 验证面板内容 - 检查Panel对象的属性
            call_args = mock_print.call_args[0][0]
            from rich.panel import Panel
            assert isinstance(call_args, Panel)
            # 检查Panel的renderable内容转换为字符串
            renderable_str = str(call_args.renderable)
            assert "session123" in renderable_str
            assert "workflow.yaml" in renderable_str
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_run_interactive_loop(self, mock_container: Mock) -> None:
        """测试运行交互式循环"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_workflow = Mock()
        mock_state = Mock(spec=AgentState)
        mock_state.messages = []
        
        # 模拟用户输入
        with patch.object(self.run_command.console, 'input') as mock_input:
            mock_input.side_effect = ["exit"]  # 立即退出
            
            with patch.object(self.run_command, '_execute_workflow') as mock_execute:
                # 创建一个已完成的Future来避免DeprecationWarning
                loop = asyncio.new_event_loop()
                future = loop.create_future()
                future.set_result(mock_state)
                mock_execute.return_value = future
                loop.close()
                
                self.run_command._run_interactive_loop(
                    "session123", 
                    mock_workflow, 
                    mock_state, 
                    mock_session_manager
                )
                
                # 验证会话被保存
                mock_session_manager.save_session.assert_called()
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_run_interactive_loop_with_user_input(self, mock_container: Mock) -> None:
        """测试交互式循环处理用户输入"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_workflow = Mock()
        mock_state = Mock(spec=AgentState)
        mock_state.messages = []
        mock_state.add_message = Mock()
        
        # 模拟AI回复消息
        mock_ai_message = Mock()
        mock_ai_message.content = "AI回复"
        
        # 模拟用户输入和AI回复
        with patch.object(self.run_command.console, 'input') as mock_input:
            mock_input.side_effect = ["测试消息", "exit"]
            
            with patch.object(self.run_command, '_execute_workflow') as mock_execute:
                # 创建一个返回mock_state的函数，确保messages包含AI消息
                def mock_execute_workflow(*args, **kwargs):
                    mock_state.messages = [mock_ai_message]
                    return mock_state
                
                mock_execute.side_effect = mock_execute_workflow
                
                with patch.object(self.run_command.console, 'print') as mock_print:
                    self.run_command._run_interactive_loop(
                        "session123", 
                        mock_workflow, 
                        mock_state, 
                        mock_session_manager
                    )
                    
                    # 验证用户消息被添加
                    mock_state.add_message.assert_called()
                    # 验证AI回复被打印
                    print_calls = []
                    for call in mock_print.call_args_list:
                        if call[0]:  # 确保有参数
                            print_calls.append(str(call[0][0]))
                    assert any("助手:" in call for call in print_calls)
    
    @patch('src.presentation.cli.run_command.get_global_container')
    def test_run_interactive_loop_keyboard_interrupt(self, mock_container: Mock) -> None:
        """测试交互式循环键盘中断"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_workflow = Mock()
        mock_state = Mock(spec=AgentState)
        
        with patch.object(self.run_command.console, 'input') as mock_input:
            mock_input.side_effect = KeyboardInterrupt()
            
            with patch.object(self.run_command.console, 'print') as mock_print:
                self.run_command._run_interactive_loop(
                    "session123", 
                    mock_workflow, 
                    mock_state, 
                    mock_session_manager
                )
                
                # 验证会话被保存
                mock_session_manager.save_session.assert_called()
                # 验证退出消息被打印
                print_calls = []
                for call in mock_print.call_args_list:
                    if call[0]:  # 确保有参数
                        print_calls.append(str(call[0][0]))
                assert any("保存会话并退出" in call for call in print_calls)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_async_method(self) -> None:
        """测试异步执行工作流（async_run方法）"""
        mock_workflow = Mock()
        mock_workflow.async_run = AsyncMock(return_value="result")
        mock_state = Mock(spec=AgentState)
        
        result = await self.run_command._execute_workflow(mock_workflow, mock_state)
        
        assert result == "result"
        mock_workflow.async_run.assert_called_once_with(mock_state)
    
    def test_execute_workflow_sync_method(self) -> None:
        """测试同步执行工作流（run方法）"""
        mock_workflow = Mock()
        mock_workflow.run = Mock(return_value="result")
        # 不设置async_run属性，这样hasattr检查会失败
        del mock_workflow.async_run
        mock_state = Mock(spec=AgentState)
        
        # 使用asyncio.run测试同步方法
        result = asyncio.run(self.run_command._execute_workflow(mock_workflow, mock_state))
        
        assert result == "result"
        mock_workflow.run.assert_called_once_with(mock_state)
    
    def test_execute_workflow_no_method(self) -> None:
        """测试工作流没有可执行方法"""
        mock_workflow = Mock()
        del mock_workflow.run  # 删除run方法
        del mock_workflow.async_run  # 删除async_run方法
        mock_state = Mock(spec=AgentState)
        
        with patch.object(self.run_command.console, 'print') as mock_print:
            result = asyncio.run(self.run_command._execute_workflow(mock_workflow, mock_state))
            
            assert result is None
            # 验证警告消息被打印
            print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
            assert any("警告" in call for call in print_calls)
    
    def test_execute_workflow_exception(self) -> None:
        """测试工作流执行异常"""
        mock_workflow = Mock()
        mock_workflow.run = Mock(side_effect=Exception("工作流异常"))
        # 不设置async_run属性，确保使用同步方法
        del mock_workflow.async_run
        mock_state = Mock(spec=AgentState)
        
        with patch.object(self.run_command.console, 'print') as mock_print:
            with pytest.raises(Exception, match="工作流异常"):
                asyncio.run(self.run_command._execute_workflow(mock_workflow, mock_state))
            
            # 验证错误消息被打印
            print_calls = []
            for call in mock_print.call_args_list:
                if call[0]:  # 确保有参数
                    print_calls.append(str(call[0][0]))
            assert any("工作流执行失败" in call for call in print_calls)


class TestRunCommandIntegration:
    """运行命令集成测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.run_command = RunCommand()
    
    def test_full_workflow_simulation(self) -> None:
        """测试完整工作流模拟"""
        # 这个测试模拟完整的工作流执行流程
        with patch('src.presentation.cli.run_command.get_global_container') as mock_container:
            # 模拟所有依赖
            mock_session_manager = Mock()
            mock_session_manager.create_session.return_value = "session123"
            mock_session_manager.restore_session.return_value = (Mock(), Mock())
            
            mock_container_instance = Mock()
            mock_container_instance.get.return_value = mock_session_manager
            mock_container.return_value = mock_container_instance
            
            with patch.object(self.run_command, '_load_agent_config') as mock_load:
                with patch.object(self.run_command, '_display_session_info'):
                    with patch.object(self.run_command, '_run_interactive_loop') as mock_loop:
                        mock_load.return_value = {"name": "test_agent"}
                        
                        # 执行命令
                        self.run_command.execute("workflow.yaml", "agent.yaml", None)
                        
                        # 验证所有步骤都被调用
                        mock_load.assert_called_once_with("agent.yaml")
                        mock_session_manager.create_session.assert_called_once()
                        mock_loop.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])