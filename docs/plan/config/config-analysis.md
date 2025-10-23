 职责现状                                                                                            
                                                                                                      
  - src/sessions/manager.py:164-210：SessionManager 负责会话生命周期、持久化、Git 版本记录，并直接依赖
  WorkflowManager 加载/构建工作流与序列化 AgentState。                                                
  - src/sessions/store.py:76-174：定义文件/内存两类会话存储，实现细节偏基础设施层。                   
  - src/sessions/event_collector.py:97-210 与 player.py:71-155：提供事件收集与回放能力，但事件钩子目前
  仅在会话侧存在。                                                                                    
  - src/workflow/manager.py:162-361：WorkflowManager 负责加载 YAML、构建 LangGraph、运行/流式执行工作 
  流并维护内存级的工作流元数据。                                                                      
  - src/workflow/builder.py:57-199、config.py:74-176 等：聚焦于 YAML 配置解析、节点注册与边连接，未涉 
  及会话状态。                                                                                        
                                                                                                      
  主要问题                                                                                            
                                                                                                      
  - SessionManager.restore_session 只依赖首次创建时缓存的 workflow_id（src/sessions/manager.py:224-   
  231），而 WorkflowManager 的 ID 在进程重启后不会被恢复（src/workflow/manager.py:186-213 会断言 ID 已
  加载）。这会导致会话恢复在常见部署场景中直接失败，说明会话层过度依赖工作流层的内部实现细节。        
  - SessionManager 在创建会话时缓存完整工作流配置快照（src/sessions/manager.py:202-207），与          
  WorkflowManager 内部的配置缓存（src/workflow/manager.py:190-207）形成重复且可能过时的数据源，职责边 
  界模糊。                                                                                            
  - save_session 接口签名仍要求传入 workflow 实例，但实现中完全未使用（src/sessions/manager.py:236-   
  258），暴露出会话层与工作流层之间职责尚未厘清、接口语义不稳定。



  > 关键现状                                                                                            
                                                                                                      
  - src/config/config_system.py:122 将加载、合并、校验、缓存、监听、回调管理等多种职责集中在          
  ConfigSystem，同时直接依赖 src/infrastructure/config_loader.py 与回调管理等内部工具，表现为“应用服务
  + 基础设施”的混合体，超出了单一层的职责范围。                                                       
  - src/config/utils/env_resolver.py:8 和 src/infrastructure/config_loader.py:83 分别实现了环境变量解 
  析，导致同一能力在不同层重复实现，维护成本高且容易出现行为不一致。                                  
  - src/config/utils/file_watcher.py:1 自行封装监听，而 src/infrastructure/config_loader.py:143 已内置
  基于 watchdog 的监听；双重监听不仅重复，也让缓存与回调触发链条难以推断。                            
  - 配置校验逻辑分散：一部分在 src/config/config_validator.py:18，LLM 专用校验又在 src/llm/           
  config_manager.py:34，ConfigSystem 与 LLM 模块形成并行的校验体系，缺乏统一入口。                    
  - src/config/config_validator_tool.py:15 内嵌 CLI 交互逻辑，更适合放在 presentation/cli 或脚本目录；
  当前模块边界模糊。                                                                                  
  - 上层使用方式不统一：TUI 直接走 ConfigSystem，但 CLI (src/presentation/cli/run_command.py:68) 仅调 
  用 IConfigLoader，造成配置能力在不同入口行为不一致。                                                
                                                                                                      
  优化建议                                                                                            
                                                                                                      
  1. 层次重构                                                                                         
      - 将 Pydantic 模型 (src/config/models/*.py) 视为 Domain；                                       
      - 把文件监听、错误恢复、环境变量解析等通用能力迁移到 src/infrastructure/config 下，统一由       
  YamlConfigLoader 暴露；                                                                             
      - 在 Application 层新增 ConfigService，负责 orchestrate Loader/Merger/Validator，提供           
  load_xxx_config 等高层 API，并通过 DI 暴露给其他层。                                                
  2. 归并重复能力                                                                                     
      - 统一使用 YamlConfigLoader 的监听与环境变量解析，废弃 src/config/utils/file_watcher.py、       
  EnvResolver 的重复逻辑，只保留必要扩展点；                                                          
      - 将 ConfigErrorRecovery 与回调管理器迁移为基础设施扩展，并通过配置服务注入使用，避免“工具类”散 
  落。                                                                                                
  3. 一致的校验与缓存策略                                                                             
      - 抽象通用校验接口，由 Application 层的 ConfigService 调用；LLM 专用校验应复用该接口（可在 llm  
  层提供扩展规则），避免双轨制。                                                                      
      - 缓存与热更新应由 Loader 统一维护，ConfigService 仅感知缓存键，减少锁与状态的交叉。            
  4. 入口统一与封装                                                                                   
      - 将 ConfigValidatorTool 移动到 CLI 层（或 scripts），通过依赖注入调用 ConfigService；          
      - 调整 CLI/TUI、Session 管理等调用点，统一依赖 ConfigService，而非直接拿 Loader 或自建流程。    
  5. 配置结构补充                                                                                     
      - 在 ConfigService 中补齐 Workflow/Prompt 等配置的加载接口，与文档约定保持一致；                
      - 对目录命名（如 tool-sets vs tools）建立常量映射，减少硬编码字符串。                           
                                                                                                      
  通过以上梳理，可让配置相关代码重新对齐“基础设施 → 应用服务 → 表现层”的分层要求，减少重复实现和状态分
  散，也方便后续扩展和测试。建议先完成职责分拆，再逐步迁移调用方，保持行为一致。 