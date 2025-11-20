"""工作流服务"""
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
import asyncio
from src.application.workflow.manager import IWorkflowManager
from src.services.workflow.interfaces import IWorkflowRegistry
from services.workflow.configuration.config_manager import IWorkflowConfigManager
from src.core.workflow.interfaces import IWorkflowVisualizer
from src.infrastructure.graph.states import WorkflowState
from ..data_access.workflow_dao import WorkflowDAO

from ..cache.memory_cache import MemoryCache
from ..cache.cache_manager import CacheManager
from ..models.requests import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowRunRequest
from ..models.responses import WorkflowResponse, WorkflowListResponse, WorkflowExecutionResponse
from ..utils.pagination import paginate_list, calculate_pagination, validate_page_params
from ..utils.serialization import serialize_workflow_data
from ..utils.validation import (
    validate_workflow_id, validate_page_params as validate_page_params_func, validate_sort_params,
    sanitize_string, validate_config_path
)


class WorkflowService:
    """工作流服务"""
    
    def __init__(
        self,
        workflow_manager: IWorkflowManager,
        workflow_registry: IWorkflowRegistry,
        config_manager: IWorkflowConfigManager,
        visualizer: IWorkflowVisualizer,
        workflow_dao: WorkflowDAO,
        cache: MemoryCache,
        cache_manager: Optional['CacheManager'] = None
    ):
        self.workflow_manager = workflow_manager
        self.workflow_registry = workflow_registry
        self.config_manager = config_manager
        self.visualizer = visualizer
        self.workflow_dao = workflow_dao
        self.cache = cache
        self.cache_manager = cache_manager
        
        # 如果提供了缓存管理器，优先使用它
        if cache_manager:
            self.cache = cache_manager
    
    async def list_workflows(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sort_by: str = "loaded_at",
        sort_order: str = "desc"
    ) -> WorkflowListResponse:
        """获取工作流列表"""
        # 验证参数
        is_valid, error_msg = validate_page_params_func(page, page_size)
        if not is_valid:
            raise ValueError(error_msg)
        
        is_valid, error_msg = validate_sort_params(sort_by, sort_order)
        if not is_valid:
            raise ValueError(error_msg or "排序参数无效")
        
        # 检查缓存
        cache_key = f"workflows:list:{page}:{page_size}:{search}:{sort_by}:{sort_order}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return WorkflowListResponse(**cached_result)
        
        # 获取工作流列表
        workflows = await self.workflow_dao.list_workflows(
            limit=page_size * 2,  # 获取更多数据用于过滤和排序
            offset=0
        )
        
        # 应用搜索过滤
        if search:
            search = sanitize_string(search, 100).lower()
            workflows = [
                w for w in workflows 
                if search in w.get("name", "").lower() or
                   search in w.get("description", "").lower()
            ]
        
        # 排序
        reverse = sort_order == "desc"
        workflows.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        
        # 分页
        total = len(workflows)
        paginated_workflows = paginate_list(workflows, page, page_size)
        pagination_info = calculate_pagination(total, page, page_size)
        
        # 转换为响应模型
        workflow_responses = [
            WorkflowResponse(**serialize_workflow_data(workflow))
            for workflow in paginated_workflows
        ]
        
        result = WorkflowListResponse(
            workflows=workflow_responses,
            **pagination_info
        )
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=60)
        
        return result
    
    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """获取特定工作流"""
        if not validate_workflow_id(workflow_id):
            raise ValueError("无效的工作流ID格式")
        
        # 检查缓存
        cache_key = f"workflow:{workflow_id}"
        cached_workflow = await self.cache.get(cache_key)
        if cached_workflow:
            return WorkflowResponse(**cached_workflow)
        
        # 从数据库获取
        workflow_data = await self.workflow_dao.get_workflow(workflow_id)
        if not workflow_data:
            return None
        
        result = WorkflowResponse(**serialize_workflow_data(workflow_data))
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=300)
        
        return result
    
    async def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowResponse:
        """创建新工作流"""
        # 验证配置路径
        if request.config_path and not validate_config_path(request.config_path):
            raise ValueError("无效的配置文件路径")
        
        # 创建工作流数据
        workflow_data = {
            "workflow_id": f"{request.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{''.join(__import__('random').choices('0123456789abcdef', k=8))}",
            "name": request.name,
            "description": request.description,
            "version": request.version,
            "config_path": request.config_path,
            "config_data": request.config_data,
            "loaded_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        
        # 保存到数据库
        await self.workflow_dao.create_workflow(workflow_data)
        
        # 清除列表缓存
        await self.cache.delete("workflows:list:*")
        
        # 返回创建的工作流
        result = await self.get_workflow(str(workflow_data["workflow_id"]))
        if not result:
            raise RuntimeError("创建工作流失败")
        
        return result
    
    async def load_workflow(self, config_path: str) -> str:
        """加载工作流配置"""
        if not validate_config_path(config_path):
            raise ValueError("无效的配置文件路径")
        
        try:
            # 通过配置管理器加载配置
            config_id = self.config_manager.load_config(config_path)
            config = self.config_manager.get_config(config_id)
            
            if not config:
                raise RuntimeError("加载工作流配置失败")
            
            # 注册到注册表
            workflow_def = {
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "config_id": config_id,
                "config_path": config_path,
                "metadata": {
                    "tags": [],
                    "category": "general"
                }
            }
            
            workflow_id = self.workflow_registry.register_workflow(workflow_def)
            
            # 保存到数据库
            workflow_data = {
                "workflow_id": workflow_id,
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "config_path": config_path,
                "config_data": config.model_dump(),
                "loaded_at": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            await self.workflow_dao.create_workflow(workflow_data)
            
            # 清除缓存
            await self.cache.delete("workflows:list:*")
            
            return workflow_id
            
        except Exception as e:
            raise RuntimeError(f"加载工作流失败: {str(e)}")
    
    async def run_workflow(
        self,
        workflow_id: str,
        request: Optional[WorkflowRunRequest] = None
    ) -> WorkflowExecutionResponse:
        """运行工作流"""
        if not validate_workflow_id(workflow_id):
            raise ValueError("无效的工作流ID格式")
        
        # 检查工作流是否存在
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError("工作流不存在")
        
        # 更新使用次数
        await self.workflow_dao.update_workflow_usage(workflow_id)
        
        # 生成执行ID
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{''.join(__import__('random').choices('0123456789abcdef', k=8))}"
        
        started_at = datetime.now()
        
        try:
            # 获取初始状态
            initial_state_dict = request.initial_state if request else None
            # 转换为 WorkflowState
            initial_state = None
            if initial_state_dict:
                initial_state = initial_state_dict  # WorkflowState是TypedDict，直接使用字典
            
            # 运行工作流
            result = self.workflow_manager.run_workflow(
                workflow_id,
                initial_state=initial_state
            )
            
            completed_at = datetime.now()
            
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                result=result.__dict__ if hasattr(result, '__dict__') else {"result": str(result)},
                error=None
            )
            
        except Exception as e:
            completed_at = datetime.now()
            
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status="error",
                started_at=started_at,
                completed_at=completed_at,
                result=None,
                error=str(e)
            )
    
    async def stream_workflow(
        self,
        workflow_id: str,
        request: Optional[WorkflowRunRequest] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式运行工作流"""
        if not validate_workflow_id(workflow_id):
            raise ValueError("无效的工作流ID格式")
        
        # 检查工作流是否存在
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError("工作流不存在")
        
        # 更新使用次数
        await self.workflow_dao.update_workflow_usage(workflow_id)
        
        # 生成执行ID
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{''.join(__import__('random').choices('0123456789abcdef', k=8))}"
        
        started_at = datetime.now()
        
        try:
            # 获取初始状态
            initial_state_dict = request.initial_state if request else None
            # 转换为 WorkflowState
            initial_state = None
            if initial_state_dict:
                initial_state = initial_state_dict  # WorkflowState是TypedDict，直接使用字典
            
            # 流式运行工作流
            for state in self.workflow_manager.stream_workflow(
                workflow_id,
                initial_state=initial_state
            ):
                yield {
                    "type": "state_update",
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "data": state,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 发送完成消息
            yield {
                "type": "completed",
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now().isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # 发送错误消息
            yield {
                "type": "error",
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "error": str(e),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now().isoformat(),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流可视化数据"""
        if not validate_workflow_id(workflow_id):
            raise ValueError("无效的工作流ID格式")
        
        # 检查缓存
        cache_key = f"workflow:viz:{workflow_id}"
        cached_viz = await self.cache.get(cache_key)
        if cached_viz:
            return cached_viz if isinstance(cached_viz, dict) else {}
        
        # 从注册表获取工作流定义
        workflow_def = self.workflow_registry.get_workflow_definition(workflow_id)
        if not workflow_def:
            raise ValueError("工作流不存在")
        
        # 从配置管理器获取配置
        config = self.config_manager.get_config(workflow_def["config_id"])
        if not config:
            raise ValueError("工作流配置不存在")
        
        # 生成可视化数据
        visualization = self.visualizer.generate_visualization(config)
        
        # 缓存结果
        await self.cache.set(cache_key, visualization, ttl=300)
        
        return visualization or {}
    
    async def unload_workflow(self, workflow_id: str) -> bool:
        """卸载工作流"""
        if not validate_workflow_id(workflow_id):
            raise ValueError("无效的工作流ID格式")
        
        # 从工作流管理器卸载
        success = self.workflow_manager.unload_workflow(workflow_id)
        
        if success:
            # 从数据库删除
            await self.workflow_dao.delete_workflow(workflow_id)
            
            # 清除缓存
            await self.cache.delete(f"workflow:{workflow_id}")
            await self.cache.delete(f"workflow:viz:{workflow_id}")
            await self.cache.delete("workflows:list:*")
        
        return success
    
    async def search_workflows(self, query: str) -> List[WorkflowResponse]:
        """搜索工作流"""
        query = sanitize_string(query, 100)
        if not query:
            return []
        
        # 搜索数据库
        workflows = await self.workflow_dao.search_workflows(query)
        
        # 转换为响应模型
        return [
            WorkflowResponse(**serialize_workflow_data(workflow))
            for workflow in workflows
        ]
    
    async def update_workflow(self, workflow_id: str, request: WorkflowUpdateRequest) -> Optional[WorkflowResponse]:
        """更新工作流"""
        if not validate_workflow_id(workflow_id):
            raise ValueError("无效的工作流ID格式")
        
        # 检查工作流是否存在
        existing_workflow = await self.get_workflow(workflow_id)
        if not existing_workflow:
            return None
        
        try:
            # 准备更新数据
            updates = {}
            if request.name is not None:
                updates["name"] = request.name
            if request.description is not None:
                updates["description"] = request.description
            if request.version is not None:
                updates["version"] = request.version
            if request.config_data is not None:
                updates["config_data"] = request.config_data
            
            # 更新数据库
            update_data = {
                "name": request.name or existing_workflow.name,
                "description": request.description if request.description is not None else existing_workflow.description,
                "version": request.version or existing_workflow.version,
                "config_data": request.config_data or existing_workflow.nodes,
                "updated_at": datetime.now().isoformat()
            }
            
            success = await self.workflow_dao.update_workflow(workflow_id, update_data)
            if not success:
                raise RuntimeError("更新工作流数据库失败")
            
            # 更新注册表（如果工作流已注册）
            registry_updates = {}
            if request.name is not None:
                registry_updates["name"] = request.name
            if request.description is not None:
                registry_updates["description"] = request.description
            if request.version is not None:
                registry_updates["version"] = request.version
            
            if registry_updates:
                self.workflow_registry.update_workflow(workflow_id, registry_updates)
            
            # 清除缓存
            await self.cache.delete(f"workflow:{workflow_id}")
            await self.cache.delete(f"workflow:viz:{workflow_id}")
            await self.cache.delete("workflows:list:*")
            
            # 返回更新后的工作流
            return await self.get_workflow(workflow_id)
            
        except Exception as e:
            logger.error(f"更新工作流失败: {workflow_id}, error: {e}")
            raise RuntimeError(f"更新工作流失败: {str(e)}")