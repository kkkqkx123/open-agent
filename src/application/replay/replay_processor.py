"""回放处理器实现"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, AsyncIterator, List
from datetime import datetime
from src.domain.replay.interfaces import (
    IReplayEngine, IReplaySource, IReplayStrategy,
    ReplayEvent, ReplaySession, ReplayConfig, ReplayMode, ReplayStatus, EventType
)
from src.domain.replay.config import ReplayConfig as ReplayConfigModel
from src.infrastructure.replay.config_service import ReplayConfigService
from src.infrastructure.replay.strategies import ReplayStrategyFactory
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ReplayProcessor(IReplayEngine):
    """回放处理器实现"""
    
    def __init__(
        self,
        replay_source: IReplaySource,
        config_service: ReplayConfigService,
        cache_manager: Optional[EnhancedCacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化回放处理器
        
        Args:
            replay_source: 回放数据源
            config_service: 配置服务
            cache_manager: 缓存管理器
            performance_monitor: 性能监控器
        """
        self.replay_source = replay_source
        self.config_service = config_service
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        
        # 活跃回放会话
        self.active_replays: Dict[str, ReplaySession] = {}
        self.replay_tasks: Dict[str, asyncio.Task] = {}
        
        # 策略缓存
        self._strategy_cache: Dict[ReplayMode, IReplayStrategy] = {}
        
        logger.info("回放处理器初始化完成")
    
    async def start_replay(
        self, 
        session_id: str, 
        config: ReplayConfig
    ) -> str:
        """开始回放
        
        Args:
            session_id: 会话ID
            config: 回放配置
            
        Returns:
            str: 回放会话ID
        """
        operation_id = self.monitor.start_operation("start_replay")
        
        try:
            # 检查配置
            if not self.config_service.is_enabled():
                raise RuntimeError("重放功能未启用")
            
            # 检查并发限制
            processor_config = self.config_service.get_processor_config()
            max_concurrent = processor_config["max_concurrent_replays"]
            
            if len(self.active_replays) >= max_concurrent:
                raise RuntimeError(f"已达到最大并发回放数限制: {max_concurrent}")
            
            # 生成回放会话ID
            replay_id = f"replay_{uuid.uuid4().hex[:8]}"
            
            # 创建回放会话
            replay_session = ReplaySession(
                id=replay_id,
                session_id=session_id,
                mode=config.mode,
                status=ReplayStatus.PENDING,
                config=config.__dict__,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 注册回放会话
            self.active_replays[replay_id] = replay_session
            
            # 缓存回放会话
            if self.cache:
                await self.cache.set(
                    f"replay_session:{replay_id}",
                    replay_session.__dict__,
                    ttl=processor_config["session_timeout"]
                )
            
            # 启动回放任务
            if config.auto_start:
                task = asyncio.create_task(self._run_replay(replay_id))
                self.replay_tasks[replay_id] = task
            
            self.monitor.end_operation(
                operation_id, "start_replay", True,
                {"replay_id": replay_id, "session_id": session_id}
            )
            
            logger.info(f"回放会话创建成功: {replay_id}")
            return replay_id
            
        except Exception as e:
            logger.error(f"开始回放失败: {e}")
            self.monitor.end_operation(
                operation_id, "start_replay", False,
                {"error": str(e)}
            )
            raise
    
    async def get_replay_stream(self, replay_id: str):
        """获取回放事件流
        
        Args:
            replay_id: 回放会话ID
            
        Yields:
            ReplayEvent: 回放事件
        """
        # 检查回放会话是否存在
        replay_session = self.active_replays.get(replay_id)
        if not replay_session:
            raise ValueError(f"回放会话不存在: {replay_id}")
        
        # 如果回放还未开始，启动它
        if replay_session.status == ReplayStatus.PENDING:
            task = asyncio.create_task(self._run_replay(replay_id))
            self.replay_tasks[replay_id] = task
        
        # 等待回放开始
        while replay_session.status == ReplayStatus.PENDING:
            await asyncio.sleep(0.1)
        
        # 从缓存获取事件流
        if self.cache:
            cache_key = f"replay_events:{replay_id}"
            while True:
                # 检查回放是否完成
                if replay_session.status in [ReplayStatus.COMPLETED, ReplayStatus.ERROR, ReplayStatus.STOPPED]:
                    break
                
                # 从缓存获取事件
                events = await self.cache.get(cache_key)
                if events:
                    for event_data in events:
                        yield self._deserialize_event(event_data)
                
                await asyncio.sleep(0.1)
    
    async def pause_replay(self, replay_id: str) -> bool:
        """暂停回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            bool: 是否成功暂停
        """
        replay_session = self.active_replays.get(replay_id)
        if not replay_session:
            return False
        
        if replay_session.status == ReplayStatus.RUNNING:
            replay_session.status = ReplayStatus.PAUSED
            replay_session.updated_at = datetime.now()
            
            # 更新缓存
            if self.cache:
                await self.cache.set(
                    f"replay_session:{replay_id}",
                    replay_session.__dict__
                )
            
            logger.info(f"回放已暂停: {replay_id}")
            return True
        
        return False
    
    async def resume_replay(self, replay_id: str) -> bool:
        """恢复回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            bool: 是否成功恢复
        """
        replay_session = self.active_replays.get(replay_id)
        if not replay_session:
            return False
        
        if replay_session.status == ReplayStatus.PAUSED:
            replay_session.status = ReplayStatus.RUNNING
            replay_session.updated_at = datetime.now()
            
            # 更新缓存
            if self.cache:
                await self.cache.set(
                    f"replay_session:{replay_id}",
                    replay_session.__dict__
                )
            
            logger.info(f"回放已恢复: {replay_id}")
            return True
        
        return False
    
    async def stop_replay(self, replay_id: str) -> bool:
        """停止回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            bool: 是否成功停止
        """
        replay_session = self.active_replays.get(replay_id)
        if not replay_session:
            return False
        
        # 更新状态
        replay_session.status = ReplayStatus.STOPPED
        replay_session.updated_at = datetime.now()
        replay_session.completed_at = datetime.now()
        
        # 取消任务
        if replay_id in self.replay_tasks:
            task = self.replay_tasks[replay_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.replay_tasks[replay_id]
        
        # 更新缓存
        if self.cache:
            await self.cache.set(
                f"replay_session:{replay_id}",
                replay_session.__dict__
            )
        
        logger.info(f"回放已停止: {replay_id}")
        return True
    
    async def get_replay_session(self, replay_id: str) -> Optional[ReplaySession]:
        """获取回放会话信息
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            Optional[ReplaySession]: 回放会话信息
        """
        # 先从内存获取
        replay_session = self.active_replays.get(replay_id)
        if replay_session:
            return replay_session
        
        # 从缓存获取
        if self.cache:
            session_data = await self.cache.get(f"replay_session:{replay_id}")
            if session_data:
                return self._deserialize_session(session_data)
        
        return None
    
    async def list_active_replays(self) -> List[ReplaySession]:
        """列出活跃的回放会话
        
        Returns:
            List[ReplaySession]: 活跃回放会话列表
        """
        return list(self.active_replays.values())
    
    async def _run_replay(self, replay_id: str):
        """运行回放任务
        
        Args:
            replay_id: 回放会话ID
        """
        replay_session = self.active_replays.get(replay_id)
        if not replay_session:
            return
        
        try:
            # 更新状态为运行中
            replay_session.status = ReplayStatus.RUNNING
            replay_session.started_at = datetime.now()
            replay_session.updated_at = datetime.now()
            
            # 获取配置
            config_dict = replay_session.config
            config = ReplayConfig(
                mode=ReplayMode(config_dict["mode"]),
                speed=config_dict.get("speed", 1.0),
                auto_start=config_dict.get("auto_start", False),
                max_events=config_dict.get("max_events"),
                enable_analysis=config_dict.get("enable_analysis", False)
            )
            
            # 获取策略
            strategy = await self._get_strategy(config.mode)
            
            # 获取事件流
            event_count = 0
            async for event in self.replay_source.get_events(
                replay_session.session_id,
                config.filters
            ):
                # 检查是否被暂停
                while replay_session.status == ReplayStatus.PAUSED:
                    await asyncio.sleep(0.1)
                
                # 检查是否被停止
                if replay_session.status == ReplayStatus.STOPPED:
                    break
                
                # 处理事件
                processed_event = await strategy.process_event(event, config.__dict__)
                
                # 检查是否应该暂停
                if await strategy.should_pause(processed_event, config.__dict__):
                    replay_session.status = ReplayStatus.PAUSED
                
                # 获取延迟
                delay = await strategy.get_delay(processed_event, config.__dict__)
                if delay > 0:
                    await asyncio.sleep(delay)
                
                # 缓存事件
                if self.cache:
                    cache_key = f"replay_events:{replay_id}"
                    existing_events = await self.cache.get(cache_key) or []
                    existing_events.append(self._serialize_event(processed_event))
                    await self.cache.set(cache_key, existing_events, ttl=300)
                
                # 更新进度
                event_count += 1
                if config.max_events and event_count >= config.max_events:
                    break
                
                # 更新进度
                replay_session.progress = min(1.0, event_count / 1000.0)  # 假设总事件数为1000
                replay_session.updated_at = datetime.now()
            
            # 标记为完成
            if replay_session.status == ReplayStatus.RUNNING:
                replay_session.status = ReplayStatus.COMPLETED
                replay_session.completed_at = datetime.now()
                replay_session.progress = 1.0
            
        except Exception as e:
            logger.error(f"回放执行失败: {e}")
            replay_session.status = ReplayStatus.ERROR
            replay_session.error_message = str(e)
            replay_session.completed_at = datetime.now()
        
        finally:
            # 清理任务
            if replay_id in self.replay_tasks:
                del self.replay_tasks[replay_id]
            
            # 更新缓存
            if self.cache:
                await self.cache.set(
                    f"replay_session:{replay_id}",
                    replay_session.__dict__
                )
    
    async def _get_strategy(self, mode: ReplayMode) -> IReplayStrategy:
        """获取回放策略
        
        Args:
            mode: 回放模式
            
        Returns:
            IReplayStrategy: 回放策略
        """
        if mode not in self._strategy_cache:
            # 获取模式配置
            mode_config = self.config_service.get_mode_config(mode.value)
            
            # 创建配置对象
            if mode == ReplayMode.REAL_TIME:
                from src.domain.replay.config import RealTimeConfig
                config_obj = RealTimeConfig(**mode_config)
            elif mode == ReplayMode.FAST_FORWARD:
                from src.domain.replay.config import FastForwardConfig
                config_obj = FastForwardConfig(**mode_config)
            elif mode == ReplayMode.STEP_BY_STEP:
                from src.domain.replay.config import StepByStepConfig
                config_obj = StepByStepConfig(**mode_config)
            elif mode == ReplayMode.ANALYSIS:
                from src.domain.replay.config import AnalysisConfig
                config_obj = AnalysisConfig(**mode_config)
            else:
                raise ValueError(f"不支持的回放模式: {mode}")
            
            # 创建策略
            strategy = ReplayStrategyFactory.create_strategy(mode, config_obj)
            self._strategy_cache[mode] = strategy
        
        return self._strategy_cache[mode]
    
    def _serialize_event(self, event: ReplayEvent) -> Dict[str, Any]:
        """序列化事件
        
        Args:
            event: 事件对象
            
        Returns:
            Dict[str, Any]: 序列化后的事件
        """
        return {
            "id": event.id,
            "type": event.type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data,
            "metadata": event.metadata,
            "session_id": event.session_id,
            "thread_id": event.thread_id,
            "workflow_id": event.workflow_id
        }
    
    def _deserialize_event(self, data: Dict[str, Any]) -> ReplayEvent:
        """反序列化事件
        
        Args:
            data: 序列化的事件数据
            
        Returns:
            ReplayEvent: 事件对象
        """
        event_type_value = data["type"]
        # 尝试转换为 EventType，如果失败则默认为 INFO
        try:
            event_type = EventType(event_type_value)
        except (ValueError, KeyError):
            event_type = EventType.INFO
        
        return ReplayEvent(
            id=data["id"],
            type=event_type,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            metadata=data["metadata"],
            session_id=data["session_id"],
            thread_id=data.get("thread_id"),
            workflow_id=data.get("workflow_id")
        )
    
    def _deserialize_session(self, data: Dict[str, Any]) -> ReplaySession:
        """反序列化会话
        
        Args:
            data: 序列化的会话数据
            
        Returns:
            ReplaySession: 会话对象
        """
        return ReplaySession(
            id=data["id"],
            session_id=data["session_id"],
            mode=ReplayMode(data["mode"]),
            status=ReplayStatus(data["status"]),
            config=data["config"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            progress=data.get("progress", 0.0)
        )