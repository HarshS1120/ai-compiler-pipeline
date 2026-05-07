"""LLM interaction utilities using Groq"""
from groq import Groq
import json
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMHelper:
    def __init__(self, model: str = None):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Available models for reference
        self.available_models = [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
    
    def complete(self, 
                 system_prompt: str, 
                 user_prompt: str,
                 temperature: float = 0.1,
                 max_tokens: int = 4000,
                 json_mode: bool = True) -> Dict[str, Any]:
        """Make an LLM call with structured output expectation"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                # Groq doesn't have native JSON mode, but we can request it in prompt
            )
            
            content = response.choices[0].message.content
            
            # Log token usage
            usage = response.usage
            logger.info(f"Tokens used - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
            
            # Try to parse as JSON
            if json_mode:
                return self._parse_json(content)
            else:
                return {"content": content}
                
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with cleanup"""
        # Remove markdown code blocks if present
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
            
            # Try to extract JSON from the content
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            
            # Return error with raw content
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
        import time
        
        for attempt in range(max_retries):
            result = self.complete(system_prompt, user_prompt, **kwargs)
            
            if "error" not in result:
                return result
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            
            # Add delay before retry
            time.sleep(1)
            
            # Make the prompt more strict on retry
            user_prompt += f"\n\nIMPORTANT: You MUST respond with ONLY valid JSON. Previous attempt failed with: {result.get('parse_error', 'Unknown error')}"
        
        return result