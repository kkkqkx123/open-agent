概览
- 推荐把“装配”放在一个独立的 Composition Root（应用启动/wiring 入口），用“配置驱动 + 工厂/Builder + 轻量DI”的组合来完成五层的组装。
- 模式选择建议（按层）：
  - LLM层：抽象工厂 + 单例/享元（按模型名缓存实例）
  - Tool层：适配器 + 工厂 + 注册表
  - Agent层：工厂 + 策略（提示/决策）+ 装饰器（审计/限额/安全）
  - Workflow层：Builder（生成StateGraph）+ 策略（路由/重试）+ 子图组合
  - Session层：工厂（Checkpointer）+ 外观/门面（SessionManager）
- 依赖注入：以“构造器注入”为主，容器只做解析（不做复杂生命周期管理）。注册表作为依赖提供者。

一、装配顺序（从下到上）
1) 读取配置 → 验证Schema（pydantic/jsonschema）
2) LLMFactory 根据 llm 配置创建/缓存模型实例
3) ToolFactory 根据 tools 配置创建工具（把外部SDK用适配器统一成 tool callable）
4) AgentFactory 组合 LLM + Tools + Prompt，产出 Agent 节点/子图
5) WorkflowBuilder 把 Agents 装配成 StateGraph（节点、边、条件、重试、并行等）
6) SessionFactory 创建 Checkpointer，WorkflowBuilder.compile(checkpointer=…) 得到可执行 Graph
7) 通过 SessionManager 暴露统一接口：invoke/astream/update_config 等

二、模式与职责对照（为什么这么选）
- 抽象工厂（LLM）：支持多提供商（OpenAI/Anthropic/本地模型）与参数差异；享元/单例减少重复连接与开销。
- 适配器（Tool）：把各种外部系统（文件、REPL、检索、CI、Git）统一成 LangGraph tool 接口，方便 LLM理解与调用。
- 工厂（Agent）：按配置装配提示词、工具白名单、使用的 LLM 与行为策略，屏蔽实现细节，支持版本/灰度。
- Builder（Workflow）：工作流拓扑天然适合 Builder 构造（节点→边→条件→策略），最终 compile 成 Graph。
- 外观（Session）：把 thread_id、持久化、回放、观测统一起来，降低上层调用复杂度。
- 策略/装饰器：把“路由/停止条件/预算/风控/重试/超时/日志”配置化注入，避免写死在节点里。

三、最小可用的装配骨架（示例）
配置示例（摘录）
```yaml
llm:
  code_model:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.2
  planning_model:
    provider: openai
    model: gpt-4o
    temperature: 0.4

tools:
  - name: python_repl
    impl: tools.python.repl:PythonReplTool
  - name: fs_read
    impl: tools.fs:ReadFile
  - name: fs_write
    impl: tools.fs:WriteFile

agents:
  supervisor:
    prompt: prompts/supervisor.txt
    llm: planning_model
    tools: []
    type: node  # 也可以是 subgraph
  code_writer:
    prompt: prompts/code_writer.txt
    llm: code_model
    tools: [python_repl, fs_read, fs_write]
    type: node
  reviewer:
    prompt: prompts/reviewer.txt
    llm: planning_model
    tools: [fs_read]
    type: node

workflow:
  nodes: [supervisor, code_writer, reviewer]
  edges:
    - {from: START, to: supervisor}
    - {from: code_writer, to: supervisor}
    - {from: reviewer, to: supervisor}
  conditional_edges:
    - from: supervisor
      router: route_decision   # 策略名 or py:path
      targets: {write: code_writer, review: reviewer, finish: END}
  policies:
    retry: [{node: code_writer, times: 2, backoff: exp}]
    timeout: [{node: code_writer, seconds: 60}]

session:
  checkpointer: sqlite
  dsn: "sqlite:///state.db"
```

