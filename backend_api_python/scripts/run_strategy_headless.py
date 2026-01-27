
import os
import sys
import time
import logging
import json
import threading
from datetime import datetime
import warnings

# Suppress pandas deprecation warnings common in backtesting libs
warnings.simplefilter(action='ignore', category=FutureWarning)

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.db import get_db_connection
from app.services.trading_executor import TradingExecutor
from app.services.live_trading.factory import create_client
from app.services.exchange_execution import resolve_exchange_config

# Setup logging
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "trades.log")

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(log_file, encoding='utf-8')
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(log_format)
f_handler.setFormatter(log_format)

# Add handlers to the logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(c_handler)
root_logger.addHandler(f_handler)

logger = logging.getLogger("HeadlessStrategy")

CONFIG_FILE_PATH = r"c:\Users\XSXMILAN\Downloads\Documents\backtest_config_20260117 (1).json"
STRATEGY_ID = 2

def load_config_from_file():
    """Load and parse the JSON configuration file."""
    if not os.path.exists(CONFIG_FILE_PATH):
        logger.error(f"Config file not found: {CONFIG_FILE_PATH}")
        sys.exit(1)
        
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        logger.info(f"Loaded config from {CONFIG_FILE_PATH}")
        return data

def setup_strategy(config_data):
    """
    Update DB strategy with config from file and ensure live mode credentials.
    """
    logger.info(f"Configuring Strategy {STRATEGY_ID} for Headless Execution...")
    
    with get_db_connection() as db:
        cur = db.cursor()
        
        # 1. Fetch existing to preserve credentials
        cur.execute("SELECT exchange_config FROM qd_strategies_trading WHERE id = %s", (STRATEGY_ID,))
        row = cur.fetchone()
        
        existing_exch = {}
        if row and row['exchange_config']:
            try:
                existing_exch = json.loads(row['exchange_config'])
            except:
                pass

        # 2. Prepare Exchange Config (Force Demo + Resolve Credentials)
        # Use existing credential_id if present (prefer DB credentials)
        exchange_config = {
            "exchange_id": "binance",
            "market_type": "swap",
            "enableDemoTrading": True,
            "credential_id": existing_exch.get('credential_id', 1) # Default to 1 if missing
        }
        
        # 3. Prepare Trading Config from File
        # Map flat JSON to trading_config structure
        trading_config = {
            "symbol": config_data.get("symbol", "BTC/USDT"),
            "timeframe": config_data.get("timeframe", "1m"),
            "leverage": config_data.get("leverage", 5),
            "trade_direction": config_data.get("trade_direction", "both"),
            "initial_capital": config_data.get("initialCapital", 5000),
            
            # Risk
            "stop_loss_pct": config_data.get("stopLossPct", 0),
            "take_profit_pct": config_data.get("takeProfitPct", 0),
            "trailing_enabled": config_data.get("trailingEnabled", False),
            "trailing_stop_pct": config_data.get("trailingStopPct", 0),
            "trailing_activation_pct": config_data.get("trailingActivationPct", 0),
            
            # Scale
            "dca_enabled": config_data.get("dcaAddEnabled", False),
            "dca_max_times": config_data.get("dcaAddMaxTimes", 0),
            "dca_step_pct": config_data.get("dcaAddStepPct", 0),
            "dca_size_pct": config_data.get("dcaAddSizePct", 0),
            
            "trend_add_enabled": config_data.get("trendAddEnabled", False),
            "trend_add_max_times": config_data.get("trendAddMaxTimes", 0),
            "trend_add_step_pct": config_data.get("trendAddStepPct", 0),
            "trend_add_size_pct": config_data.get("trendAddSizePct", 0),

            "trend_reduce_enabled": config_data.get("trendReduceEnabled", False),
            "trend_reduce_max_times": config_data.get("trendReduceMaxTimes", 0),
            "trend_reduce_step_pct": config_data.get("trendReduceStepPct", 0),
            "trend_reduce_size_pct": config_data.get("trendReduceSizePct", 0),
            

            "adverse_reduce_enabled": config_data.get("adverseReduceEnabled", False),
            "adverse_reduce_max_times": config_data.get("adverseReduceMaxTimes", 0),
            "adverse_reduce_size_pct": config_data.get("adverseReduceSizePct", 0),
            "adverse_reduce_step_pct": config_data.get("adverseReduceStepPct", 0),

            # Fees
            "commission": config_data.get("commission", 0.0002),
            "slippage": config_data.get("slippage", 0),
            
            # Other
            "entry_pct": config_data.get("entryPct", 15)
        }
        
        # 4. Indicator Config (Use indicatorId from file)
        indicator_config = {
            "indicator_id": config_data.get("indicatorId", 2),
            "params": {} # Assuming params are inside the indicator Logic or defaults
            # If the JSON had params, we would map them here. 
            # The provided JSON has no explicit 'params' dict, just root level fields.
        }

        # 5. Update DB
        cur.execute("""
            INSERT INTO qd_strategies_trading 
            (id, strategy_name, strategy_type, status, execution_mode, exchange_config, trading_config, indicator_config)
            VALUES (%s, 'HeadlessStrategy', 'IndicatorStrategy', 'running', 'live', %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
            status='running',
            execution_mode='live', 
            exchange_config=excluded.exchange_config,
            trading_config=excluded.trading_config,
            indicator_config=excluded.indicator_config
        """, (
            STRATEGY_ID, 
            json.dumps(exchange_config), 
            json.dumps(trading_config), 
            json.dumps(indicator_config)
        ))
        
        db.commit()
        logger.info("Strategy configuration updated in DB.")
        
        # Log active config in Chinese
        log_config_in_chinese(trading_config)

