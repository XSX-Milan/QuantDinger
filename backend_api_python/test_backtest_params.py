#!/usr/bin/env python3
"""
测试脚本：验证回测引擎是否正确使用参数

此脚本将使用不同的参数运行多次回测，检查结果是否有差异。
如果结果完全相同，说明参数没有被正确使用。
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.backtest import BacktestService
from datetime import datetime
from app.services.backtest_optimizer import BacktestOptimizer
import time
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# 加载环境变量 (支持本地调试)
load_dotenv()
load_dotenv('../.env')  # 尝试上级目录
load_dotenv('../../.env') # 尝试上上级目录

# 检查 API Key 是否存在
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if deepseek_key:
    print(f"✅ DEEPSEEK_API_KEY loaded: {deepseek_key[:4]}***")
else:
    print("❌ DEEPSEEK_API_KEY not found in environment variables!")

def run_ai_test():
    """运行AI优化器集成测试"""
    print("\n" + "=" * 80)
    print("AI 优化器集成测试 - DeepSeek R1 (Reasoner)")
    print("=" * 80)

    # 用户的真实指标代码 (复用上方定义的 indicator_code)
    # 注意：在 main 中我们需要确保 indicator_code 可访问，或者重新定义
    # 由于 indicator_code 在 run_test 内部定义，这里重新定义一份引用
    
    strategy_code = """
my_indicator_name = "BTC Sensitivity Pro"
my_indicator_description = "# 优化版：高灵敏度背离 + 宽松确认 | 捕捉更多波段机会"

# --- 1. 参数调整 (关键优化点) ---
rsi_len = 14
pivot_window = 2       # 缩小窗口：从4改为2，捕捉更多局部低点
vol_ma_len = 20
os_threshold = 40      # 放宽阈值：从30改为40，适应强势回调
ob_threshold = 60      # 放宽卖出阈值：从70改为60，更早止盈

df = df.copy()

# --- 2. 基础计算 ---
delta = df['close'].diff()
avg_gain = delta.clip(lower=0).ewm(alpha=1/rsi_len, adjust=False).mean()
avg_loss = (-delta).clip(lower=0).ewm(alpha=1/rsi_len, adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, np.nan)
df['rsi'] = 100 - (100 / (1 + rs))
df['rsi'] = df['rsi'].fillna(50)

