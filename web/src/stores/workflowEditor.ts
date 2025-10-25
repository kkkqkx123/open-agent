import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { WorkflowNode, WorkflowEdge, WorkflowValidationResult } from '@/types'
import { Node, Edge, addEdge, Connection, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges } from 'reactflow'

// 工作流编辑器状态接口
interface WorkflowEditorState {
  // 工作流ID
  workflowId: string | null
  
  // 节点和边
  nodes: Node[]
  edges: Edge[]
  
  // 选中状态
  selectedNodes: string[]
  selectedEdges: string[]
  
  // 编辑状态
  isDirty: boolean
  isValid: boolean
  validation: WorkflowValidationResult | null
  
  // 视图状态
  viewport: {
    x: number
    y: number
    zoom: number
  }
  
  // 历史记录
  history: {
    past: Array<{ nodes: Node[]; edges: Edge[] }>
    present: { nodes: Node[]; edges: Edge[] }
    future: Array<{ nodes: Node[]; edges: Edge[] }>
  }
  
  // 工具状态
  tools: {
    showMinimap: boolean
    showControls: boolean
    snapToGrid: boolean
    gridEnabled: boolean
  }
  
  // 执行状态
  execution: {
    isRunning: boolean
    currentNode: string | null
    executionPath: string[]
    nodeStates: Record<string, 'pending' | 'running' | 'completed' | 'failed' | 'skipped'>
  }
  
  // 调试状态
  debug: {
    isDebugging: boolean
    breakpoints: Set<string>
    debugData: Record<string, any>
  }
}

// 工作流编辑器操作接口
interface WorkflowEditorActions {
  // 工作流操作
  setWorkflowId: (id: string) => void
  resetWorkflow: () => void
  
  // 节点操作
  setNodes: (nodes: Node[]) => void
  addNode: (node: Node) => void
  updateNode: (id: string, updates: Partial<Node>) => void
  deleteNode: (id: string) => void
  duplicateNode: (id: string) => void
  
  // 边操作
  setEdges: (edges: Edge[]) => void
  addEdge: (connection: Connection) => void
  updateEdge: (id: string, updates: Partial<Edge>) => void
  deleteEdge: (id: string) => void
  
