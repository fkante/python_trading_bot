import time as true_time
import pprint
import pathlib
import operator
import os
import pandas as pd

from datetime import datetime
from datetime import timedelta
from configparser import ConfigParser

from pyrobot.robot import PyRobot
from pyrobot.indicators import Indicators
from pyrobot.stock_frame import StockFrame

# Grab the config file values
os.system("python3 configs/config.py")
config = ConfigParser()
config.read('configs/config.ini')

CLIENT_ID = config.get('main', 'CLIENT_ID')
API_KEY = config.get('main', 'API_KEY')
API_SECRET = config.get('main', 'API_SECRET').encode('UTF-8')
NONCE = config.get('main', 'NONCE')

# init the robot
trading_robot = PyRobot(
    account_number = '1',
    client_id = CLIENT_ID,
    api_key = API_KEY,
    api_secret = API_SECRET,
    nonce = NONCE,
    paper_trading = True
)

# Create a new portfolio
trading_robot_portfolio = trading_robot.create_portfolio()

# add multi positions to portfolio
'''
multi_position = [
    {
        'asset_type': 'bitcoin',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'btcusd',
        'purchase_date': '2020-09-09'
    },
    {
        'asset_type': 'altcoin',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'ethusd',
        'purchase_date': '2020-09-09'
    }
]

new_positions = trading_robot.portfolio.add_multiple_positions(positions=multi_position)
'''
#pprint.pprint(new_positions)

# add single position
trading_robot.portfolio.add_position(
    symbol='ethusd',
    quantity=10,
    purchase_price=0.70,
    purchase_date='2020-09-08',
    asset_type='altcoin'
)
#pprint.pprint(trading_robot.portfolio.positions)

# Check if market open for regular assets
'''
if trading_robot.regular_maket_open:
    print('Regular CAC market open')
else:
    print('Regular CAC market closed')

if trading_robot.pre_market_open:
    print('pre CAC market open')
else:
    print('pre CAC market closed')
'''

# Grab all current quotes in portfolio
# pprint.pprint(trading_robot.grab_current_quotes())
# pprint.pprint(trading_robot.grab_single_current_quote())
# Grab historical prices of all symbols in portfolio
historical_prices = trading_robot.grab_historical_prices()

# Convert data into a StockFrame
stock_frame = trading_robot.create_stock_frame(data=historical_prices['aggregated'])

# Print the head of the StockFrame
# pprint.pprint(stock_frame.frame)

# create a trade
new_trade = trading_robot.create_trade(
    trade_id = 'long_ethusd',
    enter_or_exit = 'enter',
    long_or_short= 'long',
    order_type= 'mkt',
    price = 4.0
)

new_trade.good_till_cancel(datetime.now() + timedelta(minutes = 10))

new_trade.instrument(
    symbol = 'ethusd',
    quantity = 2,
    asset_type = 'altcoin'
)

new_trade.add_stop_loss(
    stop_size = 0.10,
    percentage = False
)

#pprint.pprint(new_trade.order)

indicator_client = Indicators(price_data_frame = stock_frame)

# RSI
indicator_client.rsi(period = 14)

# 200-day sma
indicator_client.sma(period = 200)

# 50-day ema
indicator_client.ema(period = 50)

# add a signal to check for
indicator_client.set_indicator_signals(
    indicator = 'rsi',
    buy = 40.0,
    sell = 20.0,
    condition_buy = operator.ge,
    condition_sell = operator.le
)

# define the trade dict
trades_dict = {
    'ethusd': {
        'trade_func': trading_robot.trades['long_ethusd'],
        'trade_id': trading_robot.trades['long_ethusd'].trade_id
    }
}


while True:

    latest_bar = trading_robot.get_latest_quote()
    stock_frame.add_rows(quote = latest_bar)
    indicator_client.refresh()

    # pprint.pprint(stock_frame.frame, width = 200)

    print('='*80)
    print('current StockFrame')
    print('-'*80)
    print(stock_frame.symbol_groups.tail())
    print('-'*80)

    signals = indicator_client.check_signals()

#    trading_robot.execute_signals(signals = signals, trades_to_execute = trades)

    latest_bar_timestamp = trading_robot.stock_frame.frame.tail(1).index.get_level_values(1)
    trading_robot.wait_until_next_bar(latest_bar_timestamp = latest_bar_timestamp)
