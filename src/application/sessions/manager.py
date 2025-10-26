"""会话管理器

负责工作流会话的创建、管理、持久化和恢复。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import uuid
import json
import hashlib
import logging
from datetime import datetime

from ..workflow.manager import IWorkflowManager
from ...domain.workflow.config import WorkflowConfig
from ...application.workflow.state import AgentState
from ...domain.sessions.store import ISessionStore
from .git_manager import IGitManager

# 设置日志
logger = logging.getLogger(__name__)


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
    def save_session(self, session_id: str, state: AgentState) -> bool:
        """保存会话

        Args:
            session_id: 会话ID
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

    @abstractmethod
    def save_session_with_metrics(self, session_id: str, state: AgentState, 
                                 workflow_metrics: Dict[str, Any]) -> bool:
        """保存会话状态和工作流指标

        Args:
            session_id: 会话ID
            state: 当前状态
            workflow_metrics: 工作流指标

        Returns:
            bool: 是否成功保存
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
        self._recovery_attempts: Dict[str, int] = {}

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
        workflow_config = self.workflow_manager.get_workflow_config(workflow_id)
        
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

        # 获取工作流摘要
        workflow_summary = self.workflow_manager.get_workflow_summary(workflow_id)
        
        # 保存增强的会话元数据
        session_metadata = {
            "session_id": session_id,
            "workflow_config_path": workflow_config_path,
            "workflow_summary": workflow_summary,  # 只保存摘要
            "agent_config": agent_config or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }

        # 保存会话信息
        session_data = {
            "metadata": session_metadata,
            "state": self._serialize_state(initial_state)
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
        """改进的会话恢复方法"""
        try:
            session_data = self.session_store.get_session(session_id)
            if not session_data:
                raise ValueError(f"会话 {session_id} 不存在")
            
            metadata = session_data["metadata"]
            config_path = metadata["workflow_config_path"]
            
            # 检查配置文件是否存在
            if not Path(config_path).exists():
                raise FileNotFoundError(f"工作流配置文件不存在: {config_path}")
            
            # 使用改进的恢复策略
            return self._restore_workflow_with_fallback(metadata, session_data)
            
        except Exception as e:
            logger.error(f"会话恢复失败: session_id={session_id}, error={e}")
            # 记录详细的恢复失败信息
            self._log_recovery_failure(session_id, e)
            raise

    def save_session(self, session_id: str, state: AgentState) -> bool:
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

            # 清理恢复尝试记录
            if session_id in self._recovery_attempts:
                del self._recovery_attempts[session_id]

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
                }]
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.get_session(session_id)

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return self.get_session(session_id) is not None

    def save_session_with_metrics(self, session_id: str, state: AgentState, 
                                 workflow_metrics: Dict[str, Any]) -> bool:
        """保存会话状态和工作流指标"""
        try:
            session_data = self.session_store.get_session(session_id)
            if not session_data:
                return False

            # 更新状态
            session_data["state"] = self._serialize_state(state)
            session_data["metadata"]["updated_at"] = datetime.now().isoformat()
            
            # 添加工作流指标
            if "workflow_metrics" not in session_data:
                session_data["workflow_metrics"] = {}
            session_data["workflow_metrics"].update(workflow_metrics)

            # 保存会话数据
            self.session_store.save_session(session_id, session_data)

            # 提交更改到Git（如果提供了Git管理器）
            if self.git_manager:
                session_dir = self.storage_path / session_id
                self.git_manager.commit_changes(
                    session_dir,
                    "更新会话状态和指标",
                    {"session_id": session_id}
                )

            return True
        except Exception:
            return False

    def _restore_workflow_with_fallback(self, metadata: Dict[str, Any], session_data: Dict[str, Any]) -> Tuple[Any, AgentState]:
        """带回退机制的工作流恢复"""
        session_id = metadata.get("session_id", "unknown")
        config_path = metadata["workflow_config_path"]
        
        # 策略1: 优先使用配置路径重新加载
        try:
            workflow_id = self.workflow_manager.load_workflow(config_path)
            workflow = self.workflow_manager.create_workflow(workflow_id)
            
            # 验证配置一致性
            if not self._validate_workflow_consistency(metadata, workflow_id):
                logger.warning(f"工作流配置已变更，使用新配置恢复会话 {session_id}")
                
            # 恢复状态
            state = self._deserialize_state(session_data["state"])
            
            # 重置恢复尝试计数
            if session_id in self._recovery_attempts:
                del self._recovery_attempts[session_id]
                
            return workflow, state
            
        except Exception as e:
            # 策略2: 回退到工作流摘要中的workflow_id（如果存在）
            logger.warning(f"基于配置路径恢复失败，尝试使用工作流摘要中的workflow_id: {e}")
            try:
                workflow_summary = metadata.get("workflow_summary", {})
                original_workflow_id = workflow_summary.get("workflow_id")
                if original_workflow_id:
                    workflow = self.workflow_manager.create_workflow(original_workflow_id)
                    
                    # 恢复状态
                    state = self._deserialize_state(session_data["state"])
                    
                    # 重置恢复尝试计数
                    if session_id in self._recovery_attempts:
                        del self._recovery_attempts[session_id]
                        
                    return workflow, state
                else:
                    raise ValueError("工作流摘要中未找到workflow_id")
                    
            except Exception as e2:
                # 策略3: 最终回退 - 重新加载并更新元数据
                logger.error(f"会话恢复失败，尝试重新创建工作流: {e2}")
                try:
                    workflow_id = self.workflow_manager.load_workflow(config_path)
                    workflow = self.workflow_manager.create_workflow(workflow_id)
                    
                    # 更新会话元数据
                    self._update_session_workflow_info(session_id, workflow_id)
                    
                    # 恢复状态
                    state = self._deserialize_state(session_data["state"])
                    
                    # 重置恢复尝试计数
                    if session_id in self._recovery_attempts:
                        del self._recovery_attempts[session_id]
                        
                    return workflow, state
                    
                except Exception as e3:
                    # 所有策略都失败
                    logger.error(f"所有恢复策略都失败: {e3}")
                    raise ValueError(f"无法恢复会话 {session_id}: 所有恢复策略都失败")

    def _validate_workflow_consistency(self, metadata: Dict[str, Any], workflow_id: str) -> bool:
        """验证工作流配置一致性"""
        current_config = self.workflow_manager.get_workflow_config(workflow_id)
        if not current_config:
            return False
        
        # 获取当前工作流摘要
        current_summary = self.workflow_manager.get_workflow_summary(workflow_id)
        if not current_summary:
            return False
        
        # 获取保存的工作流摘要
        saved_summary = metadata.get("workflow_summary", {})
        
        # 检查版本
        if saved_summary.get("version") != current_config.version:
            return False
        
        # 检查配置校验和
        return saved_summary.get("checksum") == current_summary.get("checksum")

    def _calculate_config_checksum(self, config_path: str) -> str:
        """计算配置文件校验和"""
        try:
            with open(config_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"计算配置文件校验和失败: {config_path}, error: {e}")
            return ""

    def _update_session_workflow_info(self, session_id: str, new_workflow_id: str) -> None:
        """更新会话中的工作流信息"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return
        
        workflow_summary = self.workflow_manager.get_workflow_summary(new_workflow_id)
        session_data["metadata"].update({
            "workflow_summary": workflow_summary,
            "updated_at": datetime.now().isoformat(),
            "recovery_info": {
                "recovered_at": datetime.now().isoformat(),
                "original_workflow_id": session_data["metadata"].get("workflow_summary", {}).get("workflow_id"),
                "reason": "workflow_recovery"
            }
        })
        
        self.session_store.save_session(session_id, session_data)

    def _log_recovery_failure(self, session_id: str, error: Exception) -> None:
        """记录恢复失败信息"""
        recovery_attempts = self._get_recovery_attempts(session_id) + 1
        self._recovery_attempts[session_id] = recovery_attempts
        
        recovery_log = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "recovery_attempts": recovery_attempts
        }
        
        # 保存恢复日志
        self._save_recovery_log(recovery_log)

    def _get_recovery_attempts(self, session_id: str) -> int:
        """获取恢复尝试次数"""
        return self._recovery_attempts.get(session_id, 0)

    def _save_recovery_log(self, recovery_log: Dict[str, Any]) -> None:
        """保存恢复日志"""
        try:
            log_dir = self.storage_path / "recovery_logs"
            log_dir.mkdir(exist_ok=True)
            
            session_id = recovery_log["session_id"]
            log_file = log_dir / f"{session_id}_recovery.log"
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(recovery_log, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"保存恢复日志失败: {e}")

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
                role_str = msg_data.get("role", "human")
                from ...application.workflow.state import MessageRole
                try:
                    role = MessageRole(role_str)
                except ValueError:
                    role = MessageRole.HUMAN

                if msg_type == "HumanMessage":
                    from src.application.workflow.state import HumanMessage
                    msg = HumanMessage(content=msg_data.get("content", ""))
                elif msg_type == "SystemMessage":
                    from src.application.workflow.state import SystemMessage
                    msg = SystemMessage(content=msg_data.get("content", ""))
                elif msg_type == "AIMessage":
                    from src.application.workflow.state import AIMessage
                    msg = AIMessage(content=msg_data.get("content", ""))
                elif msg_type == "ToolMessage":
                    from src.application.workflow.state import ToolMessage
                    msg = ToolMessage(content=msg_data.get("content", ""))
                else:
                    from src.application.workflow.state import BaseMessage
                    msg = BaseMessage(content=msg_data.get("content", ""), role=role)

                state.add_message(msg)
            except Exception:
                # 如果创建消息失败，创建基本消息
                from ...application.workflow.state import BaseMessage, MessageRole
                role_str = msg_data.get("role", "human")
                try:
                    role = MessageRole(role_str)
                except ValueError:
                    role = MessageRole.HUMAN
                msg = BaseMessage(content=msg_data.get("content", ""), role=role)
                state.add_message(msg)

        # 恢复工具结果
        from src.application.workflow.state import ToolResult
        for result_data in state_data.get("tool_results", []):
            result = ToolResult(
                tool_name=result_data.get("tool_name", ""),
                success=result_data.get("success", False),
                output=result_data.get("result"),
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
            # 检查路径是否为空
            if not workflow_config_path or not workflow_config_path.strip():
                return "unknown"
                
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