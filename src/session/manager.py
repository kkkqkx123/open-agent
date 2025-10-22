"""会话管理器

负责工作流会话的创建、管理、持久化和恢复。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import uuid
import json
from datetime import datetime

from ..workflow.manager import IWorkflowManager
from ..workflow.config import WorkflowConfig
from ..prompts.agent_state import AgentState
from .store import ISessionStore
from .git_manager import IGitManager


class ISessionManager(ABC):
    """会话管理器接口"""

    @abstractmethod
    def create_session(
        self,
        workflow_config_path: str,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[AgentState] = None
    ) -> str:
        """创建新会话

        Args:
            workflow_config_path: 工作流配置文件路径
            agent_config: Agent配置
            initial_state: 初始状态

        Returns:
            str: 会话ID
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 会话信息，如果不存在则返回None
        """
        pass

    @abstractmethod
    def restore_session(self, session_id: str) -> Tuple[Any, AgentState]:
        """恢复会话

        Args:
            session_id: 会话ID

        Returns:
            Tuple[Any, AgentState]: 工作流实例和状态
        """
        pass

    @abstractmethod
    def save_session(self, session_id: str, workflow: Any, state: AgentState) -> bool:
        """保存会话

        Args:
            session_id: 会话ID
            workflow: 工作流实例
            state: 当前状态

        Returns:
            bool: 是否成功保存
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功删除
        """
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话

        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        pass

    @abstractmethod
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史

        Args:
            session_id: 会话ID

        Returns:
            List[Dict[str, Any]]: 会话历史记录
        """
        pass

    @abstractmethod
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 会话信息，如果不存在则返回None
        """
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            bool: 会话是否存在
        """
        pass