  // 批量操作
  onNodesChange: (changes: NodeChange[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void
  onConnect: (connection: Connection) => void
  
  // 选择操作
  selectNode: (id: string, multi?: boolean) => void
  selectEdge: (id: string, multi?: boolean) => void
  selectAll: () => void
  clearSelection: () => void
  deleteSelected: () => void
  
  // 验证操作
  validate: () => Promise<void>
  setValidation: (validation: WorkflowValidationResult) => void
  
  // 历史操作
  undo: () => void
  redo: () => void
  saveToHistory: () => void
  
  // 视图操作
  setViewport: (viewport: Partial<WorkflowEditorState['viewport']>) => void
  fitView: () => void
  zoomIn: () => void
  zoomOut: () => void
  resetZoom: () => void
  
  // 工具操作
  toggleMinimap: () => void
  toggleControls: () => void
  toggleSnapToGrid: () => void
  toggleGrid: () => void
  
  // 执行操作
  startExecution: () => void
  stopExecution: () => void
  setExecutionState: (nodeId: string, state: WorkflowEditorState['execution']['nodeStates'][string]) => void
  setExecutionPath: (path: string[]) => void
  
  // 调试操作
  startDebugging: () => void
  stopDebugging: () => void
  toggleBreakpoint: (nodeId: string) => void
  setDebugData: (nodeId: string, data: any) => void
  
  // 布局操作
  autoLayout: (type: 'hierarchical' | 'force' | 'circular') => void
  
  // 导入导出
  export: () => { nodes: Node[]; edges: Edge[] }
  import: (data: { nodes: Node[]; edges: Edge[] }) => void
}

// 创建工作流编辑器store
const useWorkflowEditorStore = create<WorkflowEditorState & WorkflowEditorActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // 初始状态
      workflowId: null,
      nodes: [],
      edges: [],
      selectedNodes: [],
      selectedEdges: [],
      isDirty: false,
      isValid: true,
      validation: null,
      viewport: { x: 0, y: 0, zoom: 1 },
      history: {
        past: [],
        present: { nodes: [], edges: [] },
        future: [],
      },
      tools: {
        showMinimap: true,
        showControls: true,
        snapToGrid: false,
        gridEnabled: true,
      },
      execution: {
        isRunning: false,
        currentNode: null,
        executionPath: [],
        nodeStates: {},
      },
      debug: {
        isDebugging: false,
        breakpoints: new Set(),
        debugData: {},
      },

      // 工作流操作
      setWorkflowId: (id) => set({ workflowId: id }),
      
      resetWorkflow: () => set({
        nodes: [],
        edges: [],
        selectedNodes: [],
        selectedEdges: [],
        isDirty: false,
        isValid: true,
        validation: null,
        history: {
          past: [],
          present: { nodes: [], edges: [] },
          future: [],
        },
        execution: {
          isRunning: false,
          currentNode: null,
          executionPath: [],
          nodeStates: {},
        },
        debug: {
          isDebugging: false,
          breakpoints: new Set(),
          debugData: {},
        },
      }),

      // 节点操作
      setNodes: (nodes) => set({ nodes, isDirty: true }),
      
      addNode: (node) => set(state => {
        const newNodes = [...state.nodes, node]
        return { nodes: newNodes, isDirty: true }
      }),
      
      updateNode: (id, updates) => set(state => {
        const newNodes = state.nodes.map(node =>
          node.id === id ? { ...node, ...updates } : node
        )
        return { nodes: newNodes, isDirty: true }
      }),
      
      deleteNode: (id) => set(state => {
        const newNodes = state.nodes.filter(node => node.id !== id)
        const newEdges = state.edges.filter(edge => 
          edge.source !== id && edge.target !== id
        )
        return { 
          nodes: newNodes, 
          edges: newEdges,
          selectedNodes: state.selectedNodes.filter(nodeId => nodeId !== id),
          isDirty: true 
        }
      }),
      
      duplicateNode: (id) => set(state => {
        const nodeToDuplicate = state.nodes.find(node => node.id === id)
        if (!nodeToDuplicate) return state
        
        const newNode: Node = {
          ...nodeToDuplicate,
          id: `${nodeToDuplicate.id}_copy_${Date.now()}`,
          position: {
            x: nodeToDuplicate.position.x + 50,
            y: nodeToDuplicate.position.y + 50,
          },
        }
        
        return {
          nodes: [...state.nodes, newNode],
          isDirty: true,
        }
      }),

      // 边操作
      setEdges: (edges) => set({ edges, isDirty: true }),
      
      addEdge: (connection) => set(state => {
        const newEdge = addEdge(connection, state.edges)
        return { edges: newEdge, isDirty: true }
      }),
      
      updateEdge: (id, updates) => set(state => {
        const newEdges = state.edges.map(edge =>
          edge.id === id ? { ...edge, ...updates } : edge
        )
        return { edges: newEdges, isDirty: true }
      }),
      
      deleteEdge: (id) => set(state => {
        const newEdges = state.edges.filter(edge => edge.id !== id)
        return { 
          edges: newEdges,
          selectedEdges: state.selectedEdges.filter(edgeId => edgeId !== id),
          isDirty: true 
        }
      }),

      // 批量操作
      onNodesChange: (changes) => set(state => {
        const newNodes = applyNodeChanges(changes, state.nodes)
        return { nodes: newNodes, isDirty: true }
      }),
      
      onEdgesChange: (changes) => set(state => {
        const newEdges = applyEdgeChanges(changes, state.edges)
        return { edges: newEdges, isDirty: true }
      }),
      
      onConnect: (connection) => {
        get().addEdge(connection)
      },

      // 选择操作
      selectNode: (id, multi = false) => set(state => {
        if (multi) {
          const selectedNodes = state.selectedNodes.includes(id)
            ? state.selectedNodes.filter(nodeId => nodeId !== id)
            : [...state.selectedNodes, id]
          return { selectedNodes }
        } else {
          return { selectedNodes: [id], selectedEdges: [] }
        }
      }),
      
      selectEdge: (id, multi = false) => set(state => {
        if (multi) {
          const selectedEdges = state.selectedEdges.includes(id)
            ? state.selectedEdges.filter(edgeId => edgeId !== id)
            : [...state.selectedEdges, id]
          return { selectedEdges }
        } else {
          return { selectedEdges: [id], selectedNodes: [] }
        }
      }),
      
      selectAll: () => set(state => ({
        selectedNodes: state.nodes.map(node => node.id),
        selectedEdges: state.edges.map(edge => edge.id),
      })),
      
      clearSelection: () => set({
        selectedNodes: [],
        selectedEdges: [],
      }),
      
      deleteSelected: () => set(state => {
        const newNodes = state.nodes.filter(node => !state.selectedNodes.includes(node.id))
        const newEdges = state.edges.filter(edge => 
          !state.selectedEdges.includes(edge.id) &&
          !state.selectedNodes.includes(edge.source) &&
          !state.selectedNodes.includes(edge.target)
        )
        
        return {
          nodes: newNodes,
          edges: newEdges,
          selectedNodes: [],
          selectedEdges: [],
          isDirty: true,
        }
      }),

      // 验证操作
      validate: async () => {
        // 这里应该调用验证API
        // const validation = await workflowService.validateWorkflow(get().workflowId!)
        // set({ validation, isValid: validation.valid })
      },
      
      setValidation: (validation) => set({ 
        validation, 
        isValid: validation?.valid || false 
      }),

      // 历史操作
      undo: () => set(state => {
        if (state.history.past.length === 0) return state
        
        const previous = state.history.past[state.history.past.length - 1]
        const newPast = state.history.past.slice(0, state.history.past.length - 1)
        const newFuture = [state.history.present, ...state.history.future]
        
        return {
          history: {
            past: newPast,
            present: previous,
            future: newFuture,
          },
          nodes: previous.nodes,
          edges: previous.edges,
          isDirty: true,
        }
      }),
      
      redo: () => set(state => {
        if (state.history.future.length === 0) return state
        
        const next = state.history.future[0]
        const newPast = [...state.history.past, state.history.present]
        const newFuture = state.history.future.slice(1)
        
        return {
          history: {
            past: newPast,
            present: next,
            future: newFuture,
          },
          nodes: next.nodes,
          edges: next.edges,
          isDirty: true,
        }
      }),
      
      saveToHistory: () => set(state => {
        const newPast = [...state.history.past, state.history.present]
        const newPresent = { nodes: state.nodes, edges: state.edges }
        
        return {
          history: {
            past: newPast,
            present: newPresent,
            future: [],
          },
        }
      }),

      // 视图操作
      setViewport: (viewport) => set(state => ({
        viewport: { ...state.viewport, ...viewport }
      })),
      
      fitView: () => {
        // 这里应该调用React Flow的fitView方法
      },
      
      zoomIn: () => set(state => ({
        viewport: { ...state.viewport, zoom: Math.min(state.viewport.zoom * 1.2, 2) }
      })),
      
      zoomOut: () => set(state => ({
        viewport: { ...state.viewport, zoom: Math.max(state.viewport.zoom / 1.2, 0.1) }
      })),
      
      resetZoom: () => set(state => ({
        viewport: { ...state.viewport, zoom: 1 }
      })),

      // 工具操作
      toggleMinimap: () => set(state => ({
        tools: { ...state.tools, showMinimap: !state.tools.showMinimap }
      })),
      
      toggleControls: () => set(state => ({
        tools: { ...state.tools, showControls: !state.tools.showControls }
      })),
      
      toggleSnapToGrid: () => set(state => ({
        tools: { ...state.tools, snapToGrid: !state.tools.snapToGrid }
      })),
      
      toggleGrid: () => set(state => ({
        tools: { ...state.tools, gridEnabled: !state.tools.gridEnabled }
      })),

      // 执行操作
      startExecution: () => set({
        execution: {
          isRunning: true,
          currentNode: null,
          executionPath: [],
          nodeStates: {},
        },
      }),
      
      stopExecution: () => set({
        execution: {
          isRunning: false,
          currentNode: null,
          executionPath: [],
          nodeStates: {},
        },
      }),
      
      setExecutionState: (nodeId, state) => set(state => ({
        execution: {
          ...state.execution,
          nodeStates: {
            ...state.execution.nodeStates,
            [nodeId]: state,
          },
        },
      })),
      
      setExecutionPath: (path) => set(state => ({
        execution: {
          ...state.execution,
          executionPath: path,
        },
      })),

      // 调试操作
      startDebugging: () => set(state => ({
        debug: { ...state.debug, isDebugging: true }
      })),
      
      stopDebugging: () => set(state => ({
        debug: { ...state.debug, isDebugging: false }
      })),
      
      toggleBreakpoint: (nodeId) => set(state => {
        const breakpoints = new Set(state.debug.breakpoints)
        if (breakpoints.has(nodeId)) {
          breakpoints.delete(nodeId)
        } else {
          breakpoints.add(nodeId)
        }
        
        return {
          debug: { ...state.debug, breakpoints }
        }
      }),
      
      setDebugData: (nodeId, data) => set(state => ({
        debug: {
          ...state.debug,
          debugData: {
            ...state.debug.debugData,
            [nodeId]: data,
          },
        },
      })),

      // 布局操作
      autoLayout: (type) => {
        // 这里应该实现自动布局算法
        console.log('自动布局:', type)
      },

      // 导入导出
      export: () => {
        const state = get()
        return { nodes: state.nodes, edges: state.edges }
      },
      
      import: (data) => set({
        nodes: data.nodes,
        edges: data.edges,
        isDirty: true,
      }),
    })),
    {
      name: 'workflow-editor-store',
    }
  )
)

export default useWorkflowEditorStore