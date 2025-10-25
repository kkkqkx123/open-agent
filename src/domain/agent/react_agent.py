"""ReAct Agent实现"""

import asyncio
from typing import Any, Dict, List
from .base import BaseAgent
from ..prompts.agent_state import AgentState, BaseMessage, ToolResult
from src.domain.tools.interfaces import ToolCall
from .events import AgentEvent


class ReActAgent(BaseAgent):
    """实现ReAct算法的Agent
    ReAct (Reasoning + Acting) 算法结合了推理和行动，通过交替进行推理和行动来解决问题
    """
    
    async def _execute_logic(self, state: AgentState) -> AgentState:
        """执行ReAct算法：Reasoning + Acting"""
        current_iteration = 0
        
        while current_iteration < state.max_iterations and current_iteration < self.config.max_iterations:
            # 1. 分析当前状态并进行推理
            reasoning_result = await self._reason(state)
            
            # 将推理结果添加到记忆中
            state.add_memory(BaseMessage(content=f"Thought: {reasoning_result}", type="reasoning"))
            
            # 2. 决策下一步行动
            action_result = await self._decide_action(state, reasoning_result)
            
            # 发布决策事件
            self.event_manager.publish(AgentEvent.DECISION_MADE, {
                "agent_id": self.config.name,
                "action_result": action_result,
                "state": state
            })
            
            # 3. 执行行动（可能包括调用工具）
            if action_result.get("action") == "tool_call":
                tool_call_str = action_result.get("tool_call", "")
                
                # 发布工具调用事件
                self.event_manager.publish(AgentEvent.TOOL_CALL_REQUESTED, {
                    "agent_id": self.config.name,
                    "tool_call": tool_call_str,
                    "state": state
                })
                
                tool_result = await self._execute_tool(state, tool_call_str)
                
                # 将工具执行结果添加到状态中
                state.tool_results.append(tool_result)
                
                # 将观察结果添加到记忆中
                observation = f"Action: {tool_call_str}\nObservation: {tool_result.result}"
                state.add_memory(BaseMessage(content=observation, type="observation"))
            elif action_result.get("action") == "final_answer":
                # 如果是最终答案，添加到状态并退出循环
                answer = action_result.get("answer", "No answer provided")
                state.add_memory(BaseMessage(content=answer, type="final_answer"))
                break
            else:
                # 其他行动类型
                state.add_memory(BaseMessage(content=f"Action: {action_result}", type="action"))
            
            current_iteration += 1
            state.iteration_count = current_iteration
        
        # 更新状态中的任务历史
        state.task_history.append({
            "agent_id": self.config.name,
            "iterations": current_iteration,
            "final_state": "completed"
        })
        
        return state
    
    def can_handle(self, state: AgentState) -> bool:
        """判断Agent是否能处理当前状态"""
        # ReAct Agent可以处理需要推理和行动的任务
        return True
    
    async def _reason(self, state: AgentState) -> str:
        """执行推理步骤"""
        # 使用LLM进行推理
        from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
        
        # 构建推理请求
        reasoning_prompt = f"""
        Given the current state and context, please think step by step:
        
        1. What is the main goal?
        2. What information do we have?
        3. What is the next logical step?
        4. Why is this step important?
        
        Current state: {str(state.__dict__)}
        """
        
        messages = [
            SystemMessage(content=f"System: {self.config.system_prompt}"),
            HumanMessage(content=reasoning_prompt)
        ]
        
        # 调用LLM进行推理
        try:
            response = await self.llm_client.generate_async(messages)
            reasoning_result = response.content
            return reasoning_result
        except Exception as e:
            # 记录错误并返回默认推理
            error_msg = f"Reasoning error: {str(e)}"
            state.add_error({"error": error_msg, "type": "reasoning_error"})
            return "Unable to reason due to an error. Proceeding with default action."
    
    async def _decide_action(self, state: AgentState, reasoning_result: str) -> Dict[str, Any]:
        """决定下一步行动"""
        # 根据推理结果决定行动
        from langchain_core.messages import HumanMessage  # type: ignore
        
        action_decision_prompt = f"""
        Based on the reasoning: "{reasoning_result}"
        
        Please decide the next action. You can:
        1. Call a tool: Return in format {{"action": "tool_call", "tool_call": "..."}}
        2. Provide final answer: Return in format {{"action": "final_answer", "answer": "..."}}
        3. Other action: Return in format {{"action": "other", "details": "..."}}
        
        Available tools: {self.config.tools}
        Available tool sets: {self.config.tool_sets}
        """
        
        messages = [HumanMessage(content=action_decision_prompt)]
        
        try:
            response = await self.llm_client.generate_async(messages)
            # 解析行动决策
            action_decision = response.content.strip()
            
            # 简单的解析逻辑（在实际实现中可能需要更复杂的解析）
            if "final_answer" in action_decision.lower():
                return {"action": "final_answer", "answer": action_decision}
            elif any(tool in action_decision for tool in self.config.tools):
                return {"action": "tool_call", "tool_call": action_decision}
            else:
                return {"action": "other", "details": action_decision}
        except Exception as e:
            # 记录错误并返回默认行动
            error_msg = f"Action decision error: {str(e)}"
            state.add_error({"error": error_msg, "type": "action_decision_error"})
            return {"action": "other", "details": "Default action due to error"}
    
    async def _execute_tool(self, state: AgentState, tool_call_str: str) -> ToolResult:
        """执行工具调用"""
        try:
            # 使用工具执行器执行工具调用
            # 在实际实现中，需要解析工具调用字符串并创建ToolCall对象
            # 这里简化为模拟执行
            if self.tool_executor and tool_call_str:
                # 模拟工具调用对象的创建
                # 简单解析工具调用字符串
                tool_name = tool_call_str.split()[0] if tool_call_str.split() else "default_tool"
                tool_call = ToolCall(
                    name=tool_name,
                    arguments={"query": tool_call_str}
                )
                
                # 执行工具
                tool_result = await self.tool_executor.execute_async(tool_call)
                
                # 将domain.tools.interfaces.ToolResult转换为domain.prompts.agent_state.ToolResult
                return ToolResult(
                    tool_name=tool_result.tool_name or "unknown_tool",
                    success=tool_result.success,
                    result=tool_result.output,
                    error=tool_result.error
                )
            else:
                # 如果没有工具执行器或工具调用为空，返回模拟结果
                result = f"Tool executed: {tool_call_str}"
                return ToolResult(tool_name="unknown_tool", success=True, result=result)
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            state.add_error({"error": error_msg, "type": "tool_execution_error"})
            return ToolResult(tool_name="unknown_tool", success=False, result=None, error=error_msg)
    
    def get_capabilities(self) -> List[str]:
        """获取Agent的能力列表"""
        return ["reasoning", "tool_execution", "react_algorithm"]