根据代码分析，history模块主要与session集成，但也有与thread集成的机制：

### History模块与Session的集成
1. **主要集成点**：History模块的核心实体（如`BaseHistoryRecord`）和查询条件（`HistoryQuery`）都以`session_id`作为关键字段
   ```python
   # src/core/history/entities.py
   @dataclass
   class BaseHistoryRecord:
       record_id: str
       session_id: str  # 主要关联字段
       workflow_id: Optional[str] = None
       # ...
   ```

2. **查询接口**：`IHistoryManager`接口中的`query_history`方法主要基于`session_id`查询
   ```python
   # src/interfaces/history.py
   @abstractmethod
   async def query_history(self, query: 'HistoryQuery') -> 'HistoryResult':
       """查询历史"""
       pass
   ```

### History模块与Thread的集成
1. **专门的接口方法**：`IHistoryManager`接口中定义了专门的`query_history_by_thread`方法
   ```python
   # src/interfaces/history.py
   @abstractmethod
   async def query_history_by_thread(
       self,
       thread_id: str,
       limit: int = 100,
       offset: int = 0,
       record_type: Optional['RecordType'] = None,
       start_time: Optional[datetime] = None,
       end_time: Optional[datetime] = None,
       model: Optional[str] = None
   ) -> 'HistoryResult':
       """按thread_id查询历史记录"""
   ```

2. **Thread中的历史查询**：`ThreadService`中的`get_thread_history`方法使用`history_manager.query_history_by_thread`方法来获取线程相关的历史记录

### Thread与Session的关联
- 通过`SessionThreadAssociation`实体，系统维护了thread到session的映射关系
- 这使得可以通过thread_id间接查询到相关的session历史

### 结论
**history模块主要与session集成，但也支持与thread集成**。在thread中引入history是合理的，因为：
1. `IHistoryManager`接口已经定义了`query_history_by_thread`方法
2. 实现了通过thread_id查询历史记录的功能
3. Thread和Session之间有明确的关联关系，可以实现thread级别的历史记录查询

因此，在ThreadService中添加history_manager依赖并实现get_thread_history方法是正确的设计，符合系统的整体架构。