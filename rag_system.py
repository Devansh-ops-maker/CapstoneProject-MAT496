import os
import json
from typing import List, Dict, Any
from datetime import datetime
from config import config

class DynamicRAGSystem:
    def __init__(self):
        self.knowledge_base_path = config.knowledge_base_path
        self.documents = []
        self.learned_queries = {}
        self.setup_knowledge_base()
    
    def setup_knowledge_base(self):
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        self.knowledge_file = os.path.join(self.knowledge_base_path, "knowledge_base.json")
        self.learning_file = os.path.join(self.knowledge_base_path, "learned_queries.json")
        
        if os.path.exists(self.knowledge_file):
            self.load_knowledge_base()
        else:
            self.documents = []
            self.save_knowledge_base()
        
        if os.path.exists(self.learning_file):
            self.load_learned_queries()
    
    def load_knowledge_base(self):
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.documents = data.get("documents", [])
        except:
            self.documents = []
    
    def load_learned_queries(self):
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                self.learned_queries = json.load(f)
        except:
            self.learned_queries = {}
    
    def save_knowledge_base(self):
        try:
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "document_count": len(self.documents),
                    "source": "dynamic_learning"
                },
                "documents": self.documents
            }
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def save_learned_queries(self):
        try:
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_queries, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def learn_from_interaction(self, query: str, response: str, source: str):
        if len(response.split()) > 10:
            self.add_document({
                "content": f"Question: {query}\nAnswer: {response}",
                "source": f"learned_from_{source}",
                "learned_date": datetime.now().isoformat(),
                "confidence": 0.7
            })
            self._learn_query_pattern(query, response)
    
    def _learn_query_pattern(self, query: str, response: str):
        query_terms = self._extract_terms(query)
        response_terms = self._extract_terms(response)
        
        for q_term in query_terms:
            if q_term not in self.learned_queries:
                self.learned_queries[q_term] = []
            for r_term in response_terms:
                if r_term not in self.learned_queries[q_term]:
                    self.learned_queries[q_term].append(r_term)
        
        self.save_learned_queries()
    
    def _extract_terms(self, text: str) -> List[str]:
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        words = text.lower().split()
        return [word.strip('.,!?;:"()[]{}') for word in words 
                if len(word) > 3 and word not in stop_words]
    
    def add_document(self, document: Dict):
        if not isinstance(document, dict) or "content" not in document:
            return
        self.documents.append(document)
        self.save_knowledge_base()
    
    def search(self, query: str, k: int = None) -> List[Dict]:
        if k is None:
            k = config.top_k_retrieval
        
        enhanced_query = self._enhance_query_with_learning(query)
        query_terms = self._extract_terms(enhanced_query)
        
        results = []
        for doc in self.documents:
            score = self._calculate_dynamic_score(doc, query_terms, query)
            if score > 0:
                results.append({**doc, "relevance_score": score})
        
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:k]
    
    def _enhance_query_with_learning(self, query: str) -> str:
        query_terms = self._extract_terms(query)
        enhanced_terms = set(query_terms)
        
        for term in query_terms:
            if term in self.learned_queries:
                enhanced_terms.update(self.learned_queries[term][:3])
        
        return query + " " + " ".join(enhanced_terms)
    
    def _calculate_dynamic_score(self, document: Dict, query_terms: List[str], original_query: str) -> float:
        if not query_terms:
            return 0.0
        
        content = document.get("content", "").lower()
        term_matches = sum(1 for term in query_terms if term in content)
        term_score = term_matches / len(query_terms) if query_terms else 0
        
        recency_boost = 1.0
        if "learned_date" in document:
            try:
                learned_date = datetime.fromisoformat(document["learned_date"])
                days_ago = (datetime.now() - learned_date).days
                recency_boost = max(0.5, 1.0 - (days_ago / 30))
            except:
                pass
        
        source_confidence = document.get("confidence", 0.5)
        
        return term_score * recency_boost * source_confidence
    
    def query(self, question: str) -> str:
        relevant_docs = self.search(question)
        if not relevant_docs:
            return None
        context = "\n".join([doc["content"] for doc in relevant_docs[:2]])
        return context
    
    def get_statistics(self) -> Dict:
        sources = {}
        for doc in self.documents:
            source = doc.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "sources_distribution": sources,
            "learned_patterns": len(self.learned_queries),
            "last_updated": datetime.now().isoformat()
        }
