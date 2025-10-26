"""Plan-Execute Agent实现"""

from typing import Any, Dict, List
from .base import BaseAgent
from .state import AgentState
from ...infrastructure.graph.state import BaseMessage
from src.domain.tools.interfaces import ToolResult
from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
from src.domain.tools.interfaces import ToolCall
from .events import AgentEvent


class PlanExecuteAgent(BaseAgent):
    """实现Plan-and-Execute算法的Agent
    Plan-and-Execute算法先制定计划，然后逐步执行计划
    """
    
    async def _execute_logic(self, state: Any, config: Dict[str, Any]) -> Any:
        """执行Plan-and-Execute算法"""
        # 1. 根据目标制定计划
        plan = await self._create_plan(state)
        
        # 发布计划创建事件
        self.event_manager.publish(AgentEvent.DECISION_MADE, {
            "agent_id": self.config.name,
            "decision_type": "plan_created",
            "plan": plan,
            "state": state
        })
        
        # 2. 逐步执行计划
        execution_result = await self._execute_plan(state, plan)
        
        # 3. 监控执行结果
        # 4. 必要时调整计划
        return execution_result
    
    def can_handle(self, state: AgentState) -> bool:
        """判断Agent是否能处理当前状态"""
        # Plan-Execute Agent适合需要复杂规划的任务
        return True
    
    async def _create_plan(self, state: AgentState) -> List[Dict[str, Any]]:
        """根据目标创建计划"""
        # 构建规划请求
        planning_prompt = f"""
        Based on the following information, create a detailed plan to achieve the goal:
        
        Current task: {state.current_task}
        Available tools: {self.config.tools}
        Available tool sets: {self.config.tool_sets}
        Context: {state.context}
        
        Please provide a step-by-step plan in JSON format:
        [
            {{
                "step": 1,
                "description": "...",
                "tool": "...",
                "expected_result": "..."
            }},
            ...
        ]
        """
        
        messages = [
            SystemMessage(content=f"System: {self.config.system_prompt}"),
            HumanMessage(content=planning_prompt)
        ]
        
        try:
            response = await self.llm_client.generate_async(messages)
            plan_str = response.content.strip()
            
            # 在实际实现中，需要解析JSON格式的计划
            # 这里简化为返回一个模拟计划
            return [
                {
                    "step": 1,
                    "description": "Execute the plan step",
                    "tool": "default_tool",
                    "expected_result": "Plan executed successfully"
                }
            ]
        except Exception as e:
            # 记录错误并返回默认计划
            error_msg = f"Planning error: {str(e)}"
            state.add_error({"error": error_msg, "type": "planning_error"})
            return [
                {
                    "step": 1,
                    "description": f"Default action due to error: {str(e)}",
                    "tool": "default_tool",
                    "expected_result": "Error handled"
                }
            ]
    
    async def _execute_plan(self, state: AgentState, plan: List[Dict[str, Any]]) -> AgentState:
        """执行计划"""
        current_step = 0
        
        for plan_step in plan:
            if current_step >= state.max_iterations or current_step >= self.config.max_iterations:
                break
                
            # 执行计划步骤
            step_result = await self._execute_plan_step(state, plan_step)
            
            # 更新状态
            from .state import AgentMessage
            state.add_message(AgentMessage(
                content=f"Step {plan_step['step']}: {step_result}",
                role="ai",
                metadata={"type": "plan_execution"}
            ))
            
            # 检查是否需要调整计划
            if not step_result.get("success", False):
                # 如果步骤失败，可能需要调整计划
                state.add_error({
                    "error": f"Plan step {plan_step['step']} failed",
                    "type": "plan_execution_error"
                })
                break
            
            current_step += 1
        
        # 更新状态中的任务历史
        state.task_history.append({
            "agent_id": self.config.name,
            "iterations": current_step,
            "final_state": "completed",
            "plan": plan
        })
        
        return state
    
    async def _execute_plan_step(self, state: AgentState, plan_step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个计划步骤"""
        try:
            step_description = plan_step.get("description", "")
            tool_name = plan_step.get("tool", "")
            
            # 根据计划步骤执行相应的操作
            if tool_name and tool_name != "default_tool":
                # 发布工具调用事件
                self.event_manager.publish(AgentEvent.TOOL_CALL_REQUESTED, {
                    "agent_id": self.config.name,
                    "tool_call": tool_name,
                    "state": state
                })
                
                # 执行工具调用
                tool_result = await self._execute_tool(state, tool_name, step_description)
                return {
                    "success": tool_result.success,
                    "result": tool_result.output,
                    "tool_name": tool_name
                }
            else:
                # 执行非工具操作
                execution_prompt = f"""
                Execute the following plan step: {step_description}
                
                Available context: {state.context}
                """
                
                messages = [HumanMessage(content=execution_prompt)]
                
                response = await self.llm_client.generate_async(messages)
                return {
                    "success": True,
                    "result": response.content,
                    "tool_name": None
                }
        except Exception as e:
            error_msg = f"Plan step execution error: {str(e)}"
            state.add_error({"error": error_msg, "type": "plan_step_error"})
            return {
                "success": False,
                "result": error_msg,
                "tool_name": plan_step.get("tool", "")
            }
    
    async def _execute_tool(self, state: AgentState, tool_name: str, description: str) -> ToolResult:
        """执行工具调用"""
        try:
            # 使用工具执行器执行工具调用
            if self.tool_executor:
                # 创建工具调用对象
                tool_call = ToolCall(
                    name=tool_name,
                    arguments={"description": description}
                )
                
                # 执行工具
                tool_result = await self.tool_executor.execute_async(tool_call)
                
                # 将domain.tools.interfaces.ToolResult转换为domain.prompts.agent_state.ToolResult
                return ToolResult(
                    tool_name=tool_result.tool_name or tool_name,
                    success=tool_result.success,
                    output=tool_result.output,
                    error=tool_result.error
                )
            else:
                # 如果没有工具执行器，返回模拟结果
                result = f"Tool {tool_name} executed: {description}"
                return ToolResult(tool_name=tool_name, success=True, output=result)
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            state.add_error({"error": error_msg, "type": "tool_execution_error"})
            return ToolResult(tool_name=tool_name, success=False, output=None, error=error_msg)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取Agent的能力列表"""
        return {"capabilities": ["planning", "execution", "plan_execute_algorithm"]}