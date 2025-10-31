`src/bootstrap.py` 文件是**应用程序启动器**，负责整个应用程序的完整启动流程。其主要作用包括：

## 核心功能
1. **应用启动管理** - 通过 [`ApplicationBootstrap`](src/bootstrap.py:24) 类提供完整的启动生命周期控制

## 启动流程（12个步骤）
1. **加载应用配置** - 使用 [`YamlConfigLoader`](src/bootstrap.py:150) 加载配置文件
2. **环境设置** - 根据配置设置环境变量和特定环境覆盖
3. **日志系统初始化** - 配置日志级别和输出格式
4. **执行启动前钩子** - 如配置验证、信号处理器注册等
3. **配置依赖注入容器** - 使用 [`create_container()`](src/bootstrap.py:235) 创建DI容器
4. **初始化生命周期管理器** - 管理服务生命周期
5. **启动核心服务** - 初始化并启动所有注册的核心服务
6. **注册全局容器** - 使容器实例在全局范围内可用
5. **启动后台任务** - 自动注册工作流模板、Agent类型和工具类型
6. **执行启动后钩子** - 启动后的自定义处理逻辑
7. **执行健康检查** - 验证关键服务是否正常运行
8. **标记运行状态** - 完成启动流程

## 关键特性
- **信号处理** - 注册 [`SIGINT`](src/bootstrap.py:513) 和 [`SIGTERM`](src/bootstrap.py:514) 处理器，实现优雅关闭
- **生命周期管理** - 通过 [`LifecycleManager`](src/bootstrap.py:245) 管理服务启动/停止
- **健康检查** - 验证 [`IConfigLoader`](src/bootstrap.py:264)、[`IWorkflowManager`](src/bootstrap.py:265)、[`ISessionManager`](src/bootstrap.py:266) 等关键服务
- **全局访问** - 提供 [`get_global_bootstrap()`](src/bootstrap.py:557) 函数获取全局启动器实例
- **便捷函数** - [`bootstrap_application()`](src/bootstrap.py:569) 和 [`shutdown_application()`](src/bootstrap.py:582) 简化使用

## 架构作用
该文件作为**应用入口协调器**，连接了配置系统、依赖注入容器、生命周期管理和各个业务模块，确保应用程序能够按照正确的顺序和配置启动运行。