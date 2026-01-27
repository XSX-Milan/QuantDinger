"""
Backtest Optimization Agent
"""
from typing import Dict, Any, List
import json
from .base_agent import BaseAgent
from app.services.llm import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BacktestAgent(BaseAgent):
    """
    Agent responsible for optimizing backtest parameters.
    It analyzes previous backtest results and suggests new parameter sets.
    """
    
    def __init__(self, memory=None):
        super().__init__("BacktestAgent", memory)
        self.llm_service = LLMService()

    def analyze_code(self, code: str, language: str = 'zh-CN', model: str = None) -> Dict[str, Any]:
        """Analyze strategy code logic."""
        lang_instruction = "Answer in Simplified Chinese." if language == 'zh-CN' else "Answer in English."
        
        system_prompt = f"""You are an expert Quantitative Strategy Analyst. 
Your task is to analyze Python trading strategy code.
{lang_instruction}

Output ONLY valid JSON format:
{{
  "summary": "Concise summary of logic, parameters, and risk management (under 200 words).",
  "params": {{ "rsi_len": 14, "std_dev": 2.0 }}, // Identified tunable parameters with default values
  "rewritten_code": "The python code where variable assignments are replaced with params.get()..."
}}

Example Rewriting:
Original:
rsi_len = 14
ma_len = 20

Rewritten:
rsi_len = params.get('rsi_len', 14)
ma_len = params.get('ma_len', 20)
"""
        user_prompt = f"""Please analyze this code:
```python
{code}
```
Explain:
1. Core Logic (Indicators, Entry/Exit)
2. Key Parameters
3. Risk Management
"""
        
        result = self.llm_service.safe_call_llm(
             system_prompt,
             user_prompt,
             {"summary": "Strategy analysis failed."},
             model=model
        )

        
        # Fallback if result is not a dict
        if not isinstance(result, dict):
            try:
                result = json.loads(result)
            except:
                result = {"summary": str(result)}
        
        # Ensure keys exist
        if 'params' not in result:
             result['params'] = {}
        if 'rewritten_code' not in result:
             result['rewritten_code'] = code # Fallback to original code
             
        return result

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest next set of parameters based on history.
        
        Args:
            context:
                - target_metric: 'totalReturn', 'sharpeRatio', etc.
                - history: List[Dict] - [{params, metrics, iteration}, ...]
                - current_best: Dict - {params, metrics}
                - constraints: Dict - {stopLossPct: {min, max}, ...} (Optional)
                - language: str 'zh-CN'
                
        Returns:
            {
                "suggested_params": Dict,
                "reasoning": str
            }
        """
        history = context.get('history', [])
        target_metric = context.get('target_metric', 'totalReturn')
        language = context.get('language', 'zh-CN')
        model = context.get('model')
        
        # Format history for prompt
        history_str = self._format_history(history, target_metric)
        
        # Extract new context
        market_ctx = context.get('market_context', {})
        trades_summary = context.get('last_trades_summary', 'No trades available yet.')
        strategy_analysis = context.get('strategy_analysis', 'N/A')
        
        # Format Market Stats
        market_str = "N/A"
        if market_ctx:
             market_str = f"Trend: {market_ctx.get('trend', 'N/A')}, Return: {market_ctx.get('total_return_pct', 0)}%, Volatility: {market_ctx.get('volatility_std', 0)}%"

        lang_instruction = "Answer in Simplified Chinese." if language == 'zh-CN' else "Answer in English."

        system_prompt = f"""You are an expert Quantitative Strategy Optimizer. Your goal is to optimize the trading strategy parameters to maximize the '{target_metric}'.
{lang_instruction}

You will receive:
1. Strategy Logic: A summary of the core strategy code.
2. Market Context: Overview of market conditions (Trend, Volatility).
3. Optimization History: Past parameters and results.
4. Last Run Trades: A summary of recent trades from the last iteration.

Analyze the relationship between parameters and performance, considering the Strategy Logic and Market Conditions.
(e.g., if Strategy is Trend Following and Market is Range Bound, suggest parameters to filter noise).

Use "Reasoning" to explain your hypothesis.
 Then provide the "Next Parameters".
 
**Constraints:**
- Risk Parameters (stopLossPct, takeProfitPct, trailingStopPct): 0.0 - 50.0.
- Strategy Parameters (e.g., rsi_len, window, threshold): OPTIMIZE THESE! Modify values if they appear in history.
- Only modify parameters present in the history. Do NOT invent new keys.