def log_config_in_chinese(cfg):
    """Log strategy parameters in Chinese for clarity."""
    logger.info("================ 策略参数 ================")
    
    # 基础信息
    logger.info(f"交易对    : {cfg.get('symbol')}")
    logger.info(f"时间周期  : {cfg.get('timeframe')}")
    logger.info(f"杠杆倍数  : {cfg.get('leverage')}x")
    logger.info(f"初始资金  : {cfg.get('initial_capital')}")
    logger.info(f"交易方向  : {cfg.get('trade_direction')}")
    logger.info(f"入场比例  : {cfg.get('entry_pct')}%")
    
    # 止盈止损
    logger.info("--- 止盈止损 ---")
    logger.info(f"止盈比例  : {cfg.get('take_profit_pct')}%")
    logger.info(f"止损比例  : {cfg.get('stop_loss_pct')}%")
    if cfg.get('trailing_enabled'):
        logger.info(f"移动止盈  : 开启 (激活: {cfg.get('trailing_activation_pct')}%, 回撤: {cfg.get('trailing_stop_pct')}%)")
    else:
        logger.info(f"移动止盈  : 关闭")
        
    # 加仓逻辑
    logger.info("--- 仓位管理 ---")
    if cfg.get('dca_enabled'):
        logger.info(f"DCA加仓   : 开启 ({cfg.get('dca_max_times')}次, 步长-{cfg.get('dca_step_pct')}%, 加仓{cfg.get('dca_size_pct')}%)")
    else:
        logger.info(f"DCA加仓   : 关闭")
        
    if cfg.get('trend_add_enabled'):
        logger.info(f"趋势加仓  : 开启 ({cfg.get('trend_add_max_times')}次, 步长+{cfg.get('trend_add_step_pct')}%, 加仓{cfg.get('trend_add_size_pct')}%)")
    else:
        logger.info(f"趋势加仓  : 关闭")
        
    # 减仓逻辑
    if cfg.get('trend_reduce_enabled'):
        logger.info(f"趋势减仓  : 开启 ({cfg.get('trend_reduce_max_times')}次, 步长+{cfg.get('trend_reduce_step_pct')}%, 减仓{cfg.get('trend_reduce_size_pct')}%)")
    else:
        logger.info(f"趋势减仓  : 关闭")
        
    if cfg.get('adverse_reduce_enabled'):
        logger.info(f"逆势减仓  : 开启 ({cfg.get('adverse_reduce_max_times')}次, 步长-{cfg.get('adverse_reduce_step_pct')}%, 减仓{cfg.get('adverse_reduce_size_pct')}%)")
    else:
        logger.info(f"逆势减仓  : 关闭")

    logger.info("==========================================")

