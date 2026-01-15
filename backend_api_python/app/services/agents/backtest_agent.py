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
        直接替换代码中的参数值（不使用 LLM）
        使用正则表达式匹配并替换参数赋值语句
        """
        import re
        
        lines = code.split('\n')
        updated_lines = []
        
        for line in lines:
            updated_line = line
            
            # 对每个参数尝试匹配和替换
            for param_name, param_value in params.items():
                # 匹配模式：param_name = value  (可选注释)
                # 捕获：(缩进)(参数名)(=)(旧值)(可选注释)
                pattern = rf'^(\s*){re.escape(param_name)}\s*=\s*(.+?)(\s*#.*)?$'
                match = re.match(pattern, line)
                
                if match:
                    indent = match.group(1)  # 保持原有缩进
                    comment = match.group(3) or ''  # 保持原有注释
                    
                    # 构造新的赋值语句
                    updated_line = f"{indent}{param_name} = {param_value}{comment}"
                    break  # 一行只替换一次
            
            updated_lines.append(updated_line)
        
        return '\n'.join(updated_lines)
