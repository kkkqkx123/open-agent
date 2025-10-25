// 导出所有store
export { default as useAppStore } from './app'
export { default as useWorkflowEditorStore } from './workflowEditor'

// 重新导出常用store
import useAppStore from './app'
import useWorkflowEditorStore from './workflowEditor'

export const stores = {
  app: useAppStore,
  workflowEditor: useWorkflowEditorStore,
}

export default stores