代码骨架（精简伪代码，Python）
```python
# 1) 依赖容器与注册表
class Registry(dict):
    def register(self, key, obj): self[key] = obj
    def get_required(self, key): 
        if key not in self: raise KeyError(key)
        return self[key]

# 2) LLM 抽象工厂（带缓存/享元）
class LLMFactory:
    def __init__(self, cfg): 
        self.cfg = cfg; self.cache = {}
    def create(self, name:str):
        if name in self.cache: return self.cache[name]
        spec = self.cfg[name]
        client = self._build_client(spec)  # 分发到不同provider
        self.cache[name] = client
        return client
    def _build_client(self, spec):
        # 这里封装OpenAI/Anthropic/本地模型差异
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=spec["model"], temperature=spec.get("temperature", 0.2))

# 3) Tool 工厂 + 适配器加载（importlib 动态加载）
import importlib
class ToolFactory:
    def __init__(self, tools_cfg:list):
        self.registry = {}
        for t in tools_cfg:
            mod, cls = t["impl"].split(":")
            ToolCls = getattr(importlib.import_module(mod), cls)
            self.registry[t["name"]] = ToolCls.from_config(t) if hasattr(ToolCls, "from_config") else ToolCls()
    def get(self, names:list):
        return [self.registry[n] for n in names]

# 4) Agent 工厂（Prompt/LLM/Tools 组合 + 装饰器）
from langchain_core.prompts import ChatPromptTemplate
def load_text(path): return open(path, "r", encoding="utf-8").read()

class AgentFactory:
    def __init__(self, agents_cfg:dict, llms:LLMFactory, tools:ToolFactory):
        self.cfg, self.llms, self.tools = agents_cfg, llms, tools
        self.registry = {}
    def build_all(self):
        for name, spec in self.cfg.items():
            llm = self.llms.create(spec["llm"])
            tools = self.tools.get(spec.get("tools", []))
            prompt = ChatPromptTemplate.from_template(load_text(spec["prompt"]))
            node = self._build_node(name, llm, tools, prompt, spec)
            self.registry[name] = node
        return self.registry
    def _build_node(self, name, llm, tools, prompt, spec):
        # 简单Agent → 单节点；复杂Agent → 返回子图（此处省略）
        from langgraph.prebuilt import create_react_agent
        agent = create_react_agent(llm, tools, prompt=prompt)
        # 可在此套装饰器：日志/限额/审计
        return agent

# 5) Workflow Builder（把 Agents 装到 StateGraph）
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import operator

class AppState(TypedDict):
    messages: List[BaseMessage]
    route: str

class WorkflowBuilder:
    def __init__(self, wf_cfg:dict, agent_nodes:dict):
        self.cfg, self.nodes = wf_cfg, agent_nodes
    def build(self):
        g = StateGraph(AppState)
        # 注册节点
        for n in self.cfg["nodes"]:
            g.add_node(n, self.nodes[n])
        # 起始
        g.add_edge("START", self.cfg["edges"][0]["to"])  # 简化处理
        for e in self.cfg["edges"][1:]:
            g.add_edge(e["from"], e["to"])
        # 条件路由
        for ce in self.cfg.get("conditional_edges", []):
            route_name = ce["router"]
            def router(state):  # 策略可替换
                return state["route"]
            g.add_conditional_edges(ce["from"], router, ce["targets"])
        # 可在此注入重试/超时策略（包装节点或使用policy装饰器）
        return g

# 6) Session 工厂 + 外观
from langgraph.checkpoint.sqlite import SqliteSaver
class SessionFactory:
    def __init__(self, sess_cfg): self.cfg = sess_cfg
    def checkpointer(self):
        if self.cfg["checkpointer"] == "sqlite":
            return SqliteSaver(self.cfg["dsn"])
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

class App:
    def __init__(self, graph, checkpointer): 
        self.graph = graph.compile(checkpointer=checkpointer)
    def invoke(self, user_input, thread_id:str):
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke({"messages": user_input}, config=config)

# 7) Composition Root（应用装配入口）
def build_app(config):
    llm_factory   = LLMFactory(config["llm"])
    tool_factory  = ToolFactory(config["tools"])
    agent_factory = AgentFactory(config["agents"], llm_factory, tool_factory)
    agent_nodes   = agent_factory.build_all()
    wf_builder    = WorkflowBuilder(config["workflow"], agent_nodes)
    graph         = wf_builder.build()
    sess_factory  = SessionFactory(config["session"])
    return App(graph, sess_factory.checkpointer())
```

四、依赖注入与扩展点
- 轻量DI容器：仅做“解析/缓存/生命周期管理（单例/请求级）”，避免引入重量级框架；把“注册表 + 工厂”看作可注入依赖。
- 构造器注入：AgentFactory(agents_cfg, llm_factory, tool_factory) 等，清晰表达依赖。
- 策略/插件注入点：
  - 路由策略（router）：在 workflow.conditional_edges 中用字符串名或 python 路径，运行时 import 注入。
  - 观测/审计：在 AgentFactory._build_node 外层用装饰器（Decorator）包一层 tracing/logging/限额。
  - 安全/沙箱：在 ToolFactory 创建时用适配器强制沙箱（文件白名单、命名空间、资源配额）。
  - 多租户：在 SessionManager 中根据 thread_id/tenant 将 llm 选择、工具配额策略作为可配置项注入 config.configurable。

五、子Agent/子图的装配建议
- 简单 Sub-Agent：仍由 AgentFactory 创建为单节点，WorkflowBuilder 直接 add_node。
- 复杂 Sub-Agent：AgentFactory 返回一个已 compile 的子图节点或一个函数型子图；WorkflowBuilder 把它当作黑盒节点；进入/退出子图的状态映射由 AgentFactory 提供适配函数（Adapter/Mapper）。

六、运行期能力（不改代码的热切换）
- 通过配置文件更新 + 工厂缓存失效（享元清理）实现 LLM/工具替换。
- WorkflowBuilder 支持按版本号/feature flag 选择不同拓扑（AB 实验、灰度）。
- Session 层可在 config.configurable 覆盖某些策略（比如将 route 固定为 reviewer 以重放问题）。

七、常见取舍
- Service Locator vs. 轻量DI：推荐“轻量DI + Registry”，避免全局单例的隐藏依赖。
- 统一 Builder 还是分层 Builder：保持单一 WorkflowBuilder，其他层用 Factory 即可，避免过度工程化。
- Graph 何时 compile：生产环境建议在应用启动时 compile（+ 热更新时重建），执行期仅执行 invoke/astream。

八、一句话落地指南
- 用 Factory 管“点”（LLM、Tools、Agent），用 Builder 管“线”（Workflow→Graph），用轻量DI把配置注入到这些构造器里；在 Session 层用 Facade 把调用与持久化封装起来。这样既配置驱动、可复用，又能在 LangGraph 中稳定地落成可执行的图。