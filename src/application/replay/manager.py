"""回放管理器实现"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.domain.history.interfaces import IHistoryManager
from src.application.sessions.manager import ISessionManager
from src.domain.replay.interfaces import (
    IReplayEngine, IReplayAnalyzer, ReplayAnalysis, ReplayConfig, ReplayMode, ReplayFilter
)
from src.infrastructure.replay.config_service import ReplayConfigService

logger = logging.getLogger(__name__)


class IReplayManager:
    """回放管理器接口"""
    
    async def start_replay(
        self, 
        session_id: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """开始回放
        
        Args:
            session_id: 会话ID
            config: 回放配置
            
        Returns:
            str: 回放ID
        """
        pass
    
    async def stop_replay(self, replay_id: str) -> bool:
        """停止回放
        
        Args:
            replay_id: 回放ID
            
        Returns:
            bool: 是否成功停止
        """
        pass
    
    async def get_replay_status(self, replay_id: str) -> Optional[Dict[str, Any]]:
        """获取回放状态
        
        Args:
            replay_id: 回放ID
            
        Returns:
            Optional[Dict[str, Any]]: 回放状态信息
        """
        pass
    
    async def analyze_replay(self, replay_id: str) -> Optional[ReplayAnalysis]:
        """分析回放
        
        Args:
            replay_id: 回放ID
            
        Returns:
            Optional[ReplayAnalysis]: 分析结果
        """
        pass


class ReplayManager(IReplayManager):
    """回放管理器实现"""
    
    def __init__(
        self,
        history_manager: Optional[IHistoryManager] = None,
        session_manager: Optional[ISessionManager] = None,
        replay_engine: Optional[IReplayEngine] = None,
        replay_analyzer: Optional[IReplayAnalyzer] = None,
        config_service: Optional[ReplayConfigService] = None
    ):
        """初始化回放管理器
        
        Args:
            history_manager: 历史管理器
            session_manager: 会话管理器
            replay_engine: 回放引擎
            replay_analyzer: 回放分析器
            config_service: 配置服务
        """
        self.history_manager = history_manager
        self.session_manager = session_manager
        self.replay_engine = replay_engine
        self.replay_analyzer = replay_analyzer
        self.config_service = config_service
        
        # 活跃回放记录
        self.active_replays: Dict[str, Dict[str, Any]] = {}
        
        logger.info("回放管理器初始化完成")
    
    async def start_replay(
        self, 
        session_id: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """开始回放"""
        if not self.replay_engine:
            raise RuntimeError("回放引擎未配置")
        
        # 检查会话是否存在
        if self.session_manager:
            session_exists = await self.session_manager.session_exists(session_id)
            if not session_exists:
                raise ValueError(f"会话不存在: {session_id}")
        
        # 创建回放配置
        replay_config = self._create_replay_config(config or {})
        
        # 启动回放
        replay_id = await self.replay_engine.start_replay(session_id, replay_config)
        
        # 记录活跃回放
        self.active_replays[replay_id] = {
            "session_id": session_id,
            "config": replay_config,
            "started_at": datetime.now(),
            "status": "running"
        }
        
        logger.info(f"回放开始: {replay_id}, 会话: {session_id}")
        return replay_id
    
    async def stop_replay(self, replay_id: str) -> bool:
        """停止回放"""
        if not self.replay_engine:
            return False
        
        # 停止回放
        success = await self.replay_engine.stop_replay(replay_id)
        
        # 更新记录
        if replay_id in self.active_replays:
            self.active_replays[replay_id]["status"] = "stopped"
            self.active_replays[replay_id]["stopped_at"] = datetime.now()
        
        logger.info(f"回放停止: {replay_id}, 成功: {success}")
        return success
    
    async def get_replay_status(self, replay_id: str) -> Optional[Dict[str, Any]]:
        """获取回放状态"""
        # 从活跃回放记录获取
        if replay_id in self.active_replays:
            return self.active_replays[replay_id].copy()
        
        # 从回放引擎获取
        if self.replay_engine:
            session = await self.replay_engine.get_replay_session(replay_id)
            if session:
                return {
                    "session_id": session.session_id,
                    "status": session.status.value,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "progress": getattr(session, 'progress', None)
                }
        
        return None
    
    async def analyze_replay(self, replay_id: str) -> Optional[ReplayAnalysis]:
        """分析回放"""
        if not self.replay_analyzer:
            logger.warning("回放分析器未配置")
            return None
        
        try:
            analysis = await self.replay_analyzer.analyze_replay(replay_id)
            return analysis
        except Exception as e:
            logger.error(f"分析回放失败: {replay_id}, 错误: {e}")
            return None
    
    def _create_replay_config(self, config_dict: Dict[str, Any]) -> ReplayConfig:
        """创建回放配置对象
        
        Args:
            config_dict: 配置字典
            
        Returns:
            ReplayConfig: 回放配置对象
        """
        # 获取模式枚举值
        mode_str = config_dict.get("mode", "real_time")
        try:
            mode = ReplayMode(mode_str)
        except ValueError:
            logger.warning(f"无效的回放模式: {mode_str}, 使用默认值 real_time")
            mode = ReplayMode.REAL_TIME
        
        speed = config_dict.get("speed", 1.0)
        auto_start = config_dict.get("auto_start", True)
        max_events = config_dict.get("max_events")
        enable_analysis = config_dict.get("enable_analysis", False)
        
        # 创建 ReplayFilter 对象
        filters = None
        if "filters" in config_dict:
            filter_dict = config_dict["filters"]
            filters = ReplayFilter(
                start_time=filter_dict.get("start_time"),
                end_time=filter_dict.get("end_time"),
                thread_ids=filter_dict.get("thread_ids"),
                workflow_ids=filter_dict.get("workflow_ids"),
                custom_filters=filter_dict.get("custom_filters")
            )
        
        return ReplayConfig(
            mode=mode,
            speed=speed,
            auto_start=auto_start,
            max_events=max_events,
            enable_analysis=enable_analysis,
            filters=filters,
            export_format=config_dict.get("export_format")
        )