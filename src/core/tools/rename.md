当前命名的问题
命名维度不一致：

内置 - 按位置（内部 vs 外部）
原生 - 按实现方式（直接 API）
MCP - 按协议/标准名称
更合理的命名方案
方案一：按实现位置（推荐）
内置工具 (Builtin) - 项目内实现
集成工具 (Integrated) - 外部API集成
协议工具 (Protocol) - 标准协议（MCP）
优点：维度一致，清晰区分内外部

方案二：按调用方式
本地工具 (Local) - 本地Python函数直接调用
远程工具 (Remote) - 远程API调用
代理工具 (Proxy) - 通过MCP代理调用
优点：从调用者角度清晰

方案三：按技术栈（最简洁）
Python工具（Python native）- 内置
API工具（REST/HTTP）- 原生
MCP工具（MCP protocol）- MCP
优点：技术特征明确，易区分

建议分类：
1.native 2.rest 3.mcp