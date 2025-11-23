import openai
from typing import List, Dict, Optional
import json
from config import config

class LLMClient:
    def __init__(self):
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.model = config.model_name
        self.temperature = config.temperature
    
    def generate(self, prompt: str, system_message: Optional[str] = None, max_tokens: int = 500) -> str:
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({"role": "system", "content": "You are a helpful assistant."})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def chat_completion(self, messages: List[Dict], max_tokens: int = 500) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in chat completion: {str(e)}"
    
    def generate_structured(self, prompt: str, response_format: Dict) -> Dict:
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that outputs structured data."},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format=response_format
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}
