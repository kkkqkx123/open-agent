# 工作流可视化模块详细实现方案

## 1. 模块概述

工作流可视化模块是Web前端的核心功能，将TUI中简单的工作流节点树形展示升级为**交互式图形化编辑器**，支持拖拽、连线、节点属性编辑等复杂交互。

## 2. 技术选型

### 2.1 核心库选择
- **React Flow** - 专业的React流程图库
- **D3.js** - 数据可视化增强
- **Framer Motion** - 动画效果
- **React Hook Form** - 表单处理

### 2.2 替代方案对比
| 方案 | 优点 | 缺点 | 选择理由 |
|------|------|------|----------|
| React Flow | 专为React设计，生态完善 | 学习成本较高 | 最适合React生态 |
| AntV X6 | 功能强大，企业级 | 配置复杂，包体积大 | 过度设计 |
| D3.js原生 | 完全自定义 | 开发工作量大 | 不适合快速开发 |
| GoJS | 功能丰富 | 商业授权，成本高 | 开源项目不适用 |

## 3. 架构设计

### 3.1 组件架构
```typescript
// 工作流可视化模块架构
interface WorkflowVisualizationModule {
  // 核心组件
  WorkflowEditor: React.FC<WorkflowEditorProps>
  NodePalette: React.FC<NodePaletteProps>
  PropertyPanel: React.FC<PropertyPanelProps>
  
  // 工具组件
  WorkflowToolbar: React.FC<ToolbarProps>
  MiniMap: React.FC<MiniMapProps>
  NodeTypes: Record<string, NodeComponent>
  
  // 服务层
  WorkflowService: WorkflowServiceInterface
  NodeService: NodeServiceInterface
  LayoutService: LayoutServiceInterface
}
```

### 3.2 数据模型设计

```typescript
// 工作流节点模型
interface WorkflowNode {
  id: string
  type: NodeType
  position: { x: number; y: number }
  data: NodeData
  style?: NodeStyle
  sourcePosition?: Position
  targetPosition?: Position
}

// 节点数据模型
interface NodeData {
  label: string
  description?: string
  parameters: Record<string, any>
  config: NodeConfig
  metadata: NodeMetadata
}

// 节点配置模型
interface NodeConfig {
  inputs: InputPort[]
  outputs: OutputPort[]
  properties: PropertyField[]
  validation: ValidationRule[]
}

// 工作流连接模型
interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  type?: EdgeType
  animated?: boolean
  style?: EdgeStyle
  data?: EdgeData
}
```

## 4. 核心功能实现

### 4.1 工作流编辑器

```typescript
// WorkflowEditor.tsx
import React, { useCallback, useMemo, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'

interface WorkflowEditorProps {
  workflowId?: string
  initialNodes?: Node[]
  initialEdges?: Edge[]
  onSave?: (nodes: Node[], edges: Edge[]) => void
  onNodeSelect?: (node: Node | null) => void
}

const WorkflowEditor: React.FC<WorkflowEditorProps> = ({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onSave,
  onNodeSelect,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  // 节点连接处理
  const onConnect = useCallback(
    (params: Connection) => setEdges(eds => addEdge(params, eds)),
    [setEdges]
  )

  // 节点选择处理
  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
    onNodeSelect?.(node)
  }, [onNodeSelect])

  // 节点拖拽处理
  const onNodeDragStop = useCallback((event: React.MouseEvent, node: Node) => {
    // 更新节点位置
    setNodes(nds => nds.map(n => n.id === node.id ? node : n))
  }, [setNodes])

  // 自定义节点类型
  const nodeTypes = useMemo(() => ({
    start: StartNode,
    process: ProcessNode,
    decision: DecisionNode,
    tool: ToolNode,
    end: EndNode,
    error: ErrorNode,
  }), [])

  // 自定义边类型
  const edgeTypes = useMemo(() => ({
    default: SmoothStepEdge,
    conditional: ConditionalEdge,
    loop: LoopEdge,
  }), [])

  return (
    <div className="workflow-editor" style={{ height: '100%', width: '100%' }}>
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls position="top-right" />
          <MiniMap position="bottom-right" />
          <Background color="#f0f2f5" gap={16} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  )
}
```

