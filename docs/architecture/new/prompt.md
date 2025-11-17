当前项目的src\application
src\domain
src\infrastructure
src\presentation四层结构过于复杂，导致很多功能需要跨越多个层级。分析如何采用更加扁平的目录结构，并给出架构设计方案。要求尽可能保持本项目的高级功能。现在分析tools, llm模块。这2个模块集中于src\infrastructure
src\domain这2个目录，结合configs\llms
configs\tool-sets
configs\tools目录理解现有配置结构。其中configs\tool-sets目录需要把configs\tool-sets\_group.yaml改造为工具组的高一级的封装，方便直接配置给节点。
将分析结果写入docs\architecture\new目录