class SessionManager(ISessionManager):
    """会话管理器实现"""

    def __init__(
        self,
        workflow_manager: IWorkflowManager,
        session_store: ISessionStore,
        git_manager: Optional[IGitManager] = None,
        storage_path: Optional[Path] = None
    ) -> None:
        """初始化会话管理器

        Args:
            workflow_manager: 工作流管理器
            session_store: 会话存储
            git_manager: Git管理器（可选）
            storage_path: 存储路径（可选）
        """
        self.workflow_manager = workflow_manager
        self.session_store = session_store
        self.git_manager = git_manager
        self.storage_path = storage_path or Path("./sessions")

        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        workflow_config_path: str,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[AgentState] = None
    ) -> str:
        """创建新会话"""
        # 加载工作流配置
        workflow_id = self.workflow_manager.load_workflow(workflow_config_path)
        workflow = self.workflow_manager.create_workflow(workflow_id)
        
        # 生成符合新命名规则的会话ID
        session_id = self._generate_session_id(workflow_config_path)

        # 准备初始状态
        if initial_state is None:
            initial_state = AgentState()

        # 创建会话目录
        session_dir = self.storage_path / session_id
        session_dir.mkdir(exist_ok=True)

        # 初始化Git仓库（如果提供了Git管理器）
        if self.git_manager:
            self.git_manager.init_repo(session_dir)

        # 保存会话元数据
        session_metadata = {
            "session_id": session_id,
            "workflow_config_path": workflow_config_path,
            "workflow_id": workflow_id,
            "agent_config": agent_config or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }

        # 保存会话信息
        workflow_config = self.workflow_manager.get_workflow_config(workflow_id)
        session_data = {
            "metadata": session_metadata,
            "state": self._serialize_state(initial_state),
            "workflow_config": workflow_config.to_dict() if workflow_config else {}
        }
        self.session_store.save_session(session_id, session_data)

        # 提交初始状态到Git（如果提供了Git管理器）
        if self.git_manager:
            self.git_manager.commit_changes(
                session_dir,
                "初始化会话",
                {"session_id": session_id}
            )

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.session_store.get_session(session_id)

    def restore_session(self, session_id: str) -> Tuple[Any, AgentState]:
        """恢复会话"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            raise ValueError(f"会话 {session_id} 不存在")

        # 重建工作流
        workflow_id = session_data["metadata"]["workflow_id"]
        workflow = self.workflow_manager.create_workflow(workflow_id)

        # 恢复状态
        state = self._deserialize_state(session_data["state"])

        return workflow, state

    def save_session(self, session_id: str, workflow: Any, state: AgentState) -> bool:
        """保存会话"""
        try:
            session_data = self.session_store.get_session(session_id)
            if not session_data:
                return False

            # 更新状态
            session_data["state"] = self._serialize_state(state)
            session_data["metadata"]["updated_at"] = datetime.now().isoformat()

            # 保存会话数据
            self.session_store.save_session(session_id, session_data)

            # 提交更改到Git（如果提供了Git管理器）
            if self.git_manager:
                session_dir = self.storage_path / session_id
                self.git_manager.commit_changes(
                    session_dir,
                    "更新会话状态",
                    {"session_id": session_id}
                )

            return True
        except Exception:
            return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            # 删除存储的会话数据
            self.session_store.delete_session(session_id)

            # 删除会话目录
            session_dir = self.storage_path / session_id
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)

            return True
        except Exception:
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = self.session_store.list_sessions()
        # 按创建时间倒序排列
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        if self.git_manager:
            session_dir = self.storage_path / session_id
            return self.git_manager.get_commit_history(session_dir)
        else:
            # 如果没有Git管理器，返回基本历史
            session_data = self.session_store.get_session(session_id)
            if session_data:
                return [{
                    "timestamp": session_data["metadata"].get("created_at"),
                    "message": "会话创建",
                    "author": "system"
                }, {
                    "timestamp": session_data["metadata"].get("updated_at"),
                    "message": "最后更新",
                    "author": "system"
                }]
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.get_session(session_id)

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return self.get_session(session_id) is not None

    def _serialize_state(self, state: AgentState) -> Dict[str, Any]:
        """序列化状态"""
        return {
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": getattr(msg, "content", ""),
                    "additional_kwargs": getattr(msg, "additional_kwargs", {})
                }
                for msg in state.messages
            ],
            "tool_results": [
                {
                    "tool_name": result.tool_name,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error
                }
                for result in state.tool_results
            ],
            "current_step": getattr(state, "current_step", ""),
            "max_iterations": getattr(state, "max_iterations", 10),
            "iteration_count": getattr(state, "iteration_count", 0),
            "workflow_name": getattr(state, "workflow_name", ""),
            "start_time": state.start_time.isoformat() if state.start_time else None,
            "errors": getattr(state, "errors", [])
        }

    def _deserialize_state(self, state_data: Dict[str, Any]) -> AgentState:
        """反序列化状态"""
        state = AgentState()

        # 恢复消息
        for msg_data in state_data.get("messages", []):
            try:
                # 尝试创建适当的消息类型
                msg_type = msg_data.get("type", "BaseMessage")
                if msg_type == "HumanMessage":
                    from ..prompts.agent_state import HumanMessage
                    msg = HumanMessage(content=msg_data.get("content", ""))
                elif msg_type == "SystemMessage":
                    from ..prompts.agent_state import SystemMessage
                    msg = SystemMessage(content=msg_data.get("content", ""))
                else:
                    from ..prompts.agent_state import BaseMessage
                    msg = BaseMessage(content=msg_data.get("content", ""))

                state.add_message(msg)
            except Exception:
                # 如果创建消息失败，创建基本消息
                from ..prompts.agent_state import BaseMessage
                msg = BaseMessage(content=msg_data.get("content", ""))
                state.add_message(msg)

        # 恢复工具结果
        from ..prompts.agent_state import ToolResult
        for result_data in state_data.get("tool_results", []):
            result = ToolResult(
                tool_name=result_data.get("tool_name", ""),
                success=result_data.get("success", False),
                result=result_data.get("result"),
                error=result_data.get("error")
            )
            state.tool_results.append(result)

        # 恢复其他属性
        state.current_step = state_data.get("current_step", "")
        state.max_iterations = state_data.get("max_iterations", 10)
        state.iteration_count = state_data.get("iteration_count", 0)
        state.workflow_name = state_data.get("workflow_name", "")
        
        # 恢复开始时间
        start_time_str = state_data.get("start_time")
        if start_time_str:
            try:
                state.start_time = datetime.fromisoformat(start_time_str)
            except (ValueError, TypeError):
                state.start_time = None
        else:
            state.start_time = None
            
        # 恢复错误列表
        state.errors = state_data.get("errors", [])
        
        return state

    def _generate_session_id(self, workflow_config_path: str) -> str:
        """生成符合新命名规则的会话ID
        
        格式: workflow名称(全小写)+年月日(如251022)+时分秒+uuid前6位
        例如: react-251022-174800-1f73e8
        
        Args:
            workflow_config_path: 工作流配置文件路径
            
        Returns:
            str: 生成的会话ID
        """
        # 生成基础UUID
        base_uuid = str(uuid.uuid4())
        uuid_prefix = base_uuid[:6]
        
        # 获取当前时间
        now = datetime.now()
        date_str = now.strftime("%y%m%d")  # 年月日，如251022
        time_str = now.strftime("%H%M%S")  # 时分秒，如174800
        
        # 从配置路径提取workflow名称
        workflow_name = self._extract_workflow_name(workflow_config_path)
        
        # 组合生成session_id
        session_id = f"{workflow_name}-{date_str}-{time_str}-{uuid_prefix}"
        return session_id
    
    def _extract_workflow_name(self, workflow_config_path: str) -> str:
        """从工作流配置路径提取workflow名称
        
        Args:
            workflow_config_path: 工作流配置文件路径
            
        Returns:
            str: workflow名称（全小写，无后缀）
        """
        try:
            # 从路径中提取文件名（不含扩展名）
            from pathlib import Path
            config_file = Path(workflow_config_path)
            base_name = config_file.stem  # 不含扩展名的文件名
            
            # 转换为小写并移除下划线和后缀，保持简洁
            # 例如: "react_workflow" -> "react"
            workflow_name = base_name.lower().replace("_", "")
            
            # 移除常见的后缀如"workflow"
            if workflow_name.endswith("workflow"):
                workflow_name = workflow_name[:-8]  # 移除"workflow"(8个字符)
                
            return workflow_name
        except Exception:
            # 如果提取失败，返回默认值
            return "unknown"