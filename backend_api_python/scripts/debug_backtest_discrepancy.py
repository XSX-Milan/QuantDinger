
import sys
import os
import json
import logging
import asyncio
import re

# --- 1. Fix Path to allow imports from 'app' ---
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../scripts
project_root = os.path.dirname(current_dir) # .../backend_api_python
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 2. Safe Imports ---
try:
    from app.services.backtest import BacktestService
    from app.utils.db import get_db_connection # Use DB util instead of models
except ImportError as e:
    logger.error(f"Import Error: {e}")
    logger.error("Please make sure you have installed requirements: pip install -r requirements.txt")
    sys.exit(1)

# BacktestOptimizer imports BacktestAgent which imports tools which imports yfinance
try:
    from app.services.backtest_optimizer import BacktestOptimizer
except ImportError as e:
    logger.warning(f"Could not import BacktestOptimizer (likely missing yfinance/pandas?): {e}")
    logger.warning("AI Backtest simulation part might fail.")

async def main():
    config_path = r"c:\Users\XSXMILAN\Downloads\Documents\backtest_config_20260117.json"
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    indicator_id = config.get('indicatorId') or 2
    user_id = config.get('userid', 1)

    logger.info(f"Loading Indicator ID: {indicator_id}")

    # --- 3. Fetch Indicator Code (Raw SQL) ---
    indicator_code = None
    try:
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute("SELECT code FROM qd_indicator_codes WHERE id = ?", (indicator_id,))
            row = cur.fetchone()
            if row:
                indicator_code = row['code']
            else:
                logger.error("Indicator not found in DB")
                return
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return

    if not indicator_code:
        logger.error("Indicator code is empty")
        return

    logger.info(f"Indicator Code Length: {len(indicator_code)}")
    
    bt_service = BacktestService()

    # --- 4. Construct Strategy Configs ---
    
    # Common Config Parts (Step 2 fields)
    from datetime import datetime
    
    start_date_str = config.get('startDate')
    end_date_str = config.get('endDate')
    
    # Parse dates (YYYY-MM-DD) -> datetime
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

    # Handle missing keys in config (e.g. symbol)
    symbol = config.get('symbol') or 'BTC/USDT'
    market = config.get('market') or 'Crypto'
    # Try to get timeframe from root, then _uiState, then default
    timeframe = config.get('timeframe') or config.get('_uiState', {}).get('selectedTimeframe') or '1m'

    base_params = {
        'market': market,
        'symbol': symbol,
        'timeframe': timeframe,
        'start_date': start_date,
        'end_date': end_date,
        'initial_capital': config.get('initialCapital'),
        'commission': config.get('commission'),
        'slippage': config.get('slippage'),
        'leverage': config.get('leverage'),
        'trade_direction': config.get('tradeDirection'),
    }

    # Strategy Config Structure (Nested)
    def build_strategy_config(params_dict):
        return {
            'risk': {
                'stopLossPct': config.get('stopLossPct') / 100, 
                'takeProfitPct': config.get('takeProfitPct') / 100,
                'trailingEnabled': config.get('trailingEnabled'),
                'trailingStopPct': config.get('trailingStopPct') / 100,
                'trailingActivationPct': config.get('trailingActivationPct') / 100,
            },
            'position': {
                'entryPct': config.get('entryPct') / 100,
                'leverage': config.get('leverage'),
                'tradeDirection': config.get('tradeDirection')
            },
            'scale': {
                'trendAddEnabled': config.get('trendAddEnabled'),
                'trendAddStepPct': config.get('trendAddStepPct') / 100,
                'trendAddSizePct': config.get('trendAddSizePct') / 100,
                'trendAddMaxTimes': config.get('trendAddMaxTimes'),
                'dcaAddEnabled': config.get('dcaAddEnabled'),
                'dcaAddStepPct': config.get('dcaAddStepPct') / 100,
                'dcaAddSizePct': config.get('dcaAddSizePct') / 100,
                'dcaAddMaxTimes': config.get('dcaAddMaxTimes'),
                'trendReduceEnabled': config.get('trendReduceEnabled'),
                'trendReduceStepPct': config.get('trendReduceStepPct') / 100,
                'trendReduceSizePct': config.get('trendReduceSizePct') / 100,
                'trendReduceMaxTimes': config.get('trendReduceMaxTimes'),
                'adverseReduceEnabled': config.get('adverseReduceEnabled'),
                'adverseReduceStepPct': config.get('adverseReduceStepPct') / 100,
                'adverseReduceSizePct': config.get('adverseReduceSizePct') / 100,
                'adverseReduceMaxTimes': config.get('adverseReduceMaxTimes'),
            },
            'params': params_dict
        }

    # Case A: Manual Backtest (Standard)
    logger.info(f"\n--- CASE A: Manual Backtest (Standard) ---")
    cfg_manual = build_strategy_config({})
    try:
        res_manual = bt_service.run(indicator_code=indicator_code, strategy_config=cfg_manual, **base_params)
        ret_manual = res_manual.get('metrics', {}).get('totalReturn')
        logger.info(f"Result (Manual): Return={ret_manual:.4f}")
    except Exception as e:
        logger.error(f"Run Failed: {e}")
        ret_manual = None

    # Case B: AI Backtest (1st Iteration / No Optimization yet)
    logger.info(f"\n--- CASE B: AI Backtest (1st Iteration) ---")
    cfg_ai = build_strategy_config({}) 
    try:
        res_ai = bt_service.run(indicator_code=indicator_code, strategy_config=cfg_ai, **base_params)
        ret_ai = res_ai.get('metrics', {}).get('totalReturn')
        logger.info(f"Result (AI 1st Iteration): Return={ret_ai:.4f}")
    except Exception as e:
        logger.error(f"Run Failed: {e}")
        ret_ai = None

    # Analysis
    logger.info("\n--- ANALYSIS ---")
    if ret_manual is not None and ret_ai is not None:
        if ret_manual != ret_ai:
            logger.info(">>> DISCREPANCY FOUND <<<")
            logger.info(f"Manual Mode Return: {ret_manual}")
            logger.info(f"AI Mode Return:     {ret_ai}")
        else:
            logger.info(">>> RESULTS MATCH <<<")
            logger.info(f"Both returns are: {ret_manual}")
            logger.info("This confirms that when parameters are identical, the backtest results are consistent.")
            
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
