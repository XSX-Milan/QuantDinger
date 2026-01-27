"""
Backtest Optimizer Service
Manages async optimization jobs.
"""
import threading
import uuid
import time
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from app.services.backtest import BacktestService
from app.services.agents.backtest_agent import BacktestAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OptimizationJob:
    def __init__(self, job_id, config, strategy_code, target_metric, max_iterations, model=None):
        self.id = job_id
        self.config = config
        self.strategy_code = strategy_code
        self.target_metric = target_metric
        self.max_iterations = max_iterations
        self.model = model
        
        self.status = "pending"  # pending, running, paused, completed, failed, cancelled
        self.current_iteration = 0
        self.best_result = None
        self.history = []  # List of {iteration, params, metrics, reasoning}
        self.logs = []     # List of str logs
        self.error = None
        
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set() # Set means NOT paused (wait returns immediately)

    def log(self, message):
        ts = datetime.now().strftime('%H:%M:%S')
        entry = f"[{ts}] {message}"
        self.logs.append(entry)
        # Keep logs manageable
        if len(self.logs) > 500:
            self.logs.pop(0)

class BacktestOptimizer:
    _instance = None
    _jobs: Dict[str, OptimizationJob] = {}
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BacktestOptimizer, cls).__new__(cls)
            cls._instance.backtest_service = BacktestService()
            cls._instance.agent = BacktestAgent()
        return cls._instance

    def start_optimization(self, data: Dict[str, Any]) -> str:
        """
        Start a new optimization job.
        Args:
            data: {
                "config": dict,          # Initial backtest config
                "strategy_code": str,     # Python code (optional if built-in)
                "target_metric": str,     # e.g., 'sharpeRatio'
                "max_iterations": int     # e.g., 10
            }
        Returns:
            job_id
        """
        job_id = str(uuid.uuid4())
        job = OptimizationJob(
            job_id=job_id,
            config=data.get('config', {}),
            strategy_code=data.get('strategy_code', ''),
            target_metric=data.get('target_metric', 'totalReturn'),
            max_iterations=int(data.get('max_iterations', 10)),
            model=data.get('model')
        )
        
        with self._lock:
            self._jobs[job_id] = job
            
        thread = threading.Thread(target=self._run_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return job_id

    def get_job(self, job_id: str) -> Optional[OptimizationJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def control_job(self, job_id: str, action: str) -> bool:
        """
        Control job state: pause, resume, stop.
        """
        job = self.get_job(job_id)
        if not job:
            return False
            
        if action == 'pause':
            job._pause_event.clear() # Blocks wait()
            job.status = 'paused'
            job.log("Job paused by user.")
        elif action == 'resume':
            job._pause_event.set()   # Unblocks wait()
            job.status = 'running'
            job.log("Job resumed.")
        elif action == 'stop':
            job._stop_event.set()
            job.status = 'cancelled'
            job.log("Job cancelled by user.")
            
        return True

    def _run_job(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return
            
        job.status = "running"
        job.log(f"Starting optimization. Target: {job.target_metric}, Max Iterations: {job.max_iterations}, Model: {job.model or 'Default'}")
        
        current_params = job.config
        
        # Initial Run (Baseline)
        
        # Pre-Analyze Strategy Code (for AI Context)
        # Avoid re-analyzing if resuming (checking hasattr)
        if not hasattr(job, 'strategy_analysis'):
           code = job.config.get('strategy_code')
           # If not in config, maybe passed in optimization_data but lost? 
           # BacktestOptimizer.start_optimization stores it in job init.
           if not code:
               code = getattr(job, 'strategy_code', None)

           if code: 
               job.log("Agent is analyzing strategy code (One-time)...")
               logger.info(f"Analyzing strategy code for job {job.id}")
               t0 = time.time()
               try:
                   analysis_result = self.agent.analyze_code(code, model=job.model)
                   
                   if isinstance(analysis_result, dict):
                       job.strategy_analysis = analysis_result.get('summary', 'Analysis success')
                       job.strategy_params_def = analysis_result.get('params', {})
                       job.strategy_code_rewritten = analysis_result.get('rewritten_code', code)
                       
                       # Merge params
                       if job.strategy_params_def:
                           for k, v in job.strategy_params_def.items():
                               if k not in current_params:
                                   current_params[k] = v
                   else:
                       job.strategy_analysis = analysis_result
                       job.strategy_params_def = {}
                       job.strategy_code_rewritten = code
                   dur = time.time() - t0
                   job.log(f"Strategy analysis complete ({dur:.1f}s)")
                   job.log(f"Strategy Analysis: {job.strategy_analysis}")
               except Exception as e:
                   logger.error(f"Strategy analysis failed: {e}")
                   job.log(f"Strategy analysis failed: {e}")
                   job.strategy_analysis = "Analysis failed."
           else:
               job.strategy_analysis = "No strategy code provided."

        try:
            job.log("Running baseline backtest...")
            result = self._run_backtest(job, current_params)
            last_result = result
            
            # Capture Market Context
            market_context = result.get('market_context', {})
            job.market_context = market_context
            if market_context:
                trend = market_context.get('trend', 'Unknown')
                vol = market_context.get('volatility_std', 0)
                job.log(f"Market Analysis: {trend} Trend, Volatility: {vol:.2f}%")
            
            self._record_result(job, 0, current_params, result, "Baseline run")
            job.best_result = {
                "params": current_params,
                "metrics": result.get('metrics', {})
            }
            job.log(f"Baseline Result: {job.target_metric}={job.best_result['metrics'].get(job.target_metric)}")
            
            # Log detailed trades for baseline
            self._log_detailed_trades(job, result.get('trades', []))
            
        except Exception as e:
            job.error = str(e)
            job.status = "failed"
            job.log(f"Baseline failed: {str(e)}")
            logger.error(f"Optimization Job {job_id} failed: {traceback.format_exc()}")
            self._cleanup_job_cache(job) # Cleanup on failure
            return


        # Optimization Loop
        for i in range(1, job.max_iterations + 1):
            if job._stop_event.is_set():
                break
                
            # Handle Pause
            if not job._pause_event.is_set():
                job.log("Waiting for resume...")
                job._pause_event.wait()
                if job._stop_event.is_set(): # Check again after wait
                    break
            
            job.current_iteration = i
            job.log(f"--- Iteration {i} ---")
            
            try:
                # 1. Ask Agent for Params
                best_val = job.best_result['metrics'].get(job.target_metric, -999) if job.best_result else -999
                job.log(f"Agent is analyzing history (Current best {job.target_metric}: {best_val})...")
                logger.info(f"Job {job.id} Iteration {i}: Agent analyzing {len(job.history)} historical results, model: {job.model}")
                
                # Prepare Context
                last_trades = last_result.get('trades', [])
                trades_summary = self._summarize_trades(last_trades)
                
                context = {
                    "target_metric": job.target_metric,
                    "history": job.history,
                    "current_best": job.best_result,
                    "market_context": getattr(job, 'market_context', {}),
                    "last_trades_summary": trades_summary,
                    "strategy_analysis": getattr(job, 'strategy_analysis', ''), # Pass pre-analyzed strategy
                    "language": "zh-CN", # TODO: Make configurable
                    "model": job.model
                }
                
                t0 = time.time()
                agent_resp = self.agent.analyze(context)
                duration_agent = time.time() - t0
                job.log(f"Agent analysis took {duration_agent:.1f}s")
                logger.info(f"Job {job.id} Iteration {i}: Agent analysis completed in {duration_agent:.1f}s")
                
                agent_data = agent_resp.get('data', {})
                reasoning = agent_data.get('reasoning', '')
                suggested_params = agent_data.get('suggested_params', {})
                
                if not suggested_params:
                    job.log("Agent failed to suggest parameters. Retrying...")
                    continue
                    
                job.log(f"Agent Hypothesis: {reasoning}")
                logger.info(f"Job {job.id} Iteration {i} - Agent Hypothesis: {reasoning}")
                
                # Merge suggested params with base config (preserve other fields)
                next_config = current_params.copy()
                next_config.update(suggested_params)
                
                # 2. Run Backtest
                job.log(f"Running backtest with params: {json.dumps(next_config)}")
                logger.info(f"Job {job.id} Iteration {i} - Parameters: {json.dumps(suggested_params)}")
                
                # Log Optimized Strategy Params
                if getattr(job, 'strategy_params_def', None):
                    strat_params = {k: next_config.get(k) for k in job.strategy_params_def.keys() if k in next_config}
                    if strat_params:
                        job.log(f"Optimized Strategy Params: {json.dumps(strat_params)}")
                t1 = time.time()
                result = self._run_backtest(job, next_config)
                duration_bt = time.time() - t1
                job.log(f"Backtest execution took {duration_bt:.1f}s")
                
                # Log detailed trades for this iteration
                self._log_detailed_trades(job, result.get('trades', []))
                
                metrics = result.get('metrics', {})
                
                # 3. Record & Compare
                last_result = result # Update for next iteration context
                self._record_result(job, i, suggested_params, result, reasoning)
                # Compare with best result
                current_val = metrics.get(job.target_metric, -999)
                current_val = -999 if current_val is None else current_val
                
                best_metrics = job.best_result.get('metrics', {}) if job.best_result else {}
                best_val = best_metrics.get(job.target_metric, -999)
                best_val = -999 if best_val is None else best_val
                
                if current_val > best_val:
                    job.log(f"New Best Found! {job.target_metric}: {best_val} -> {current_val}")
                    job.best_result = {
                        "params": next_config,
                        "metrics": metrics
                    }
                else:
                    job.log(f"Result ({current_val}) did not beat best ({best_val}).")
                    
            except Exception as e:
                job.log(f"Iteration {i} Error: {e}")
                logger.error(f"Job {job_id} Iteration {i} failed: {e}")
                # Continue to next iteration instead of stopping
                
        if job.status != 'cancelled':
            job.status = "completed"
            job.log(f"Optimization complete. Best {job.target_metric}: {job.best_result['metrics'].get(job.target_metric)}")
        
        # Cleanup cache
        self._cleanup_job_cache(job)

    def _run_backtest(self, job: OptimizationJob, config: Dict) -> Dict:
        """Helper to run actual backtest service."""
        # Extract base parameters
        market = config.get('market')
        symbol = config.get('symbol')
        timeframe = config.get('selectedTimeframe') or config.get('timeframe', '1d')
        
        # Parse dates
        start_date_str = config.get('startDate')
        end_date_str = config.get('endDate')
        
        # Handle JS ISO string or YYYY-MM-DD
        def parse_date(d):
            if isinstance(d, datetime): return d
            try:
                if 'T' in d: # ISO format
                    return datetime.fromisoformat(d.replace('Z', '+00:00'))
                return datetime.strptime(d[:10], '%Y-%m-%d')
            except:
                return datetime.now()

        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        
        # Transform flat config to nested structure expected by backtest engine
        # Frontend sends: {stopLossPct: 0.1, takeProfitPct: 0.2, ...}
        # But engine expects: {risk: {stopLossPct: 0.1}, position: {entryPct: 1.0}, ...}
        # Identify strategy params based on Agent's analysis
        strategy_params_def = getattr(job, 'strategy_params_def', {})
        dynamic_params = {}
        if strategy_params_def:
            for k in strategy_params_def.keys():
               if k in config:
                   dynamic_params[k] = config[k]

        strategy_config = {
            "params": dynamic_params, # Inject Strategy Params (Do NOT convert these, e.g. rsi_len)
            "risk": {
                "stopLossPct": float(config.get('stopLossPct', 0)),
                "takeProfitPct": float(config.get('takeProfitPct', 0)),
                "trailing": {
                    "enabled": config.get('trailingEnabled', False),
                    "pct": float(config.get('trailingStopPct', 0)),
                    "activationPct": float(config.get('trailingActivationPct', 0)),
                }
            },
            "position": {
                "entryPct": float(config.get('entryPct', 1.0)), # Expecting 0~1 (e.g. 0.25 for 25%)
            },
            "scale": {
                "trendAdd": {
                    "enabled": config.get('trendAddEnabled', False),
                    "stepPct": float(config.get('trendAddStepPct', 0)),
                    "sizePct": float(config.get('trendAddSizePct', 0)),
                    "maxTimes": config.get('trendAddMaxTimes', 0),
                },
                "dcaAdd": {
                    "enabled": config.get('dcaAddEnabled', False),
                    "stepPct": float(config.get('dcaAddStepPct', 0)),
                    "sizePct": float(config.get('dcaAddSizePct', 0)),
                    "maxTimes": config.get('dcaAddMaxTimes', 0),
                },
                "trendReduce": {
                    "enabled": config.get('trendReduceEnabled', False),
                    "stepPct": float(config.get('trendReduceStepPct', 0)),
                    "sizePct": float(config.get('trendReduceSizePct', 0)),
                    "maxTimes": config.get('trendReduceMaxTimes', 0),
                },
                "adverseReduce": {
                    "enabled": config.get('adverseReduceEnabled', False),
                    "stepPct": float(config.get('adverseReduceStepPct', 0)),
                    "sizePct": float(config.get('adverseReduceSizePct', 0)),
                    "maxTimes": config.get('adverseReduceMaxTimes', 0),
                }
            }
        }
        
        # Run Backtest with transformed config
        return self.backtest_service.run(
            indicator_code=getattr(job, 'strategy_code_rewritten', job.strategy_code),
            market=market,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(config.get('initialCapital', 10000)),
            commission=float(config.get('commission', 0.0002)), # Default 0.02% -> 0.0002
            slippage=float(config.get('slippage', 0.0)),
            leverage=int(config.get('leverage', 1)),
            trade_direction=config.get('tradeDirection', 'both'),
            strategy_config=strategy_config,  # Use transformed nested config
            cache_key=job.id  # Use job_id as cache key
        )

    def _record_result(self, job, iteration, params, result, reasoning):
        with self._lock:
            # Convert decimal metrics to percentage for AI analysis
            metrics_raw = result.get('metrics', {})
            metrics_for_ai = self._convert_metrics_to_percentage(metrics_raw)
            
            job.history.append({
                "iteration": iteration,
                "params": params,
                "metrics": metrics_for_ai,
                "reasoning": reasoning
            })
    
    def _convert_metrics_to_percentage(self, metrics: dict) -> dict:
        """Convert decimal metrics (0.5) to percentage (50) for AI display."""
        if not metrics:
            return metrics
        
        converted = metrics.copy()
        # Convert these metrics from decimal to percentage
        percentage_fields = ['totalReturn', 'annualReturn', 'maxDrawdown', 'winRate']
        
        for field in percentage_fields:
            if field in converted and converted[field] is not None:
                # Convert decimal to percentage: 0.5 -> 50
                converted[field] = round(converted[field] * 100, 2)
        
        return converted
    
    def _cleanup_job_cache(self, job: OptimizationJob):
        """Clean up cached K-line data for completed/failed job"""
        try:
            from app.services.backtest import BacktestService
            BacktestService.cleanup_cache(job.id)
            logger.info(f"Cleaned up cache for job {job.id}")
        except Exception as e:
            logger.error(f"Failed to cleanup cache for job {job.id}: {e}")

    def _log_detailed_trades(self, job: OptimizationJob, trades: List[Dict]):
        """在日志中记录交易详情"""
        if not trades:
            job.log("No trades executed.")
            return

        job.log(f"Total Trades: {len(trades)}")
        
        # Helper to format trade log
        def format_trade(idx, t):
            # BacktestService returns trade events
            time_str = t.get('time', 'N/A')
            type_str = t.get('type', 'unknown')
            price = t.get('price', 0)
            amount = t.get('amount', 0)
            profit = t.get('profit', 0)
            balance = t.get('balance', 0)
            
            return f"Trade #{idx+1}: {type_str} @ {time_str} | Price: {price} | Amt: {amount} | Profit: {profit} | Bal: {balance}"

        # Log all trades
        for i in range(len(trades)):
            job.log(format_trade(i, trades[i]))

    def _summarize_trades(self, trades: List[Dict]) -> str:
        """Generate a concise summary of trades for LLM context."""
        if not trades:
            return "No trades executed."
        
        # Take last 30 trades to be safe with context window
        recent_trades = trades[-30:]
        
        lines = []
        for i, t in enumerate(recent_trades):
            raw_type = t.get('type', 'unknown')
            profit = t.get('profit', 0)
            price = t.get('price', 0)
            amount = t.get('amount', 0)
            time_str = t.get('time', '')
            
            # Simplify type display
            action = raw_type
            if "close_long" in raw_type: action = "Close Long"
            elif "close_short" in raw_type: action = "Close Short"
            elif "open_long" in raw_type: action = "Open Long"
            elif "open_short" in raw_type: action = "Open Short"
            elif "liquidation" in raw_type: action = "LIQUIDATION"
            
            lines.append(f"{time_str} {action}: Price={price}, Amt={amount}, Profit={profit}")
            
        return "\n".join(lines)

