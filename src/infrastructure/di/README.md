核心作用
这是一个依赖注入（DI）配置文件，负责组织和管理 Thread（线程）与 Session（会话）相关组件的创建和生命周期。

主要职责
1. ThreadSessionDIConfig 类（配置层）
配置管理：接收并管理存储路径、存储模式、Git 功能开关等配置参数
组件工厂方法：提供一系列 create_* 方法来创建各个组件
create_langgraph_adapter() - LangGraph 适配器（工作流执行）
create_thread_metadata_store() - Thread 元数据存储（文件或内存）
create_checkpoint_manager() - Checkpoint 管理器（状态保存）
create_thread_manager() - Thread 管理器（核心）
create_session_store() - Session 存储（文件或内存）
create_git_manager() - Git 管理器（版本控制，可选）
create_session_manager() - Session 管理器（核心）
完整栈创建：create_complete_stack() 按依赖顺序创建所有组件并返回字典
2. ThreadSessionFactory 类（工厂层）
单例缓存：实现组件的单例模式，确保各组件在应用生命周期内只创建一次
便捷获取：提供 get_* 方法供外部代码获取已缓存的组件
缓存管理：支持 clear_cache() 清空缓存（主要用于测试）
3. 环境差异化配置（工厂函数）
create_development_stack() - 开发环境：文件存储 + 真实 Git
create_testing_stack() - 测试环境：内存存储 + 模拟 Git
create_production_stack() - 生产环境：文件存储 + 真实 Git
4. 全局工厂管理（便捷 API）
get_default_factory() - 获取全局默认工厂实例
get_thread_manager() / get_session_manager() / get_langgraph_adapter() - 便捷方法
initialize_thread_session_system() - 系统初始化入口
设计模式
ThreadSessionDIConfig（配置）
    ↓
ThreadSessionFactory（缓存单例）
    ↓
便捷函数 API
    ↓
使用者代码
组件依赖关系
LangGraphAdapter → ThreadManager → SessionManager
                      ↓
            MetadataStore + CheckpointManager
SessionManager → SessionStore + GitManager
应用场景
在应用启动时调用 initialize_thread_session_system() 初始化整个系统
在代码中通过便捷方法 get_session_manager() 获取 Session 管理器
支持不同环境（开发/测试/生产）的快速切换配置