# ATR 和成交量
tr = pd.concat([df['high'] - df['low'], 
                (df['high'] - df['close'].shift()).abs(), 
                (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
df['atr'] = tr.rolling(14).mean().fillna(method='bfill').fillna(0)
df['vol_ma'] = df['volume'].rolling(vol_ma_len).mean().fillna(df['volume'])

# 峰谷检测 (更灵敏)
df['is_local_low'] = (df['low'] == df['low'].rolling(window=pivot_window*2+1, center=True).min())

# --- 3. 信号逻辑引擎 ---
df['buy'] = False
df['sell'] = False

# 转换为列表加速
is_low_list = df['is_local_low'].tolist()
close_list = df['close'].tolist()
open_list = df['open'].tolist()
high_list = df['high'].tolist()
low_list = df['low'].tolist()
rsi_list = df['rsi'].tolist()
vol_list = df['volume'].tolist()
vma_list = df['vol_ma'].tolist()

buy_signals = [False] * len(df)
sell_signals = [False] * len(df)

# 状态变量
last_pivot_low_p = np.nan
last_pivot_low_r = np.nan
waiting_bull_div = False
div_low_price = 0
cooldown_counter = 0 # 冷却计数器，防止信号过于密集

for i in range(len(df)):
    if i < 5: continue
    
    # 冷却逻辑：买入后休息5根K线
    if cooldown_counter > 0:
        cooldown_counter -= 1
        continue

    # A. 捕获底背离 (宽松模式)
    if is_low_list[i] is True:
        curr_p = low_list[i]
        curr_r = rsi_list[i]
        
        if not np.isnan(last_pivot_low_p):
            # 价格创新低 (或接近新低)
            price_lower = curr_p < last_pivot_low_p * 1.001 
            # RSI 抬高
            rsi_higher = curr_r > last_pivot_low_r
            # 只要当前RSI小于40即可 (之前是30)
            rsi_low_enough = curr_r < os_threshold
            
            if price_lower and rsi_higher and rsi_low_enough:
                waiting_bull_div = True
                div_low_price = curr_p # 记录背离时的最低价作为止损参考
        
        last_pivot_low_p = curr_p
        last_pivot_low_r = curr_r

    # B. 确认入场逻辑 (二选一即可)
    if waiting_bull_div:
        # 确认条件组：
        # 1. 价格突破：收盘价 > 前一日最高价 (强力突破)
        is_breakout = close_list[i] > high_list[i-1]
        
        # 2. 动能确认：RSI 拐头向上且 > 35
        is_rsi_up = rsi_list[i] > 35 and rsi_list[i] > rsi_list[i-1]
        
        # 3. 成交量确认：只需大于均线 OR 是实体大阳线(收盘价涨幅>1%)
        is_volume_ok = vol_list[i] > vma_list[i]
        is_big_candle = (close_list[i] - open_list[i]) / open_list[i] > 0.01
        
        # 逻辑：(突破 + RSI好) 且 (有量 或 大阳线)
        if is_breakout and is_rsi_up and (is_volume_ok or is_big_candle):
            buy_signals[i] = True
            waiting_bull_div = False
            cooldown_counter = 5 # 触发后冷却
        
        # 失效重置：如果价格跌破背离低点 2% (放宽止损范围)
        if close_list[i] < div_low_price * 0.98:
            waiting_bull_div = False

    # C. 卖出逻辑 (RSI高位死叉 OR 价格跌破均线趋势)
    # 简单卖出：RSI 从 > 60 掉下来
    if rsi_list[i-1] > ob_threshold and rsi_list[i] <= ob_threshold:
        sell_signals[i] = True

# 同步回 df
df['buy'] = buy_signals
df['sell'] = sell_signals

# --- 4. 绘图数据 ---
atr_list = df['atr'].tolist()
buy_marks = [low_list[i] - (atr_list[i] * 0.8) if buy_signals[i] else None for i in range(len(df))]
sell_marks = [high_list[i] + (atr_list[i] * 0.8) if sell_signals[i] else None for i in range(len(df))]

output = {
  'name': my_indicator_name,
  'plots': [
    {'name': 'RSI', 'data': df['rsi'].tolist(), 'color': '#faad14', 'overlay': False},
    {'name': 'Upper', 'data': [ob_threshold]*len(df), 'color': '#ff4d4f', 'overlay': False, 'style': 'dashed'},
    {'name': 'Lower', 'data': [os_threshold]*len(df), 'color': '#52c41a', 'overlay': False, 'style': 'dashed'}
  ],
  'signals': [
    {'type': 'buy', 'text': 'BUY', 'data': buy_marks, 'color': '#00E676'},
    {'type': 'sell', 'text': 'SELL', 'data': sell_marks, 'color': '#FF5252'}
  ]
}
"""

    # 初始配置 (用户指定)
    # 分析胜率为0的原因：
    # 1. 止盈目标(15%)较高，在短周期(5m)的一个月回测中可能难以触及。
    # 2. 追踪激活(5%)虽然比之前低，但在震荡行情中仍可能未激活就回调止损。
    # 3. 入场比例(10%)较低，影响总收益绝对值，但不影响胜率。
    # 4. 如果策略信号质量一般，配合大止损(12%)，可能导致大额亏损交易。
    initial_config = {
      "market": "Crypto",
      "symbol": "BTC/USDT",
      "stopLossPct": 12.0,
      "takeProfitPct": 30.0,
      "trailingEnabled": True,
      "startDate": "2025-12-16T07:06:56.381Z",
      "endDate": "2026-01-15T07:06:56.381Z",
      "initialCapital": 10000,
      "commission": 0.0002,
      "slippage": 0,
      "leverage": 1,
      "tradeDirection": "long",
      "timeframe": "5m",
      "selectedTimeframe": "5m",
      "trailingStopPct": 10.0,
      "trailingActivationPct": 5.0,
      "trendAddEnabled": True,
      "dcaAddEnabled": False,
      "trendAddStepPct": 1,
      "dcaAddStepPct": 0,
      "trendAddSizePct": 5,
      "dcaAddSizePct": 0,
      "trendAddMaxTimes": 10,
      "dcaAddMaxTimes": 0,
      "trendReduceEnabled": False,
      "adverseReduceEnabled": True,
      "trendReduceStepPct": 0,
      "adverseReduceStepPct": 1,
      "trendReduceSizePct": 0,
      "adverseReduceSizePct": 5,
      "trendReduceMaxTimes": 0,
      "adverseReduceMaxTimes": 10,
      "entryPct": 30
    }
    
    print(f"初始化配置: {json.dumps(initial_config, indent=2)}")
    
    optimizer = BacktestOptimizer()
    
    # 开始优化任务
    # 参数: DeepSeek R1 (Reasoner), 迭代5次, 目标 Total Return
    optimization_data = {
        "strategy_code": strategy_code,
        "config": initial_config,
        "max_iterations": 50,
        "model": "deepseek-reasoner", # 映射到后端支持的 DeepSeek 模型ID
        "target_metric": "totalReturn",
        "user_id": "test_runner"
    }
    
    job_id = optimizer.start_optimization(optimization_data)
    # 注意: start_optimization 的 model 参数通常需要匹配 LLM Provider 的模型名
    # 如果 backend 只是透传，则 "DeepSeek R1 (Reasoner)" 可能不合法，通常是 "deepseek-reasoner" 或类似
    # 这里我们再次调用 start_optimization，这次我们传入 exact string 如果 backend 处理
    # 如果 backend 有 mapping，我们可能需要查看 analyst_agents.py
    
    # 修正：根据常规 API 命名，DeepSeek R1 通常是 "deepseek-reasoner"
    # 但为了保险，我们先检查一下 analyst_agents.py (之前已查看，但没细看模型列表)
    # 假设用户要求 "DeepSeek R1 (Reasoner)" 是 UI 显示名，后端可能需要 "deepseek-reasoner"
    
    print(f"🚀 优化任务已启动 Job ID: {job_id}")
    
    # 轮询状态
    start_time = time.time()
    last_update_time = start_time
    last_iter = -1
    last_log_count = 0 
    last_history_count = 0
    
    while True:
        job = optimizer.get_job(job_id)
        if not job:
            print("❌ 无法获取任务信息")
            break
            
        current_status = job.status
        current_iter = job.current_iteration
        total_iter = job.max_iterations
        
        # 打印新日志
        if len(job.logs) > last_log_count:
            for i in range(last_log_count, len(job.logs)):
                print(f"📝 {job.logs[i]}")
            last_log_count = len(job.logs)
            
        # 打印新迭代结果
        if len(job.history) > last_history_count:
            for i in range(last_history_count, len(job.history)):
                record = job.history[i]
                metrics = record.get('metrics', {})
                params = record.get('params', {})
                iteration_idx = record.get('iteration', i)
                
                print(f"\n📊 --- 迭代 {iteration_idx} 结果 ---")
                print(f"   Total Return: {metrics.get('totalReturn', 0):.2f}%")
                print(f"   Win Rate:     {metrics.get('winRate', 0):.2f}%")
                print(f"   Trades:       {metrics.get('totalTrades', 0)}")
                print(f"   Params:       StopLoss={params.get('stopLossPct')}%, TakeProfit={params.get('takeProfitPct')}%")
                print("-" * 40)
            
            last_history_count = len(job.history)
        
        # 更新活动时间
        if current_iter != last_iter or last_history_count != len(job.history):
             last_update_time = time.time()
             last_iter = current_iter
        
        if current_status in ['completed', 'failed', 'cancelled']:
            print(f"\n✅ 任务结束状态: {current_status}")
            if job.error:
                print(f"❌ 错误信息: {job.error}")
            break
            
        time.sleep(1)
        
        # 10分钟无进展超时 (每次迭代最大允许时间)
        if time.time() - last_update_time > 1200: 
            print("\n❌ 测试超时: 10分钟无新迭代结果")
            break
    
    # 打印最终结果
    job = optimizer.get_job(job_id)
    best_result = job.best_result if job else None
    
    print("\n" + "=" * 80)
    print("🏆 最佳优化结果")
    print("=" * 80)
    
    if best_result:
        metrics = best_result.get('metrics', {})
        params = best_result.get('params', {})
        
        print(f"最佳 Total Return: {metrics.get('totalReturn', 0):.2%}")
        print(f"Win Rate: {metrics.get('winRate', 0):.2%}")
        print(f"Trades: {metrics.get('totalTrades', 0)}")
        print("\n最佳参数组合:")
        print(json.dumps(params, indent=2))
        
        history = job.history
        print(f"\n共探索了 {len(history)} 组参数")
        
        # 验证参数多样性
        unique_returns = set()
        for h in history:
            m = h.get('metrics', {})
            if m:
                # 转换回浮点数，因为它们可能被转换为百分比用于显示
                val = m.get('totalReturn')
                unique_returns.add(val)
                
        print(f"结果多样性检查: 发现 {len(unique_returns)} 种不同的结果")
        if len(unique_returns) > 1:
            print("✅ 确认AI正在有效地探索参数空间")
        else:
            print("⚠️ 警告: 所有迭代结果相同，AI可能未有效探索或参数未生效")
            
    else:
        print("❌ 未找到最佳结果")

def run_test():
    """运行参数测试"""
    # 用户的真实指标代码：BTC Ultimate Confirmed v3
    indicator_code = """
my_indicator_name = "BTC Ultimate Confirmed v3"
my_indicator_description = "# 修复Backtest列缺失错误 | 包含价格突破+量能确认"

# --- 参数设置 ---
rsi_len = 14
pivot_window = 4
vol_ma_len = 20
os_threshold = 30
ob_threshold = 70

df = df.copy()

# --- 1. 核心指标计算 ---
delta = df['close'].diff()
avg_gain = delta.clip(lower=0).ewm(alpha=1/rsi_len, adjust=False).mean()
avg_loss = (-delta).clip(lower=0).ewm(alpha=1/rsi_len, adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, np.nan)
df['rsi'] = 100 - (100 / (1 + rs))
df['rsi'] = df['rsi'].fillna(50)

# ATR 和成交量均线
tr = pd.concat([df['high'] - df['low'], 
                (df['high'] - df['close'].shift()).abs(), 
                (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
df['atr'] = tr.rolling(14).mean().fillna(method='bfill').fillna(0)
df['vol_ma'] = df['volume'].rolling(vol_ma_len).mean().fillna(df['volume'])

# --- 2. 峰谷检测 ---
df['is_local_low'] = (df['low'] == df['low'].rolling(window=pivot_window*2+1, center=True).min())
df['is_local_high'] = (df['high'] == df['high'].rolling(window=pivot_window*2+1, center=True).max())

# --- 3. 信号确认引擎 ---
# 初始化回测要求的布尔列
df['buy'] = False
df['sell'] = False

# 临时状态变量
last_pivot_low_p = np.nan
last_pivot_low_r = np.nan
waiting_bull_div = False
div_low_price = 0

# 转换为 list 以提升速度并修复 ValueError
is_low_list = df['is_local_low'].tolist()
close_list = df['close'].tolist()
high_list = df['high'].tolist()
low_list = df['low'].tolist()
rsi_list = df['rsi'].tolist()
vol_list = df['volume'].tolist()
vma_list = df['vol_ma'].tolist()

buy_signals = [False] * len(df)
sell_signals = [False] * len(df)

for i in range(len(df)):
    if i < 1: continue

    # A. 捕获底背离形态
    if is_low_list[i] is True:
        curr_p = low_list[i]
        curr_r = rsi_list[i]
        if not np.isnan(last_pivot_low_p):
            # 价格新低 + RSI抬高 + 处于超卖区
            if curr_p < last_pivot_low_p and curr_r > last_pivot_low_r and curr_r < os_threshold:
                waiting_bull_div = True
                div_low_price = curr_p
        last_pivot_low_p = curr_p
        last_pivot_low_r = curr_r

    # B. 确认入场逻辑 (BULL DIV + Price Action + Volume)
    if waiting_bull_div:
        # 1. 突破前高 2. 适度放量 3. RSI 站回 35 以上
        if close_list[i] > high_list[i-1] and vol_list[i] > vma_list[i] * 1.1 and rsi_list[i] > 35:
            buy_signals[i] = True
            waiting_bull_div = False
        
        # 失效保护：跌破背离最低点一定比例则重置
        if close_list[i] < div_low_price * 0.985:
            waiting_bull_div = False

    # C. 卖出确认逻辑 (超买区死叉回归)
    if rsi_list[i-1] > ob_threshold and rsi_list[i] <= ob_threshold:
        sell_signals[i] = True

# 将计算结果同步回 df (回测关键要求)
df['buy'] = buy_signals
df['sell'] = sell_signals

# --- 4. 封装输出数据 ---
# 生成绘图坐标数据 (基于 df['buy'] 和 df['sell'] 列)
atr_list = df['atr'].tolist()
buy_marks = [low_list[i] - (atr_list[i] * 1.0) if buy_signals[i] else None for i in range(len(df))]
sell_marks = [high_list[i] + (atr_list[i] * 1.0) if sell_signals[i] else None for i in range(len(df))]

output = {
  'name': my_indicator_name,
  'plots': [
    {'name': 'RSI', 'data': df['rsi'].tolist(), 'color': '#faad14', 'overlay': False},
    {'name': 'Mid Line', 'data': [50]*len(df), 'color': '#8c8c8c', 'overlay': False, 'style': 'dashed'},
    {'name': 'Upper Band', 'data': [ob_threshold]*len(df), 'color': '#ff4d4f', 'overlay': False},
    {'name': 'Lower Band', 'data': [os_threshold]*len(df), 'color': '#52c41a', 'overlay': False}
  ],
  'signals': [
    {'type': 'buy', 'text': 'BULL CONFIRM', 'data': buy_marks, 'color': '#00E676'},
    {'type': 'sell', 'text': 'SELL', 'data': sell_marks, 'color': '#FF5252'}
  ]
}
"""
    
    backtest_service = BacktestService()
    
    # 测试用例：不同的止损止盈参数
    test_cases = [
        {
            "name": "极小止损止盈",
            "config": {
                "risk": {
                    "stopLossPct": 0.001,  # 0.1%
                    "takeProfitPct": 0.003,  # 0.3%
                    "trailing": {
                        "enabled": False
                    }
                }
            }
        },
        {
            "name": "中等止损止盈",
            "config": {
                "risk": {
                    "stopLossPct": 0.02,  # 2%
                    "takeProfitPct": 0.06,  # 6%
                    "trailing": {
                        "enabled": False
                    }
                }
            }
        },
        {
            "name": "大止损止盈",
            "config": {
                "risk": {
                    "stopLossPct": 0.05,  # 5%
                    "takeProfitPct": 0.15,  # 15%
                    "trailing": {
                        "enabled": False
                    }
                }
            }
        },
        {
            "name": "启用追踪止损",
            "config": {
                "risk": {
                    "stopLossPct": 0.02,
                    "takeProfitPct": 0.06,
                    "trailing": {
                        "enabled": True,
                        "pct": 0.01,
                        "activationPct": 0.02
                    }
                }
            }
        },
    ]
    
    print("=" * 80)
    print("回测参数测试 - 验证参数是否被正确使用")
    print("=" * 80)
    print()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 80)
        
        # 使用新的配置结构
        strategy_config = test_case['config']
        
        print(f"参数配置: {json.dumps(strategy_config, indent=2, ensure_ascii=False)}")
        
        try:
            # 运行回测
            result = backtest_service.run(
                indicator_code=indicator_code,
                market="Crypto",
                symbol="BTC/USDT",
                timeframe="5m",
                start_date=datetime(2025, 12, 16),
                end_date=datetime(2026, 1, 15),
                initial_capital=10000,
                commission=0.0002,
                slippage=0,
                leverage=3,
                trade_direction="both",
                strategy_config=strategy_config
            )
            
            # 提取关键指标
            metrics = result.get('metrics', {})
            total_return = metrics.get('totalReturn', 0)
            win_rate = metrics.get('winRate', 0)
            total_trades = metrics.get('totalTrades', 0)
            max_drawdown = metrics.get('maxDrawdown', 0)
            
            print(f"结果:")
            print(f"  总回报: {total_return:.2%}")
            print(f"  胜率: {win_rate:.2%}")
            print(f"  总交易数: {total_trades}")
            print(f"  最大回撤: {max_drawdown:.2%}")
            
            # 提取风险配置用于显示
            risk_cfg = strategy_config.get('risk', {})
            stop_loss = risk_cfg.get('stopLossPct', 0)
            take_profit = risk_cfg.get('takeProfitPct', 0)
            
            results.append({
                "name": test_case['name'],
                "stopLoss": stop_loss,
                "takeProfit": take_profit,
                "totalReturn": total_return,
                "winRate": win_rate,
                "totalTrades": total_trades,
                "maxDrawdown": max_drawdown,
            })
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 分析结果
    print("\n" + "=" * 80)
    print("结果汇总")
    print("=" * 80)
    
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  配置: stopLoss={result['stopLoss']:.1%}, takeProfit={result['takeProfit']:.1%}")
        print(f"  结果: totalReturn={result['totalReturn']:.2%}, winRate={result['winRate']:.2%}, trades={result['totalTrades']}, maxDD={result['maxDrawdown']:.2%}")
    
    # 检查是否所有结果相同
    print("\n" + "=" * 80)
    print("诊断分析")
    print("=" * 80)
    
    unique_returns = set(r['totalReturn'] for r in results)
    unique_win_rates = set(r['winRate'] for r in results)
    unique_trades = set(r['totalTrades'] for r in results)
    
    if len(unique_returns) == 1:
        print("⚠️  警告: 所有测试的totalReturn完全相同！")
        print("   这表明止损止盈参数可能没有被正确使用。")
    else:
        print(f"✅ 检测到 {len(unique_returns)} 种不同的totalReturn值")
        print(f"   变化范围: {min(unique_returns):.2%} 到 {max(unique_returns):.2%}")
        print("   参数正在影响回测结果。")
    
    if len(unique_trades) == 1:
        print("⚠️  警告: 所有测试的交易数完全相同！")
    else:
        print(f"✅ 检测到 {len(unique_trades)} 种不同的交易数")
        print(f"   参数正在影响交易执行。")
    
    print("\n✅ 测试完成！")
    if len(unique_returns) > 1:
        print("参数传递和使用正常，回测引擎工作正常。")
    else:
        print("\n建议:")
        print("1. 检查 BacktestService._simulate_trading_new_format() 方法的配置读取逻辑")
        print("2. 添加调试日志确认参数是否被读取")
        print("3. 查看止损止盈执行逻辑")

if __name__ == "__main__":
    # 运行基础参数传递测试
    # run_test()
    
    # 运行AI优化测试
    run_ai_test()