### 4.2 自定义节点组件

```typescript
// 开始节点组件
const StartNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`start-node ${selected ? 'selected' : ''}`}>
      <div className="node-header">
        <RocketOutlined className="node-icon" />
        <span className="node-label">{data.label}</span>
      </div>
      <Handle type="source" position={Position.Right} className="node-handle" />
    </div>
  )
}

// 处理节点组件
const ProcessNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`process-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} className="node-handle" />
      <div className="node-content">
        <SettingOutlined className="node-icon" />
        <div className="node-info">
          <div className="node-label">{data.label}</div>
          {data.description && (
            <div className="node-description">{data.description}</div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="node-handle" />
    </div>
  )
}

// 决策节点组件
const DecisionNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`decision-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} className="node-handle" />
      <div className="node-content">
        <ForkOutlined className="node-icon" />
        <div className="node-label">{data.label}</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="node-handle" id="yes" />
      <Handle type="source" position={Position.Right} className="node-handle" id="no" />
    </div>
  )
}

// 工具节点组件
const ToolNode: React.FC<NodeProps> = ({ data, selected }) => {
  const [isExecuting, setIsExecuting] = useState(false)
  
  return (
    <div className={`tool-node ${selected ? 'selected' : ''} ${isExecuting ? 'executing' : ''}`}>
      <Handle type="target" position={Position.Left} className="node-handle" />
      <div className="node-content">
        <ToolOutlined className="node-icon" />
        <div className="node-info">
          <div className="node-label">{data.label}</div>
          <div className="node-type">{data.toolType}</div>
        </div>
        {isExecuting && <LoadingOutlined className="executing-icon" spin />}
      </div>
      <Handle type="source" position={Position.Right} className="node-handle" />
    </div>
  )
}
```

### 4.3 节点调色板

```typescript
// NodePalette.tsx
interface NodePaletteProps {
  onNodeAdd: (nodeType: string) => void
}

const NodePalette: React.FC<NodePaletteProps> = ({ onNodeAdd }) => {
  const nodeTypes = [
    { type: 'start', label: '开始', icon: <RocketOutlined />, color: '#52c41a' },
    { type: 'process', label: '处理', icon: <SettingOutlined />, color: '#1890ff' },
    { type: 'decision', label: '决策', icon: <ForkOutlined />, color: '#faad14' },
    { type: 'tool', label: '工具', icon: <ToolOutlined />, color: '#722ed1' },
    { type: 'end', label: '结束', icon: <CheckCircleOutlined />, color: '#f5222d' },
  ]

  const handleDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="node-palette">
      <div className="palette-header">
        <h3>节点类型</h3>
      </div>
      <div className="palette-content">
        {nodeTypes.map(node => (
          <div
            key={node.type}
            className="palette-item"
            draggable
            onDragStart={(e) => handleDragStart(e, node.type)}
            style={{ borderLeftColor: node.color }}
          >
            <div className="palette-icon" style={{ color: node.color }}>
              {node.icon}
            </div>
            <span className="palette-label">{node.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

### 4.4 属性面板

```typescript
// PropertyPanel.tsx
interface PropertyPanelProps {
  selectedNode: Node | null
  onNodeUpdate: (nodeId: string, data: NodeData) => void
}

