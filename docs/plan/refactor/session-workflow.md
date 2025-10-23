职责现状

- src/sessions/manager.py:164-210：SessionManager 负责会话生命周期、持久化、Git 版本记录，并直接依赖 WorkflowManager 加载/构建工作流与序列化 AgentState。
- src/sessions/store.py:76-174：定义文件/内存两类会话存储，实现细节偏基础设施层。
- src/sessions/event_collector.py:97-210 与 player.py:71-155：提供事件收集与回放能力，但事件钩子目前仅在会话侧存在。
- src/workflow/manager.py:162-361：WorkflowManager 负责加载 YAML、构建 LangGraph、运行/流式执行工作流并维护内存级的工作流元数据。
- src/workflow/builder.py:57-199、config.py:74-176 等：聚焦于 YAML 配置解析、节点注册与边连接，未涉及会话状态。

主要问题

- SessionManager.restore_session 只依赖首次创建时缓存的 workflow_id（src/sessions/manager.py:224-231），而 WorkflowManager 的 ID 在进程重启后不会被恢复（src/workflow/manager.py:186-213 会断言 ID 已加载）。这会导致会话恢复在常见部署场景中直接失败，说明会话层过度依赖工作流层的内部实现细节。
- SessionManager 在创建会话时缓存完整工作流配置快照（src/sessions/manager.py:202-207），与 WorkflowManager 内部的配置缓存（src/workflow/manager.py:190-207）形成重复且可能过时的数据源，职责边界模糊。
- save_session 接口签名仍要求传入 workflow 实例，但实现中完全未使用（src/sessions/manager.py:236-258），暴露出会话层与工作流层之间职责尚未厘清、接口语义不稳定。
- WorkflowEventCollector 及其事件封装仅存在于会话模块（src/sessions/event_collector.py:244-318），workflow 模块没有任何调用。会话层期待捕获节点/LLM 事件，但工作流层并未暴露相应的 Hook，导致过程记录与可视化能力无法落地。

修改建议

1. 稳定会话恢复链路：在 SessionManager.restore_session 中优先依据 workflow_config_path 重新加载工作流，若原 ID 不存在则调用 WorkflowManager.load_workflow 重新生成 ID，再创建实例；同时将会话元数据中的工作流标识改为以 config_path + version 为主键，避免依赖易失的 ID。
2. 精简配置存储职责：为 WorkflowManager 补充按需导出配置摘要的接口（仅返回名称、版本、校验指纹等），SessionManager 只保存引用信息与运行时参数；会话层读取完整配置时通过 WorkflowManager.get_workflow_config 获取，降低配置快照漂移风险。
3. 贯通事件流：在 WorkflowManager.run_workflow/stream_workflow 或 WorkflowBuilder 中注入可选的事件收集器回调，在工作流入口、节点执行前后、LLM/工具调用处触发 WorkflowEventCollector，并由 SessionManager 负责创建带 session_id 的装饰器，真正实现过程记录。
4. 梳理接口语义：将 SessionManager.save_session 的 workflow 参数剔除或改为显式使用（例如从 workflow 提取运行统计写入会话），并考虑把 FileSessionStore 等 IO 实现挪到 src/infrastructure，在会话层仅保留抽象接口以契合分层原则。
5. 后续验证：完成上述调整后，建议优先补充针对会话恢复的集成测试（如基于 tests/integration/test_session_integration.py 制造“重启后恢复”场景），并回归 pytest 全量确认事件写入与工作流执行未回归。