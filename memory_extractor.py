import re
from typing import Dict, Any

class MemoryExtractor:
    def __init__(self):
        self.patterns = [
            (r"my (?:name is|name's) (\w+)", "name"),
            (r"i am (\w+) years old", "age"),
            (r"i am from (\w+)", "location"),
            (r"my favorite (?:subject|color|food|movie) is (\w+)", "favorite"),
            (r"i (?:like|love|enjoy) (\w+)", "likes"),
            (r"i (?:hate|dislike) (\w+)", "dislikes"),
            (r"i work as (\w+)", "occupation"),
        ]
    
    def extract(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        
        for pattern, key in self.patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = match.group(1).strip()
                return {
                    "is_memory": True,
                    "key": f"{key}_{hash(value) % 1000}",
                    "value": value,
                    "type": key
                }
        
        memory_indicators = ["remember that", "don't forget", "my"]
        if any(indicator in query_lower for indicator in memory_indicators):
            if "is" in query_lower:
                parts = query_lower.split(" is ")
                if len(parts) == 2:
                    key_part = parts[0].replace("my ", "").replace("remember that ", "").strip()
                    value_part = parts[1].strip()
                    if key_part and value_part:
                        return {
                            "is_memory": True,
                            "key": f"custom_{hash(key_part) % 1000}",
                            "value": f"{key_part}: {value_part}",
                            "type": "custom"
                        }
        
        return {"is_memory": False}
    
    def close(self):
        pass