const PropertyPanel: React.FC<PropertyPanelProps> = ({ 
  selectedNode, 
  onNodeUpdate 
}) => {
  const [form] = Form.useForm()

  useEffect(() => {
    if (selectedNode) {
      form.setFieldsValue({
        label: selectedNode.data.label,
        description: selectedNode.data.description,
        ...selectedNode.data.parameters
      })
    }
  }, [selectedNode, form])

  const handleValuesChange = (changedValues: any, allValues: any) => {
    if (selectedNode) {
      onNodeUpdate(selectedNode.id, {
        ...selectedNode.data,
        label: allValues.label,
        description: allValues.description,
        parameters: { ...allValues }
      })
    }
  }

  if (!selectedNode) {
    return (
      <div className="property-panel-empty">
        <Empty description="请选择一个节点" />
      </div>
    )
  }

  return (
    <div className="property-panel">
      <div className="panel-header">
        <h3>节点属性</h3>
        <Tag color="blue">{selectedNode.type}</Tag>
      </div>
      
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        autoComplete="off"
      >
        <Form.Item
          label="节点名称"
          name="label"
          rules={[{ required: true, message: '请输入节点名称' }]}
        >
          <Input placeholder="输入节点名称" />
        </Form.Item>

        <Form.Item
          label="描述"
          name="description"
        >
          <TextArea 
            rows={3} 
            placeholder="输入节点描述"
          />
        </Form.Item>

        {/* 动态属性字段 */}
        <DynamicPropertyFields nodeType={selectedNode.type} />
      </Form>
    </div>
  )
}
```

## 5. 高级功能实现

### 5.1 自动布局算法

```typescript
// LayoutService.ts
class LayoutService {
  // 层次布局
  static hierarchicalLayout(nodes: Node[], edges: Edge[]): { nodes: Node[], edges: Edge[] } {
    const levels = this.calculateNodeLevels(nodes, edges)
    const levelNodes = this.groupNodesByLevel(levels)
    
    let yOffset = 0
    const updatedNodes = nodes.map(node => {
      const level = levels.get(node.id) || 0
      const levelNodeCount = levelNodes.get(level)?.length || 1
      const nodeIndex = levelNodes.get(level)?.indexOf(node.id) || 0
      
      return {
        ...node,
        position: {
          x: level * 300 + 100,
          y: yOffset + (nodeIndex * 150) + 50
        }
      }
    })
    
    return { nodes: updatedNodes, edges }
  }

  // 力导向布局
  static forceDirectedLayout(nodes: Node[], edges: Edge[]): { nodes: Node[], edges: Edge[] } {
    // 使用D3.js力导向算法
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges).id((d: any) => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(400, 300))
      .force('collision', d3.forceCollide().radius(50))
    
    // 运行模拟并获取最终位置
    simulation.tick(300)
    
    return { nodes, edges }
  }

  // 计算节点层次
  private static calculateNodeLevels(nodes: Node[], edges: Edge[]): Map<string, number> {
    const levels = new Map<string, number>()
    const visited = new Set<string>()
    const queue: Array<{ id: string, level: number }> = []
    
    // 找到开始节点
    const startNodes = nodes.filter(n => n.type === 'start')
    startNodes.forEach(node => {
      levels.set(node.id, 0)
      queue.push({ id: node.id, level: 0 })
    })
    
    // BFS遍历
    while (queue.length > 0) {
      const { id, level } = queue.shift()!
      visited.add(id)
      
      // 找到所有子节点
      const childEdges = edges.filter(e => e.source === id)
      childEdges.forEach(edge => {
        if (!visited.has(edge.target)) {
          const childLevel = level + 1
          levels.set(edge.target, childLevel)
          queue.push({ id: edge.target, level: childLevel })
        }
      })
    }
    
    return levels
  }
}
```

### 5.2 执行路径动画

```typescript
// ExecutionPathAnimation.tsx
interface ExecutionPathAnimationProps {
  executionPath: string[]
  nodes: Node[]
  edges: Edge[]
  currentStep: number
}