Response JSON Format:
{{
  "reasoning": "Analysis of previous runs and hypothesis...",
  "suggested_params": {{
    "stopLossPct": 1.5,
    "takeProfitPct": 3.0,
    ...
  }}
}}
"""

        user_prompt = f"""Target Metric: {target_metric} (Higher is better)

**Strategy Analysis:**
{strategy_analysis}

**Market Context:**
{market_str}

**Optimization History (Latest First):**
{history_str}

**Last Run Trades (Summary):**
{trades_summary}

Please suggest the next set of parameters to improve {target_metric}."""

        # Default fallback
        fallback_params = {}
        if history:
            fallback_params = history[0].get('params', {})

        result = self.llm_service.safe_call_llm(
            system_prompt,
            user_prompt,
            {"reasoning": "Failed to generate parameters", "suggested_params": fallback_params},
            model=model
        )
        
        return {
            "type": "optimization",
            "data": result
        }

    def _format_history(self, history: List[Dict], target_metric: str) -> str:
        if not history:
            return "No history yet. Propose initial safe parameters."
        
        lines = []
        # Take last 10 runs to avoid context overflow, plus the Best Run if not included
        relevant_history = history[-10:]
        
        for item in reversed(relevant_history):
            metrics = item.get('metrics', {})
            params = item.get('params', {})
            lines.append(f"Iteration {item.get('iteration')}:")
            lines.append(f"  Result: {target_metric}={metrics.get(target_metric, 'N/A')}, WinRate={metrics.get('winRate', 'N/A')}%")
            lines.append(f"  Params: {json.dumps(params, ensure_ascii=False)}")
            lines.append("---")
            
        return "\n".join(lines)

    def apply_params_to_code(self, code: str, params: Dict[str, Any], model: str = None) -> str:
        """
        Update strategy code with new parameters.
        Hybrid approach:
        1. Use regex to update EXISTING parameters (preserves comments/formatting).
        2. Insert NEW parameters after imports (with '# AI Added' comment).
        """
        import re

        lines = code.split('\n')
        updated_lines = []
        replaced_params = set()

        # Phase 1: Regex Replacement
        for line in lines:
            updated_line = line
            for param_name, param_value in params.items():
                if param_name in replaced_params:
                    continue

                # Pattern: start_of_line + indent + param_name + spaces + = + spaces + value + (comment)
                # We use re.escape for the param name to handle any special chars safely
                pattern = rf'^(\s*){re.escape(param_name)}\s*=\s*(.+?)(\s*#.*)?$'
                match = re.match(pattern, line)

                if match:
                    indent = match.group(1)
                    # Group 2 is the old value, we discard it
                    comment = match.group(3) or ''
                    
                    # Use repr to safely format values (e.g. adds quotes for strings)
                    formatted_value = repr(param_value)
                    
                    updated_line = f"{indent}{param_name} = {formatted_value}{comment}"
                    replaced_params.add(param_name)
                    break # Only one replacement per line

            updated_lines.append(updated_line)

        # Phase 2: Insert New Parameters
        new_params = {k: v for k, v in params.items() if k not in replaced_params}
        
        if new_params:
            insert_index = 0
            # Heuristic: Find first line that is NOT an import or empty/comment, 
            # but usually we want to insert AFTER imports.
            # State machine: 
            # 0: Start
            # 1: Found imports
            # 2: Found code -> INSERT HERE
            
            # Simplified approach: Look for the last import line
            last_import_index = -1
            for i, line in enumerate(updated_lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    last_import_index = i
            
            # If imports found, insert after the last one
            if last_import_index != -1:
                insert_index = last_import_index + 1
            else:
                # No imports, try to insert at top, but skip initial comments/docstrings is better
                # For now, inserting at 0 is safe enough for simple scripts, 
                # or maybe after the first docstring?
                # Let's just stick to 0 or after last import.
                insert_index = 0

            # Prepare injection lines
            injection_lines = []
            
            # Add a blank line separator if we are inserting after something
            if insert_index > 0 and insert_index < len(updated_lines) and updated_lines[insert_index-1].strip() != '':
                 injection_lines.append('')
            
            for k, v in new_params.items():
                injection_lines.append(f"{k} = {repr(v)}  # AI Added")
            
            # Add a blank line after our block if needed
            if insert_index < len(updated_lines) and updated_lines[insert_index].strip() != '':
                injection_lines.append('')
                
            # Insert into the list
            updated_lines[insert_index:insert_index] = injection_lines

        return '\n'.join(updated_lines)
