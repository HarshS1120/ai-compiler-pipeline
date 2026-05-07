"""LLM interaction utilities using Groq REST API"""
import json
import os
import time
import logging
import httpx
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()
logger = logging.getLogger(__name__)

class LLMHelper:
    def __init__(self, model: str = None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.base_url = "https://api.groq.com/openai/v1"
    
    def complete(self, 
                 system_prompt: str, 
                 user_prompt: str,
                 temperature: float = 0.1,
                 max_tokens: int = 4000,
                 json_mode: bool = True) -> Dict[str, Any]:
        """Make an LLM call using Groq REST API directly"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            if json_mode:
                return self._parse_json(content)
            else:
                return {"content": content}
                
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with cleanup"""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            
            return {
                "error": "JSONParseError",
                "raw_output": content,
                "parse_error": str(e)
            }
    
    def complete_with_retry(self,
                           system_prompt: str,
                           user_prompt: str,
                           max_retries: int = 3,
                           **kwargs) -> Dict[str, Any]:
        """Complete with automatic retry on JSON parse failure"""
        for attempt in range(max_retries):
            result = self.complete(system_prompt, user_prompt, **kwargs)
            
            if "error" not in result:
                return result
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(1)
        
        return result