const ExecutionPathAnimation: React.FC<ExecutionPathAnimationProps> = ({
  executionPath,
  nodes,
  edges,
  currentStep
}) => {
  const [animatedNodes, setAnimatedNodes] = useState<Node[]>(nodes)
  const [animatedEdges, setAnimatedEdges] = useState<Edge[]>(edges)

  useEffect(() => {
    if (executionPath.length === 0) return

    // 高亮当前执行路径
    const updatedNodes = nodes.map(node => ({
      ...node,
      className: executionPath.includes(node.id) ? 'executing' : '',
      style: {
        ...node.style,
        opacity: currentStep >= executionPath.indexOf(node.id) ? 1 : 0.5
      }
    }))

    // 高亮执行边
    const updatedEdges = edges.map(edge => {
      const sourceIndex = executionPath.indexOf(edge.source)
      const targetIndex = executionPath.indexOf(edge.target)
      
      return {
        ...edge,
        animated: sourceIndex !== -1 && targetIndex !== -1 && targetIndex === sourceIndex + 1,
        style: {
          ...edge.style,
          stroke: targetIndex === sourceIndex + 1 ? '#52c41a' : '#d9d9d9',
          strokeWidth: targetIndex === sourceIndex + 1 ? 3 : 1
        }
      }
    })

    setAnimatedNodes(updatedNodes)
    setAnimatedEdges(updatedEdges)
  }, [executionPath, nodes, edges, currentStep])

  return null // 这个组件只负责更新节点和边的样式
}
```

### 5.3 节点调试面板

```typescript
// NodeDebugger.tsx
interface NodeDebuggerProps {
  selectedNode: Node | null
  executionData: ExecutionData
  onDebugAction: (action: DebugAction) => void
}

