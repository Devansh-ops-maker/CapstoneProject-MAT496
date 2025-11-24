# react_agent.py
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from llm_client import LLMClient
from tool_system import ToolManager
from config import config

class ReActAgent:
    def __init__(self, tool_manager: ToolManager):
        self.tool_manager = tool_manager
        self.llm = LLMClient()
        self.thought_trace = []
        self.max_steps = config.max_react_steps
    
    def think(self, 
              query: str, 
              context: Optional[Dict] = None,
              max_steps: Optional[int] = None) -> Dict[str, Any]:
        """ReAct reasoning with tool usage"""
        if max_steps is None:
            max_steps = self.max_steps
            
        self.thought_trace = []
        context = context or {}
        
        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": query})
        
        for step in range(max_steps):
            print(f"ReAct Step {step + 1}/{max_steps}")
            
            # Get LLM response
            llm_response = self.llm.chat_completion(messages)
            
            # Parse the response
            thought = self._parse_react_response(llm_response)
            thought["step"] = step
            thought["timestamp"] = datetime.now().isoformat()
            
            self.thought_trace.append(thought)
            
            # Check if we should respond directly
            if thought.get("action") == "respond":
                final_response = thought.get("action_input", "")
                if not final_response:
                    final_response = self.llm.generate(
                        f"Based on the reasoning process, provide a final answer to: {query}"
                    )
                
                return {
                    "type": "response",
                    "content": final_response,
                    "thought_trace": self.thought_trace,
                    "steps_taken": step + 1
                }
            
            # Execute tool if specified
            elif thought.get("action") and thought["action"] != "respond":
                tool_result = self._execute_tool_action(thought)
                
                # Add observation to context
                observation_msg = {
                    "role": "system",
                    "content": f"Observation: {json.dumps(tool_result, indent=2)}"
                }
                messages.append(observation_msg)
                
                # Update thought with observation
                self.thought_trace[-1]["observation"] = tool_result
                
                # Check if tool execution provides final answer
                if self._is_final_answer(tool_result, query):
                    return {
                        "type": "tool_response",
                        "content": self._format_tool_response(tool_result),
                        "thought_trace": self.thought_trace,
                        "steps_taken": step + 1
                    }
            else:
                # No valid action, break out
                break
        
        # Final response after max steps
        final_response = self.llm.chat_completion(messages)
        return {
            "type": "final_response",
            "content": final_response,
            "thought_trace": self.thought_trace,
            "steps_taken": max_steps
        }
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build the system prompt for ReAct reasoning"""
        base_prompt = f"""You are a reasoning assistant that uses tools to solve problems. Follow this format exactly:

Thought: Analyze the problem and decide what to do next. Consider what information you need.
Action: Choose one of: {', '.join(self.tool_manager.list_tools())} OR respond
Action Input: JSON parameters for the tool OR the final answer if action is respond

Available tools:
{self.tool_manager.get_tool_descriptions()}

Guidelines:
- Use tools when you need specific information (weather, calculations, time, web search)
- Use 'respond' when you have enough information to answer directly
- Be concise in your thoughts
- If a tool returns an error, try a different approach
- After getting information from tools, synthesize it into a coherent response

Example:
Thought: I need to calculate the total cost first.
Action: calculator
Action Input: {{"expression": "25 * 4 + 10"}}

Thought: Now I have the calculation result, I can provide the total cost.
Action: respond  
Action Input: The total cost for 25 items at $4 each plus $10 shipping is $110.

Now, solve the following problem:"""
        
        # Add context if available
        if context.get("conversation_history"):
            history_context = "\n\nRecent conversation history:\n"
            for conv in context["conversation_history"][-3:]:  # Last 3 exchanges
                history_context += f"User: {conv['message']}\nAssistant: {conv['response']}\n"
            base_prompt += history_context
        
        return base_prompt
    
    def _parse_react_response(self, response: str) -> Dict[str, Any]:
        """Parse ReAct format from LLM response"""
        thought_match = re.search(r'Thought:\s*(.*?)(?=Action:|$)', response, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r'Action:\s*(\w+)', response, re.IGNORECASE)
        action_input_match = re.search(r'Action Input:\s*(.*?)(?=Thought:|$)', response, re.DOTALL | re.IGNORECASE)
        
        parsed = {}
        
        if thought_match:
            parsed["thought"] = thought_match.group(1).strip()
        
        if action_match:
            parsed["action"] = action_match.group(1).strip().lower()
        
        if action_input_match:
            input_text = action_input_match.group(1).strip()
            if input_text and input_text.lower() != "null":
                # Try to parse as JSON, otherwise keep as string
                try:
                    parsed["action_input"] = json.loads(input_text)
                except json.JSONDecodeError:
                    # If it's not JSON and action is respond, use it as the response
                    if parsed.get("action") == "respond":
                        parsed["action_input"] = input_text
                    else:
                        # Try to extract JSON from the text
                        json_match = re.search(r'\{.*\}', input_text)
                        if json_match:
                            try:
                                parsed["action_input"] = json.loads(json_match.group())
                            except:
                                parsed["action_input"] = input_text
                        else:
                            parsed["action_input"] = input_text
        
        return parsed
    
    def _execute_tool_action(self, thought: Dict) -> Dict:
        """Execute tool action based on thought"""
        action = thought.get("action")
        action_input = thought.get("action_input", {})
        
        if not isinstance(action_input, dict):
            action_input = {"input": action_input}
        
        print(f"Executing tool: {action} with input: {action_input}")
        
        try:
            return self.tool_manager.execute_tool(action, action_input)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _is_final_answer(self, tool_result: Dict, original_query: str) -> bool:
        """Check if tool result contains a final answer"""
        # Simple heuristic: if tool result doesn't contain error and query is simple
        if "error" in tool_result:
            return False
        
        # For certain tools, they might provide direct answers
        direct_answer_tools = ["calculator", "get_time"]
        if any(tool in original_query.lower() for tool in direct_answer_tools):
            return True
        
        return False
    
    def _format_tool_response(self, tool_result: Dict) -> str:
        """Format tool result into user-friendly response"""
        if "error" in tool_result:
            return f"Tool error: {tool_result['error']}"
        
        # Format based on tool type
        if "result" in tool_result:
            return f"The result is: {tool_result['result']}"
        elif "current_time" in tool_result:
            return f"The current time is: {tool_result['current_time']}"
        elif "temperature" in tool_result:
            return f"Weather in {tool_result['location']}: {tool_result['temperature']}, {tool_result['conditions']}"
        else:
            return json.dumps(tool_result, indent=2)
    
    def get_thought_trace(self) -> List[Dict]:
        """Get the complete reasoning trace"""
        return self.thought_trace
    
    def clear_trace(self):
        """Clear the thought trace"""
        self.thought_trace = []