def run_strategy_loop():
    """
    Instantiate Executor and run simulation loop.
    """
    logger.info("Initializing TradingExecutor...")
    executor = TradingExecutor()
    
    # Force single run iteration
    logger.info("Starting strategy loop (Continuous monitoring)...")
    logger.info("You should see 'Detailed Signal Log' if signals are generated.")
    
    try:
        # We'll run it a few times or continuously. 
        # For 'reproduce' style, maybe just once? 
        # But 'Headless' implies running. Let's run for a fixed duration or N ticks.
        
        monitor_duration_sec = 60 # Run for 1 minute as a test driver
        start_time = time.time()
        
        # Run indefinitely until Ctrl+C
        while True:
            # Manually trigger the strategy logic for ID 2
            # TradingExecutor usually runs its own threads. 
            # We can rely on that if we start it, but here we want to direct control.
            
            # We will call _run_strategy_loop logic for one tick
            logger.info("--- Tick ---")
            
            # 1. Load context
            with get_db_connection() as db:
                cur = db.cursor()
                cur.execute("SELECT * FROM qd_strategies_trading WHERE id=%s", (STRATEGY_ID,))
                row = cur.fetchone()
                cur.close()
            
            if not row:
                logger.error("Strategy gone!")
                break
                
            # 2. Execute Strategy Logic (Mocking the worker thread essentially)
            try:
                # We reuse the logic from executor.py's _run_single_strategy or extract it.
                # But easiest is often to just let the executor do its thing if it has a method.
                # It doesn't exposed a public 'tick' method easily.
                
                # Let's inspect TradingExecutor to see if we can call anything public.
                # It has `start()` but that starts threads.
                # Let's just instantiate and start it, then tail logs?
                # No, user wants output IN THIS LOG.
                
                # We will manually invoke the internal method _run_strategy_loop logic
                # Actually, `executor.start_strategy(strategy_id)` spawns a thread.
                # We can call that and then just keep main thread alive.
                
                # BUT, to capture "decisions" in this console, we need to divert logs or print.
                # The executor uses `logger`, so we will see it here since we configured basicConfig.
                
                if STRATEGY_ID not in executor.running_strategies:
                     executor.start_strategy(STRATEGY_ID)
                     logger.info("Strategy thread started.")
                
                # 3. Log Remote Positions (Manual Check)
                try:
                    from app.services.exchange_execution import load_strategy_configs, resolve_exchange_config
                    cfg = load_strategy_configs(STRATEGY_ID)
                    exchange_config = resolve_exchange_config(cfg.get("exchange_config") or {})
                    market_type = str(cfg.get("market_type") or "swap").strip().lower()
                    
                    client = create_client(exchange_config, market_type=market_type)
                    
                    if hasattr(client, "get_positions"):
                        positions = client.get_positions()
                        # Unpack 'raw' if present (SDK wrapper)
                        if isinstance(positions, dict) and "raw" in positions:
                            positions = positions["raw"]
                            
                        if isinstance(positions, list):
                            active_pos = []
                            for p in positions:
                                amt = float(p.get('positionAmt') or p.get('size') or 0)
                                if abs(amt) > 0:
                                    sym = p.get('symbol') or p.get('instrument')
                                    active_pos.append(f"{sym}: {amt}")
                            
                            if active_pos:
                                logger.info(f"LIVE POSITIONS: {', '.join(active_pos)}")
                            else:
                                logger.info("LIVE POSITIONS: (None)")
                        else:
                             logger.info(f"LIVE POSITIONS: (Unknown format: {type(positions)})")
                except Exception as e:
                    logger.error(f"Position Check Error: {e}")

            except Exception as e:
                logger.error(f"Tick Error: {e}")
                
            time.sleep(5) # 5s interval
            
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        executor.stop_strategy(STRATEGY_ID)
        logger.info("Strategy stopped.")

if __name__ == "__main__":
    cfg = load_config_from_file()
    setup_strategy(cfg)
    run_strategy_loop()
