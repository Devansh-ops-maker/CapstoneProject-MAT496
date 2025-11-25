import uuid
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import config
from llm_client import LLMClient
from memory_manager import MemoryManager
from tool_system import ToolManager
from rag_system import DynamicRAGSystem
from memory_extractor import MemoryExtractor

class DynamicPersonalAssistant:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = MemoryManager()
        self.tool_manager = ToolManager()
        self.rag_system = DynamicRAGSystem()
        self.memory_extractor = MemoryExtractor()
        self.learning_enabled = True
        self.performance_metrics = {
            "total_queries": 0,
            "sources_used": {},
            "learning_opportunities": 0,
            "memory_usage_count": 0
        }

    def _is_quota_error(self, err: Exception) -> bool:
        text = str(err).lower()
        return "insufficient_quota" in text or "429" in text or "quota" in text

    def _quota_message(self) -> str:
        return "Unable to complete this request because the API quota is exhausted."

    def _safe_llm_generate(self, prompt: str) -> str:
        try:
            return self.llm.generate(prompt)
        except Exception as e:
            if self._is_quota_error(e):
                return self._quota_message()
            return self._quota_message()

    def _safe_rag_query(self, query: str) -> Optional[str]:
        try:
            return self.rag_system.query(query)
        except Exception as e:
            if self._is_quota_error(e):
                return None
            return None

    def _safe_tool_execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.tool_manager.execute_tool(tool_name, params)
        except Exception as e:
            if self._is_quota_error(e):
                return {"error": self._quota_message()}
            return {"error": str(e)}

    def _safe_rag_learn(self, query: str, content: str, source: str):
        try:
            self.rag_system.learn_from_interaction(query, content, source)
        except Exception as e:
            if self._is_quota_error(e):
                return

    def process_query(self, user_id: str, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        self.performance_metrics["total_queries"] += 1
        if not session_id:
            session_id = str(uuid.uuid4())
        
        memory_data = self.memory_extractor.extract(query)
        if memory_data.get("is_memory"):
            self.memory.store_memory(user_id, memory_data["key"], memory_data["value"])
        
        conversation_history = self.memory.get_recent_conversations(user_id, session_id)
        user_memories = self.memory.get_user_memories(user_id)
        
        responses = self._generate_all_responses(query, user_id, session_id, conversation_history, user_memories)
        best_response = self._select_response_dynamically(query, responses)
        
        if user_memories and best_response["source"] != "tool":
            refined_response = self._refine_response_with_memory(
                best_response["content"], query, user_memories, conversation_history
            )
            if refined_response and refined_response != self._quota_message():
                best_response["content"] = refined_response
        
        if self.learning_enabled and best_response["confidence"] > 0.7:
            self._learn_from_interaction(query, best_response)
        
        self.memory.store_conversation(user_id, session_id, query, best_response["content"])
        
        self.performance_metrics["sources_used"][best_response["source"]] = \
            self.performance_metrics["sources_used"].get(best_response["source"], 0) + 1
        
        memory_used = len(conversation_history) > 0 or len(user_memories) > 0
        if memory_used:
            self.performance_metrics["memory_usage_count"] += 1
        
        return {
            "response": best_response["content"],
            "session_id": session_id,
            "source": best_response["source"],
            "confidence": best_response["confidence"],
            "learning_applied": self.learning_enabled,
            "memory_used": memory_used,
            "user_memories_count": len(user_memories)
        }

    def _refine_response_with_memory(self, original_response: str, query: str, 
                                    user_memories: Dict[str, str], history: List[Dict]) -> str:
        try:
            if len(original_response.strip()) < 10 or "unable to complete" in original_response.lower():
                return original_response
            
            unique_memories = []
            seen_memories = set()
            for key, value in user_memories.items():
                if value not in seen_memories and len(value.strip()) > 2:
                    seen_memories.add(value)
                    unique_memories.append(f"{key}: {value}")
            
            if not unique_memories:
                return original_response
            
            memory_facts = "\n".join([f"- {mem}" for mem in unique_memories[:10]])
            
            prompt = f"""You are a helpful personal assistant. The user has asked you a question, and you have access to facts about them.

User's Question: "{query}"

Facts about the user:
{memory_facts}

Instructions:
1. Answer the user's question directly.
2. Use the relevant facts about the user.
3. Keep the response short and specific.
4. Avoid generic motivational language.

Generate the personalized response:"""
            
            refined_response = self._safe_llm_generate(prompt)
            
            if (refined_response and 
                refined_response != self._quota_message() and 
                len(refined_response.strip()) > 10 and
                "unable to complete" not in refined_response.lower()):
                return refined_response
            
            return original_response
        except:
            return original_response

    def _generate_all_responses(self, query: str, user_id: str, session_id: str,
                               history: List[Dict], user_memories: Dict[str, str]) -> List[Dict]:
        responses = []
        llm_response = self._generate_llm_response(query, user_id, session_id, history, user_memories)
        if llm_response:
            responses.append(llm_response)
        rag_response = self._generate_rag_response(query, history, user_memories)
        if rag_response:
            responses.append(rag_response)
        tool_responses = self._generate_tool_responses(query, history)
        responses.extend(tool_responses)
        return responses

    def _generate_llm_response(self, query: str, user_id: str, session_id: str,
                              history: List[Dict], user_memories: Dict[str, str]) -> Dict:
        try:
            basic_prompt = f"""You are a helpful assistant. Answer the user's question clearly.

Question: {query}

Response:"""
            
            basic_response = self._safe_llm_generate(basic_prompt)
            
            return {
                "content": basic_response,
                "source": "direct_llm",
                "confidence": 0.7,
                "response_length": len(basic_response),
                "method": "llm_basic"
            }
        except:
            return None

    def _generate_rag_response(self, query: str, history: List[Dict],
                               user_memories: Dict[str, str]) -> Optional[Dict]:
        try:
            enhanced_query = self._enhance_query_with_memory(query, history, user_memories)
            rag_context = self._safe_rag_query(enhanced_query)
            if not rag_context:
                return None
            return {
                "content": rag_context,
                "source": "rag",
                "confidence": 0.85,
                "response_length": len(rag_context),
                "method": "rag_basic"
            }
        except:
            return None

    def _enhance_query_with_memory(self, query: str, history: List[Dict],
                                   user_memories: Dict[str, str]) -> str:
        enhanced_terms = []
        for value in user_memories.values():
            words = value.split()
            enhanced_terms.extend([word for word in words if len(word) > 3])
        
        if history:
            for conv in history[-2:]:
                enhanced_terms.extend(conv['message'].split()[:3])
                enhanced_terms.extend(conv['response'].split()[:3])
        
        if enhanced_terms:
            unique_terms = set(term.lower() for term in enhanced_terms if len(term) > 3)
            return query + " " + " ".join(unique_terms)
        return query

    def _generate_tool_responses(self, query: str, history: List[Dict]) -> List[Dict]:
        tool_responses = []
        query_lower = query.lower()
        
        for tool_name in self.tool_manager.list_tools():
            if self._is_tool_relevant(query_lower, tool_name, history):
                try:
                    params = self._extract_tool_params(query, tool_name, history)
                    tool_result = self._safe_tool_execute(tool_name, params)
                    
                    if "error" not in tool_result:
                        response_content = self._format_tool_response(tool_result, tool_name, query)
                        tool_responses.append({
                            "content": response_content,
                            "source": "tool",
                            "confidence": self._calculate_tool_confidence(tool_result, query_lower, tool_name),
                            "response_length": len(response_content),
                            "method": f"tool_{tool_name}",
                            "tool_data": tool_result,
                            "tool_name": tool_name
                        })
                except:
                    pass
        
        return tool_responses
    
    def _is_tool_relevant(self, query_lower: str, tool_name: str, history: List[Dict]) -> bool:
        tool_patterns = {
            "calculator": {
                "patterns": [
                    r'(\d+\.?\d*\s*[+\-*/]\s*\d+\.?\d*)',
                    r'calculate',
                    r'what is \d+',
                    r'\d+ plus \d+',
                    r'\d+ minus \d+',
                    r'\d+ times \d+',
                    r'\d+ divided by \d+',
                    r'sum of',
                    r'product of',
                    r'difference between'
                ],
                "keywords": ["calculate", "math", "add", "subtract", "multiply", "divide", "sum", "product"]
            },
            "get_weather": {
                "patterns": [
                    r'weather(?: in| at| for)?\s+([a-zA-Z]+)',
                    r'temperature(?: in| at| for)?\s+([a-zA-Z]+)',
                    r'forecast(?: in| at| for)?\s+([a-zA-Z]+)',
                    r'how is the weather',
                    r"how's the weather"
                ],
                "keywords": ["weather", "temperature", "forecast", "rain", "sunny", "hot", "cold"]
            },
            "get_time": {
                "patterns": [
                    r'what is the time',
                    r"what's the time",
                    r'current time',
                    r'what time is it',
                    r'time now',
                    r'date and time'
                ],
                "keywords": ["time", "current time", "what time", "clock", "date"]
            },
            "web_search": {
                "patterns": [
                    r'search for',
                    r'find information about',
                    r'look up',
                    r'google'
                ],
                "keywords": ["search", "find", "look up", "information about"]
            }
        }
        
        if tool_name not in tool_patterns:
            return False
        
        for pattern in tool_patterns[tool_name]["patterns"]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True
        
        for keyword in tool_patterns[tool_name]["keywords"]:
            if keyword in query_lower:
                return True
        
        if history:
            recent_text = " ".join([conv['message'] + " " + conv['response'] for conv in history[-2:]])
            if tool_name in recent_text.lower():
                return True
        
        return False
    
    def _extract_tool_params(self, query: str, tool_name: str, history: List[Dict]) -> Dict:
        query_lower = query.lower()
        
        if tool_name == "calculator":
            patterns = [
                r'(\d+\.?\d*)\s*([+\-*/])\s*(\d+\.?\d*)',
                r'(\d+)\s+plus\s+(\d+)',
                r'(\d+)\s+minus\s+(\d+)',
                r'(\d+)\s+times\s+(\d+)',
                r'(\d+)\s+divided by\s+(\d+)',
                r'sum of (\d+) and (\d+)',
                r'product of (\d+) and (\d+)',
                r'difference between (\d+) and (\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    if pattern == patterns[0]:
                        return {"expression": f"{match.group(1)} {match.group(2)} {match.group(3)}"}
                    elif "plus" in pattern:
                        return {"expression": f"{match.group(1)} + {match.group(2)}"}
                    elif "minus" in pattern:
                        return {"expression": f"{match.group(1)} - {match.group(2)}"}
                    elif "times" in pattern:
                        return {"expression": f"{match.group(1)} * {match.group(2)}"}
                    elif "divided" in pattern:
                        return {"expression": f"{match.group(1)} / {match.group(2)}"}
                    elif "sum" in pattern:
                        return {"expression": f"{match.group(1)} + {match.group(2)}"}
                    elif "product" in pattern:
                        return {"expression": f"{match.group(1)} * {match.group(2)}"}
                    elif "difference" in pattern:
                        return {"expression": f"{match.group(1)} - {match.group(2)}"}
        
        elif tool_name == "get_weather":
            location_patterns = [
                r'weather(?: in| at| for)?\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
                r'temperature(?: in| at| for)?\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
                r'forecast(?: in| at| for)?\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
                r'in\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)(?:\s+weather|\s+temperature)',
                r'at\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)(?:\s+weather|\s+temperature)'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    if location and len(location) > 1:
                        return {"location": location}
            
            return {"location": "Delhi"}
        
        elif tool_name == "get_time":
            return {}
        
        elif tool_name == "web_search":
            search_patterns = [
                r'search for\s+(.+)',
                r'find information about\s+(.+)',
                r'look up\s+(.+)',
                r'google\s+(.+)'
            ]
            
            for pattern in search_patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    search_query = match.group(1).strip()
                    return {"query": search_query, "max_results": 3}
            
            return {"query": query, "max_results": 3}
        
        return {}
    
    def _format_tool_response(self, tool_result: Dict, tool_name: str, original_query: str) -> str:
        if "error" in tool_result:
            return f"Sorry, I couldn't process your request: {tool_result['error']}"
        
        if tool_name == "calculator":
            if "result" in tool_result:
                return f"The result is {tool_result['result']}"
        
        elif tool_name == "get_weather":
            if "location" in tool_result and "temperature" in tool_result:
                return f"Current weather in {tool_result['location']}: {tool_result['temperature']}"
        
        elif tool_name == "get_time":
            if "current_time" in tool_result:
                return f"The current time is {tool_result['current_time']}"
        
        elif tool_name == "web_search":
            if "results" in tool_result and tool_result["results"]:
                first_result = tool_result["results"][0]
                return first_result.get('snippet', 'No details available')
        
        return str(tool_result)
    
    def _calculate_tool_confidence(self, tool_result: Dict, query_lower: str, tool_name: str) -> float:
        base_confidence = 0.85
        
        if tool_name == "calculator":
            if "result" in tool_result and not "error" in tool_result:
                return 0.95
        
        elif tool_name == "get_time":
            return 0.95
        
        elif tool_name == "get_weather":
            if "temperature" in tool_result:
                return 0.90
            else:
                return 0.80
        
        if any(keyword in query_lower for keyword in [tool_name, "calculate", "weather", "time", "search"]):
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)
    
    def _calculate_response_score(self, response: Dict, query: str) -> float:
        score = 0
        
        source_scores = {
            "tool": 90,
            "rag": 70,
            "direct_llm": 65,
            "fallback": 10
        }
        
        source = response.get("source", "unknown")
        score += source_scores.get(source, 50)
        
        content = response.get("content", "")
        if content:
            word_count = len(content.split())
            if source == "tool":
                if 5 <= word_count <= 50:
                    score += 20
                elif word_count < 5:
                    score += 10
                else:
                    score += min(word_count * 0.3, 20)
            else:
                score += min(word_count * 0.5, 20)
        
        if any(phrase in content.lower() for phrase in ["error", "unable", "cannot", "don't know", "i don't have"]):
            score -= 40
        
        query_terms = set(word.lower() for word in query.split() if len(word) > 3)
        content_terms = set(word.lower() for word in content.split() if len(word) > 3)
        common_terms = query_terms.intersection(content_terms)
        if query_terms:
            relevance_ratio = len(common_terms) / len(query_terms)
            score += relevance_ratio * 30
        
        if source == "tool":
            tool_keywords = ["weather", "calculate", "time", "search", "math", "temperature"]
            if any(keyword in query.lower() for keyword in tool_keywords):
                score += 25
        
        if "memory" in response.get("method", ""):
            score += 15
        
        return max(score, 10)
    
    def _is_tool_applicable(self, query: str, tool_name: str, history: List[Dict]) -> bool:
        query_lower = query.lower()
        tool_patterns = {
            "calculator": [r'\d+\.?\d*\s*[+\-*/]\s*\d+\.?\d*', r'calculate', r'math'],
            "get_weather": [r'weather', r'temperature', r'forecast'],
            "get_time": [r'time', r'current.*time', r'what.*time'],
            "web_search": [r'search', r'find.*information', r'look up']
        }
        if tool_name in tool_patterns:
            for pattern in tool_patterns[tool_name]:
                if re.search(pattern, query_lower):
                    return True
        if history:
            recent_conversation = " ".join([conv['message'] + " " + conv['response'] for conv in history[-2:]])
            if tool_name in recent_conversation.lower():
                return True
        return False

    def _infer_tool_parameters(self, query: str, tool_name: str, history: List[Dict]) -> Dict:
        params = {}
        if tool_name == "calculator":
            math_match = re.search(r'(\d+\.?\d*)\s*([+\-*/])\s*(\d+\.?\d*)', query)
            if math_match:
                params = {"expression": f"{math_match.group(1)} {math_match.group(2)} {math_match.group(3)}"}
        elif tool_name == "get_weather":
            location_match = re.search(r'(?:in|at|for)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)', query)
            if location_match:
                params = {"location": location_match.group(1)}
            elif history:
                for conv in reversed(history):
                    loc_match = re.search(r'(?:weather|temperature).*?(?:in|at|for)\s+([a-zA-Z]+)',
                                         conv['message'] + " " + conv['response'], re.IGNORECASE)
                    if loc_match:
                        params = {"location": loc_match.group(1)}
                        break
        return params

    def _format_tool_result_with_memory(self, tool_result: Dict, tool_name: str,
                                       original_query: str, history: List[Dict]) -> str:
        if "error" in tool_result:
            return f"Could not process your request: {tool_result['error']}"
        memory_context = ""
        if history:
            memory_context = f"\nPrevious conversation context: {history[-1]['message'][:50]}..."
        prompt = f"""The user asked: "{original_query}"{memory_context}
The tool '{tool_name}' returned this result: {tool_result}
Provide a natural response based on this result:"""
        try:
            return self._safe_llm_generate(prompt)
        except:
            return f"Result: {tool_result}"

    def _select_response_dynamically(self, query: str, responses: List[Dict]) -> Dict:
        if not responses:
            return {
                "content": "I'm currently unable to process your request. Please try again.",
                "source": "fallback",
                "confidence": 0.1
            }
        scored_responses = []
        for response in responses:
            score = self._calculate_response_score(response, query)
            scored_responses.append((score, response))
        best_score, best_response = max(scored_responses, key=lambda x: x[0])
        best_response["confidence"] = min(best_score / 100, 0.95)
        return best_response

    def _get_dynamic_source_scores(self) -> Dict[str, float]:
        base_scores = {
            "tool": 80,
            "rag": 70,
            "direct_llm": 65,
            "fallback": 10
        }
        total_queries = self.performance_metrics["total_queries"]
        if total_queries > 0:
            for source, count in self.performance_metrics["sources_used"].items():
                success_rate = count / total_queries
                if source in base_scores:
                    base_scores[source] += success_rate * 20
        return base_scores

    def _learn_from_interaction(self, query: str, response: Dict):
        self.performance_metrics["learning_opportunities"] += 1
        self._safe_rag_learn(query, response["content"], response["source"])

    def get_conversation_history(self, user_id: str, session_id: str) -> list:
        return self.memory.get_recent_conversations(user_id, session_id)

    def get_user_memories(self, user_id: str) -> Dict[str, str]:
        return self.memory.get_user_memories(user_id)

    def get_performance_metrics(self) -> Dict:
        metrics = self.performance_metrics.copy()
        try:
            metrics["rag_statistics"] = self.rag_system.get_statistics()
        except Exception:
            metrics["rag_statistics"] = {}
        return metrics

    def enable_learning(self, enabled: bool = True):
        self.learning_enabled = enabled

    def add_knowledge(self, content: str, source: str = "user_input"):
        try:
            self.rag_system.add_document({
                "content": content,
                "source": source,
                "added_date": datetime.now().isoformat(),
                "confidence": 0.8
            })
        except Exception as e:
            if not self._is_quota_error(e):
                pass

    def close(self):
        try:
            self.memory.close()
        except Exception:
            pass
        try:
            self.memory_extractor.close()
        except Exception:
            pass