const NodeDebugger: React.FC<NodeDebuggerProps> = ({
  selectedNode,
  executionData,
  onDebugAction
}) => {
  const [breakpoints, setBreakpoints] = useState<Set<string>>(new Set())
  const [isDebugging, setIsDebugging] = useState(false)

  const toggleBreakpoint = (nodeId: string) => {
    const newBreakpoints = new Set(breakpoints)
    if (newBreakpoints.has(nodeId)) {
      newBreakpoints.delete(nodeId)
    } else {
      newBreakpoints.add(nodeId)
    }
    setBreakpoints(newBreakpoints)
  }

  const handleDebugAction = (action: DebugAction) => {
    onDebugAction(action)
  }

  if (!selectedNode) {
    return (
      <div className="node-debugger-empty">
        <Empty description="请选择一个节点进行调试" />
      </div>
    )
  }

  return (
    <div className="node-debugger">
      <div className="debugger-header">
        <h3>节点调试器</h3>
        <div className="debugger-controls">
          <Button
            icon={<PlayCircleOutlined />}
            onClick={() => handleDebugAction({ type: 'continue' })}
            disabled={!isDebugging}
          >
            继续
          </Button>
          <Button
            icon={<StepForwardOutlined />}
            onClick={() => handleDebugAction({ type: 'step' })}
            disabled={!isDebugging}
          >
            单步
          </Button>
          <Button
            icon={<PauseCircleOutlined />}
            onClick={() => handleDebugAction({ type: 'pause' })}
          >
            暂停
          </Button>
        </div>
      </div>

      <Tabs defaultActiveKey="input">
        <TabPane tab="输入数据" key="input">
          <CodeEditor
            language="json"
            value={JSON.stringify(executionData.input, null, 2)}
            readOnly
          />
        </TabPane>
        <TabPane tab="输出数据" key="output">
          <CodeEditor
            language="json"
            value={JSON.stringify(executionData.output, null, 2)}
            readOnly
          />
        </TabPane>
        <TabPane tab="执行日志" key="logs">
          <LogViewer logs={executionData.logs} />
        </TabPane>
        <TabPane tab="性能指标" key="metrics">
          <MetricsViewer metrics={executionData.metrics} />
        </TabPane>
      </Tabs>
    </div>
  )
}
```

## 6. 样式系统设计

### 6.1 节点样式系统

```scss
// workflow-nodes.scss
.workflow-editor {
  .react-flow__node {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    
    &.selected {
      box-shadow: 0 0 0 2px #1890ff, 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    &.executing {
      animation: pulse 1.5s ease-in-out infinite;
    }
  }
  
  // 开始节点
  .start-node {
    background: linear-gradient(135deg, #52c41a, #73d13d);
    color: white;
    padding: 12px 16px;
    min-width: 80px;
    text-align: center;
    
    .node-icon {
      font-size: 20px;
      margin-bottom: 4px;
    }
    
    .node-label {
      font-weight: 600;
      font-size: 14px;
    }
  }
  
  // 处理节点
  .process-node {
    background: white;
    border: 2px solid #1890ff;
    padding: 12px 16px;
    min-width: 120px;
    
    .node-content {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .node-icon {
      color: #1890ff;
      font-size: 18px;
    }
    
    .node-label {
      font-weight: 500;
      color: #262626;
    }
    
    .node-description {
      font-size: 12px;
      color: #8c8c8c;
      margin-top: 2px;
    }
  }
  
  // 决策节点
  .decision-node {
    background: white;
    border: 2px solid #faad14;
    transform: rotate(45deg);
    padding: 16px;
    min-width: 80px;
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .node-content {
      transform: rotate(-45deg);
      text-align: center;
    }
    
    .node-icon {
      color: #faad14;
      font-size: 16px;
      margin-bottom: 4px;
    }
    
    .node-label {
      font-weight: 500;
      color: #262626;
      font-size: 12px;
    }
  }
  
  // 工具节点
  .tool-node {
    background: white;
    border: 2px solid #722ed1;
    padding: 12px 16px;
    min-width: 120px;
    
    .node-content {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .node-icon {
      color: #722ed1;
      font-size: 18px;
    }
    
    .node-label {
      font-weight: 500;
      color: #262626;
    }
    
    .node-type {
      font-size: 11px;
      color: #8c8c8c;
      margin-top: 2px;
    }
    
    .executing-icon {
      margin-left: 8px;
      color: #722ed1;
    }
  }
  
  // 连接线样式
  .react-flow__edge {
    .react-flow__edge-path {
      stroke: #8c8c8c;
      stroke-width: 2;
      transition: all 0.3s ease;
    }
    
    &.selected .react-flow__edge-path {
      stroke: #1890ff;
      stroke-width: 3;
    }
    
    &.animated .react-flow__edge-path {
      stroke-dasharray: 10;
      animation: dash 1s linear infinite;
    }
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(24, 144, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0);
  }
}

@keyframes dash {
  to {
    stroke-dashoffset: -20;
  }
}
```

## 7. 性能优化

### 7.1 虚拟化优化

```typescript
// 大型工作流虚拟化
const VirtualizedWorkflowEditor: React.FC<VirtualizedWorkflowProps> = ({
  nodes,
  edges,
  viewport
}) => {
  const visibleNodes = useMemo(() => {
    return nodes.filter(node => {
      const isInViewport = 
        node.position.x >= viewport.x - 100 &&
        node.position.x <= viewport.x + viewport.width + 100 &&
        node.position.y >= viewport.y - 100 &&
        node.position.y <= viewport.y + viewport.height + 100
      
      return isInViewport
    })
  }, [nodes, viewport])

  return (
    <ReactFlow
      nodes={visibleNodes}
      edges={edges}
      // 其他配置...
    />
  )
}
```

### 7.2 渲染优化

```typescript
// 节点渲染优化
const OptimizedNode = React.memo(({ data, selected }: NodeProps) => {
  // 使用useMemo缓存计算结果
  const nodeStyle = useMemo(() => ({
    backgroundColor: data.color,
    borderColor: selected ? '#1890ff' : data.borderColor
  }), [data.color, data.borderColor, selected])

  return (
    <div style={nodeStyle} className="optimized-node">
      {/* 节点内容 */}
    </div>
  )
}, (prevProps, nextProps) => {
  // 自定义比较函数，只比较必要的属性
  return prevProps.data.label === nextProps.data.label &&
         prevProps.selected === nextProps.selected
})
```

这个详细的工作流可视化模块实现方案提供了完整的技术架构、组件设计和性能优化策略，确保实现一个功能强大且用户体验优秀的工作流编辑器。