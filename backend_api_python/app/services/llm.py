"""
LLM service.
Wraps OpenRouter API calls and robust JSON parsing.
Kept separate from AnalysisService to avoid circular imports.
"""
import json
import requests
from typing import Dict, Any, Optional, List

from app.utils.logger import get_logger
from app.config import APIKeys
from app.utils.config_loader import load_addon_config

logger = get_logger(__name__)


class LLMService:
    """LLM provider wrapper."""

    def __init__(self):
        # Config may not be loaded yet during import time; we resolve lazily via properties.
        pass

    @property
    def api_key(self):
        return APIKeys.DEEPSEEK_API_KEY
        
    @property
    def openrouter_api_key(self):
        return APIKeys.OPENROUTER_API_KEY

    @property
    def base_url(self):
        config = load_addon_config()
        import os
        return config.get('deepseek', {}).get('base_url') or os.getenv('DEEPSEEK_BASE_URL', "https://api.deepseek.com")
        
    @property
    def openrouter_base_url(self):
        config = load_addon_config()
        import os
        return config.get('openrouter', {}).get('base_url') or os.getenv('OPENROUTER_BASE_URL', "https://openrouter.ai/api/v1")

    def call_llm_api(self, messages: list, model: str = None, temperature: float = 0.7, use_fallback: bool = True) -> str:
        """Dispatch to appropriate API provider."""
        config = load_addon_config()
        import os
        
        default_deepseek = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        default_openrouter = config.get('openrouter', {}).get('model', 'openai/gpt-4o')
        
        target_model = model
        if target_model is None:
            # Decide default provider based on what keys are available or env var
            if APIKeys.DEEPSEEK_API_KEY:
                target_model = default_deepseek
            else:
                target_model = default_openrouter
                
        # Heuristic: OpenRouter models usually have "provider/model" format (contains slash)
        # DeepSeek direct models are like "deepseek-chat" or "DeepSeek-..." (no slash usually, or we assume so for our specific ones)
        # Exception: "deepseek/deepseek-v3" is OpenRouter.
        
        is_openrouter = "/" in target_model
        
        # Override heuristic if specifically asking for our direct DeepSeek Speciale
        if target_model in ["DeepSeek-V3.2-Speciale", "deepseek-chat", "deepseek-reasoner"]:
            is_openrouter = False
            
        if is_openrouter:
            return self.call_openrouter_api(messages, target_model, temperature, use_fallback)
        else:
            return self.call_deepseek_api(messages, target_model, temperature, use_fallback)

    def call_deepseek_api(self, messages: list, model: str = None, temperature: float = 0.7, use_fallback: bool = True) -> str:
        """Call DeepSeek API."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not model:
            import os
            model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

        models_to_try = [model]
        fallback_models = ["deepseek-chat"]
        if use_fallback and model != "deepseek-chat":
            models_to_try.extend(fallback_models)

        last_error = None
        import os
        timeout = int(os.getenv('DEEPSEEK_TIMEOUT', 300))
        
        for current_model in models_to_try:
            try:
                data = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                    "stream": False
                }

                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                
                if response.status_code == 402:
                    logger.warning(f"DeepSeek returned 402 for model {current_model} (Payment Required)")
                    last_error = f"402 Payment Required"
                    continue
                
                response.raise_for_status()
                
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"DeepSeek API returned unexpected structure: {json.dumps(result)}")
                    raise ValueError("DeepSeek API response is missing 'choices'")
                    
            except Exception as e:
                logger.error(f"DeepSeek API error ({current_model}): {str(e)}")
                last_error = str(e)
                if current_model == models_to_try[-1]:
                    raise
        
        raise Exception(f"All DeepSeek model calls failed. Last error: {last_error}")

    def call_openrouter_api(self, messages: list, model: str = None, temperature: float = 0.7, use_fallback: bool = True) -> str:
        """Call OpenRouter API."""
        config = load_addon_config()
        openrouter_config = config.get('openrouter', {})
        url = f"{self.openrouter_base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://quantdinger.com", 
            "X-Title": "QuantDinger Analysis" 
        }

        models_to_try = [model] if model else [openrouter_config.get('model', 'openai/gpt-4o')]
        if use_fallback:
            models_to_try.append("openai/gpt-4o-mini")

        last_error = None
        timeout = int(openrouter_config.get('timeout', 120))
        
        for current_model in models_to_try:
            try:
                data = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"}
                }

                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                
                if response.status_code == 402:
                    logger.warning(f"OpenRouter returned 402 for model {current_model}")
                    last_error = f"402 Payment Required"
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise ValueError("OpenRouter API response is missing 'choices'")
                    
            except Exception as e:
                logger.error(f"OpenRouter API error ({current_model}): {str(e)}")
                last_error = str(e)
                if current_model == models_to_try[-1]:
                    raise

        raise Exception(f"All OpenRouter model calls failed. Last error: {last_error}")

    def safe_call_llm(self, system_prompt: str, user_prompt: str, default_structure: Dict[str, Any], model: str = None) -> Dict[str, Any]:
        """Safe LLM call with robust JSON parsing and fallback structure."""
        response_text = ""
        try:
            response_text = self.call_llm_api([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], model=model)
            
            # Strip markdown fences if present
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                first_newline = clean_text.find("\n")
                if first_newline != -1:
                    clean_text = clean_text[first_newline+1:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            result = json.loads(clean_text)
            return result
        except json.JSONDecodeError:
            logger.error(f"JSON parse failed. Raw text: {response_text[:200] if response_text else 'N/A'}")
            
            # Try extracting JSON substring
            try:
                if response_text:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        result = json.loads(response_text[start:end])
                        return result
            except:
                pass
            
            default_structure['report'] = f"Failed to parse analysis result JSON. Raw output (partial): {response_text[:500] if response_text else 'N/A'}"
            return default_structure
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            default_structure['report'] = f"Analysis failed: {str(e)}"
            return default_structure
