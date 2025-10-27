"""工作流接口测试

测试工作流相关的接口定义。
"""

import unittest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional, List, Generator
from abc import ABC

from src.application.workflow.interfaces import (
    IWorkflowManager, IWorkflowBuilder, IEventCollector,
    IWorkflowExecutor, IWorkflowTemplate, IWorkflowTemplateRegistry
)
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import WorkflowState


class TestIWorkflowManager(unittest.TestCase):
    """测试工作流管理器接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        self.assertTrue(issubclass(IWorkflowManager, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IWorkflowManager()  # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = [
            'load_workflow', 'create_workflow', 'run_workflow',
            'run_workflow_async', 'stream_workflow', 'list_workflows',
            'get_workflow_config', 'unload_workflow', 'get_workflow_visualization',
            'get_workflow_summary'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowManager, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteWorkflowManager(IWorkflowManager):
            def load_workflow(self, config_path: str) -> str:
                return "test_id"
            
            def create_workflow(self, workflow_id: str) -> Any:
                return Mock()
            
            def run_workflow(self, workflow_id: str, initial_state: Optional[WorkflowState] = None, 
                          event_collector: Optional[Any] = None, **kwargs: Any) -> WorkflowState:
                return Mock(spec=WorkflowState)
            
            async def run_workflow_async(self, workflow_id: str, initial_state: Optional[WorkflowState] = None,
                                      event_collector: Optional[Any] = None, **kwargs: Any) -> WorkflowState:
                return Mock(spec=WorkflowState)
            
            def stream_workflow(self, workflow_id: str, initial_state: Optional[WorkflowState] = None,
                             event_collector: Optional[Any] = None, **kwargs: Any) -> Generator[WorkflowState, None, None]:
                yield Mock(spec=WorkflowState)
            
            def list_workflows(self) -> List[str]:
                return ["test_id"]
            
            def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
                return Mock(spec=WorkflowConfig)
            
            def unload_workflow(self, workflow_id: str) -> bool:
                return True
            
            def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
                return {}
            
            def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
                return {}
        
        # 应该能够实例化
        manager = ConcreteWorkflowManager()
        self.assertIsInstance(manager, IWorkflowManager)


class TestIWorkflowBuilder(unittest.TestCase):
    """测试工作流构建器接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        self.assertTrue(issubclass(IWorkflowBuilder, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IWorkflowBuilder()  # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = ['build_graph', 'load_workflow_config', 'validate_config']
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowBuilder, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteWorkflowBuilder(IWorkflowBuilder):
            def build_graph(self, config: WorkflowConfig) -> Any:
                return Mock()
            
            def load_workflow_config(self, config_path: str) -> WorkflowConfig:
                return Mock(spec=WorkflowConfig)
            
            def validate_config(self, config: WorkflowConfig) -> List[str]:
                return []
        
        # 应该能够实例化
        builder = ConcreteWorkflowBuilder()
        self.assertIsInstance(builder, IWorkflowBuilder)


class TestIEventCollector(unittest.TestCase):
    """测试事件收集器接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        self.assertTrue(issubclass(IEventCollector, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IEventCollector()  # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = ['collect_workflow_start', 'collect_workflow_end', 'collect_error']
        
        for method in methods:
            self.assertTrue(hasattr(IEventCollector, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteEventCollector(IEventCollector):
            def collect_workflow_start(self, workflow_name: str, config: Dict[str, Any]) -> None:
                pass
            
            def collect_workflow_end(self, workflow_name: str, result: Dict[str, Any]) -> None:
                pass
            
            def collect_error(self, error: Exception, context: Dict[str, Any]) -> None:
                pass
        
        # 应该能够实例化
        collector = ConcreteEventCollector()
        self.assertIsInstance(collector, IEventCollector)


class TestIWorkflowExecutor(unittest.TestCase):
    """测试工作流执行器接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        self.assertTrue(issubclass(IWorkflowExecutor, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IWorkflowExecutor() # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = ['execute', 'execute_async', 'stream_execute']
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowExecutor, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteWorkflowExecutor(IWorkflowExecutor):
            def execute(self, workflow: Any, initial_state: WorkflowState, **kwargs: Any) -> WorkflowState:
                return Mock(spec=WorkflowState)
            
            async def execute_async(self, workflow: Any, initial_state: WorkflowState, **kwargs: Any) -> WorkflowState:
                return Mock(spec=WorkflowState)
            
            def stream_execute(self, workflow: Any, initial_state: WorkflowState, **kwargs: Any) -> Generator[WorkflowState, None, None]:
                yield Mock(spec=WorkflowState)
        
        # 应该能够实例化
        executor = ConcreteWorkflowExecutor()
        self.assertIsInstance(executor, IWorkflowExecutor)


class TestIWorkflowTemplate(unittest.TestCase):
    """测试工作流模板接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        self.assertTrue(issubclass(IWorkflowTemplate, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IWorkflowTemplate() # type: ignore
    
    def test_interface_properties_and_methods_exist(self):
        """测试接口属性和方法存在"""
        properties = ['name', 'description']
        methods = ['create_template', 'get_parameters', 'validate_parameters']
        
        for prop in properties:
            self.assertTrue(hasattr(IWorkflowTemplate, prop))
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowTemplate, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有属性和方法"""
        class ConcreteWorkflowTemplate(IWorkflowTemplate):
            @property
            def name(self) -> str:
                return "test_template"
            
            @property
            def description(self) -> str:
                return "Test template"
            
            def create_template(self, config: Dict[str, Any]) -> WorkflowConfig:
                return Mock(spec=WorkflowConfig)
            
            def get_parameters(self) -> List[Dict[str, Any]]:
                return []
            
            def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
                return []
        
        # 应该能够实例化
        template = ConcreteWorkflowTemplate()
        self.assertIsInstance(template, IWorkflowTemplate)
        self.assertEqual(template.name, "test_template")
        self.assertEqual(template.description, "Test template")


class TestIWorkflowTemplateRegistry(unittest.TestCase):
    """测试工作流模板注册表接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        self.assertTrue(issubclass(IWorkflowTemplateRegistry, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IWorkflowTemplateRegistry() # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = [
            'register_template', 'get_template', 'list_templates', 'unregister_template'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowTemplateRegistry, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteWorkflowTemplateRegistry(IWorkflowTemplateRegistry):
            def __init__(self):
                self._templates = {}
            
            def register_template(self, template: IWorkflowTemplate) -> None:
                self._templates[template.name] = template
            
            def get_template(self, name: str) -> Optional[IWorkflowTemplate]:
                return self._templates.get(name)
            
            def list_templates(self) -> List[str]:
                return list(self._templates.keys())
            
            def unregister_template(self, name: str) -> bool:
                if name in self._templates:
                    del self._templates[name]
                    return True
                return False
        
        # 应该能够实例化
        registry = ConcreteWorkflowTemplateRegistry()
        self.assertIsInstance(registry, IWorkflowTemplateRegistry)


if __name__ == '__main__':
    unittest.main()