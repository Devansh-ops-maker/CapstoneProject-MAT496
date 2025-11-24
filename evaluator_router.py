from typing import List, Dict, Any, Optional
import re
from datetime import datetime

class ResponseEvaluator:
    def __init__(self):
        self.evaluation_history = []
    
    def evaluate_responses(self, query: str, responses: List[Dict], user_context: Optional[Dict] = None) -> Dict:
        if not responses:
            return {
                "selected_response": {
                    "content": "No responses were generated.",
                    "source": "error",
                    "confidence": 0.0
                },
                "all_scores": [],
                "reason": "no_responses"
            }
        
        scores = []
        for i, response in enumerate(responses):
            score_data = self._evaluate_single_response(query, response, user_context)
            scores.append({
                "index": i,
                "response": response,
                "scores": score_data,
                "composite_score": score_data["composite_score"]
            })
        
        best = max(scores, key=lambda x: x["composite_score"])
        
        evaluation_result = {
            "selected_response": best["response"],
            "all_scores": scores,
            "reason": f"Highest composite score: {best['composite_score']:.3f}",
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
        self.evaluation_history.append({
            "query": query,
            "evaluation": evaluation_result,
            "timestamp": datetime.now().isoformat()
        })
        
        return evaluation_result
    
    def _evaluate_single_response(self, query: str, response: Dict, user_context: Optional[Dict] = None) -> Dict:
        content = response.get("content", "")
        source = response.get("source", "unknown")
        confidence = response.get("confidence", 0.5)
        
        relevance_score = self._calculate_relevance_score(query, content)
        completeness_score = self._calculate_completeness_score(content)
        coherence_score = self._calculate_coherence_score(content)
        source_score = self._calculate_source_score(source)
        
        weights = {
            "relevance": 0.35,
            "completeness": 0.25, 
            "coherence": 0.20,
            "source": 0.20
        }
        
        composite_score = (
            relevance_score * weights["relevance"] +
            completeness_score * weights["completeness"] +
            coherence_score * weights["coherence"] + 
            source_score * weights["source"]
        )
        
        composite_score *= confidence
        
        return {
            "relevance_score": relevance_score,
            "completeness_score": completeness_score,
            "coherence_score": coherence_score,
            "source_score": source_score,
            "composite_score": min(composite_score, 1.0),
            "evaluation_method": "multi_criteria"
        }
    
    def _calculate_relevance_score(self, query: str, response: str) -> float:
        if not response or not query:
            return 0.0
        
        query_terms = set(term.lower() for term in query.split() if len(term) > 3)
        response_terms = set(term.lower() for term in response.split() if len(term) > 3)
        
        if not query_terms:
            return 0.5
        
        overlapping_terms = query_terms.intersection(response_terms)
        term_overlap_score = len(overlapping_terms) / len(query_terms)
        
        query_complexity = len(query.split())
        response_length = len(response.split())
        
        if query_complexity <= 5:
            if response_length < 5:
                length_score = 0.3
            elif response_length > 100:
                length_score = 0.7
            else:
                length_score = 1.0
        else:
            if response_length < 10:
                length_score = 0.2
            elif response_length > 200:
                length_score = 0.8
            else:
                length_score = 1.0
        
        return (term_overlap_score * 0.7 + length_score * 0.3)
    
    def _calculate_completeness_score(self, response: str) -> float:
        if not response:
            return 0.0
        
        word_count = len(response.split())
        sentence_count = len(re.split(r'[.!?]+', response))
        
        word_score = min(word_count / 50, 1.0)
        sentence_score = min(sentence_count / 3, 1.0)
        
        incompleteness_indicators = [
            "i don't know", "i'm not sure", "i can't answer", 
            "no information", "don't have enough"
        ]
        
        completeness_penalty = 0.0
        for indicator in incompleteness_indicators:
            if indicator in response.lower():
                completeness_penalty = 0.5
                break
        
        return (word_score * 0.6 + sentence_score * 0.4) * (1 - completeness_penalty)
    
    def _calculate_coherence_score(self, response: str) -> float:
        if not response:
            return 0.0
        
        sentences = re.split(r'[.!?]+', response)
        avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / max(len(sentences), 1)
        
        if 8 <= avg_sentence_length <= 20:
            sentence_structure_score = 1.0
        elif 5 <= avg_sentence_length <= 25:
            sentence_structure_score = 0.8
        else:
            sentence_structure_score = 0.5
        
        transition_words = {"however", "therefore", "additionally", "furthermore", "consequently"}
        transition_count = sum(1 for word in transition_words if word in response.lower())
        transition_score = min(transition_count / 3, 1.0)
        
        return (sentence_structure_score * 0.7 + transition_score * 0.3)
    
    def _calculate_source_score(self, source: str) -> float:
        source_scores = {
            "tool": 0.9,
            "rag": 0.8,
            "react": 0.85,
            "direct_llm": 0.7,
            "fallback": 0.3,
            "error": 0.1
        }
        
        return source_scores.get(source, 0.5)
    
    def get_evaluation_history(self, limit: int = 10) -> List[Dict]:
        return self.evaluation_history[-limit:]

class IntelligentRouter:
    def __init__(self, evaluator: ResponseEvaluator):
        self.evaluator = evaluator
        self.routing_history = []
    
    def route_query(self, query: str, context: Optional[Dict] = None) -> str:
        context = context or {}
        query_lower = query.lower()
        
        routes = []
        
        tool_keywords = {
            "weather": ["weather", "temperature", "forecast"],
            "calculator": ["calculate", "math", "equation", "times", "plus", "minus"],
            "time": ["time", "current time", "what time", "date"],
            "web_search": ["search for", "find information about", "look up"]
        }
        
        tool_confidence = 0.0
        detected_tool = None
        
        for tool, keywords in tool_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                tool_confidence = 0.8
                detected_tool = tool
                break
        
        if tool_confidence > 0:
            routes.append(("tool", tool_confidence, f"Detected tool: {detected_tool}"))
        
        rag_keywords = ["what is", "who is", "explain", "tell me about", "define"]
        knowledge_queries = ["capital of", "founder of", "invented by", "located in"]
        
        rag_confidence = 0.0
        if any(keyword in query_lower for keyword in rag_keywords + knowledge_queries):
            rag_confidence = 0.7
            routes.append(("rag", rag_confidence, "Knowledge-based query"))
        
        complexity_indicators = [
            len(query.split()) > 10,
            "and" in query_lower and "or" in query_lower,
            any(word in query_lower for word in ["complex", "multiple", "various"]),
            "?" in query and " " in query.split("?")[0]
        ]
        
        react_confidence = sum(complexity_indicators) / len(complexity_indicators)
        if react_confidence > 0.5:
            routes.append(("react", react_confidence, "Complex query requiring reasoning"))
        
        direct_confidence = 0.6
        routes.append(("direct_llm", direct_confidence, "General query"))
        
        best_route = max(routes, key=lambda x: x[1])
        
        routing_decision = {
            "query": query,
            "selected_route": best_route[0],
            "confidence": best_route[1],
            "reason": best_route[2],
            "all_routes": routes,
            "timestamp": datetime.now().isoformat()
        }
        
        self.routing_history.append(routing_decision)
        
        return best_route[0]
    
    def get_routing_history(self, limit: int = 10) -> List[Dict]:
        return self.routing_history[-limit:]
