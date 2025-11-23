from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json
from datetime import datetime
import requests
from config import config

class BaseTool(ABC):
    @abstractmethod
    def execute(self, params: Dict) -> Dict:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    def parameters(self) -> Dict:
        return {}

class WeatherTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "Get current weather information for a location"
    
    @property
    def parameters(self) -> Dict:
        return {
            "location": {
                "type": "string",
                "description": "City name or location"
            }
        }
    
    def execute(self, params: Dict) -> Dict:
        location = params.get("location", "")
        if not location:
            return {"error": "Location parameter is required"}
        
        return {
            "location": location,
            "temperature": "22°C",
            "conditions": "Sunny",
            "humidity": "65%",
            "wind_speed": "15 km/h",
            "source": "weather_api"
        }

class CalculatorTool(BaseTool):
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform mathematical calculations"
    
    @property
    def parameters(self) -> Dict:
        return {
            "expression": {
                "type": "string", 
                "description": "Mathematical expression to evaluate"
            }
        }
    
    def execute(self, params: Dict) -> Dict:
        expression = params.get("expression", "")
        if not expression:
            return {"error": "Expression parameter is required"}
        
        try:
            allowed_ops = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y, 
                '*': lambda x, y: x * y,
                '/': lambda x, y: x / y if y != 0 else "Division by zero",
                '**': lambda x, y: x ** y,
                '//': lambda x, y: x // y if y != 0 else "Division by zero",
                '%': lambda x, y: x % y if y != 0 else "Modulo by zero",
            }
            result = eval(expression, {"__builtins__": {}}, allowed_ops)
            
            return {
                "expression": expression,
                "result": result,
                "type": "calculation"
            }
        except Exception as e:
            return {"error": f"Calculation failed: {str(e)}"}

class TimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_time"
    
    @property
    def description(self) -> str:
        return "Get current date and time information"
    
    def execute(self, params: Dict) -> Dict:
        now = datetime.now()
        return {
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "local",
            "timestamp": now.timestamp(),
            "formats": {
                "iso": now.isoformat(),
                "readable": now.strftime("%A, %B %d, %Y at %I:%M %p")
            }
        }

class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    @property
    def parameters(self) -> Dict:
        return {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "max_results": {
                "type": "integer", 
                "description": "Maximum number of results",
                "default": 3
            }
        }
    
    def execute(self, params: Dict) -> Dict:
        query = params.get("query", "")
        max_results = params.get("max_results", 3)
        
        if not query:
            return {"error": "Query parameter is required"}
        
        return {
            "query": query,
            "results": [
                {
                    "title": f"Result 1 for {query}",
                    "snippet": f"This is information about {query} from the web.",
                    "url": "https://example.com/1"
                },
                {
                    "title": f"Result 2 for {query}", 
                    "snippet": f"More details about {query} found online.",
                    "url": "https://example.com/2"
                }
            ][:max_results],
            "source": "web_search_api"
        }

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.register_tools()
    
    def register_tools(self):
        tool_classes = [WeatherTool, CalculatorTool, TimeTool, WebSearchTool]
        for tool_class in tool_classes:
            tool_instance = tool_class()
            self.tools[tool_instance.name] = tool_instance
    
    def get_tool_descriptions(self) -> str:
        descriptions = []
        for tool in self.tools.values():
            desc = f"{tool.name}: {tool.description}"
            if tool.parameters:
                params_desc = ", ".join([f"{name}: {info['type']}" for name, info in tool.parameters.items()])
                desc += f" | Parameters: {params_desc}"
            descriptions.append(desc)
        return "\n".join(descriptions)
    
    def execute_tool(self, tool_name: str, params: Dict) -> Dict:
        if tool_name in self.tools:
            try:
                return self.tools[tool_name].execute(params)
            except Exception as e:
                return {"error": f"Tool execution failed: {str(e)}"}
        return {"error": f"Tool '{tool_name}' not found"}
    
    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        return None
