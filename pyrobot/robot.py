import pandas as pd
import pprint
import sys

from datetime import datetime
from datetime import time
from datetime import timezone
from datetime import timedelta
import time

from typing import List
from typing import Dict
from typing import Union
from typing import Optional

from pyrobot.portfolio import Portfolio
from pyrobot.stock_frame import StockFrame
from pyrobot.trades import Trade

from tools.bitstamp_command import bitstamp_requests, string_to_float

class PyRobot():

    def __init__(self, account_number: str = None, client_id: str = None,
                 api_key: str = None, api_secret: str = None, nonce: str = None,
                 paper_trading: bool = False) -> None:

        self.account_number: str =      account_number
        self.client_id: str =           client_id
        self.api_key: str =             api_key
        self.api_secret: str =          api_secret
        self.nonce: str =               nonce
        self.trades: dict =             {}
        self.historical_prices: dict =  {}
        self.stock_frame =              None
        self.paper_trading =            paper_trading

    def get_client_id(self) -> str:
        return (self.client_id)

    def get_api_key(self) -> str:
        return (self.api_key)

    def get_api_secret(self) -> str:
        return (self.api_secret)

    def get_nonce(self) -> str:
        return (self.nonce)

    @property
    def pre_market_open(self) -> bool:
        pre_market_start_time = datetime.utcnow().replace(hour=7, minute=30, second=00).timestamp()
        market_start_time = datetime.utcnow().replace(hour=8, minute=00, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_start_time >= right_now >= pre_market_start_time:
            return True
        else:
            return False

    @property
    def post_market_open(self) -> bool:
        post_market_end_time = datetime.utcnow().replace(hour=17, minute=00, second=00).timestamp()
        market_end_time = datetime.utcnow().replace(hour=16, minute=30, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if post_market_end_time >= right_now >= market_end_time:
            return True
        else:
            return False

    @property
    def regular_maket_open(self) -> bool:
        market_start_time = datetime.utcnow().replace(hour=8, minute=00, second=00).timestamp()
        market_end_time = datetime.utcnow().replace(hour=16, minute=30, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False

    def create_portfolio(self):
        # init new portfolio object
        self.portfolio = Portfolio(account_number = self.account_number)
        return self.portfolio

    def create_trade(self, trade_id: str, enter_or_exit: str,
                     long_or_short: str, order_type: str = 'mkt',
                     price: float = 0.0,
                     stop_limit_price: float = 0.0) -> Trade:
        trade = Trade()
        trade.new_trade(
            trade_id = trade_id,
            order_type = order_type,
            enter_or_exit = enter_or_exit,
            side = long_or_short,
            price = price,
            stop_limit_price = stop_limit_price
        )
        self.trades[trade_id] = trade
        return trade

    def create_stock_frame(self, data: List[dict]) -> StockFrame:
        self.stock_frame = StockFrame(data = data)
        return self.stock_frame

    def grab_current_quotes(self) -> dict:
        quotes = self.portfolio.positions.keys()
        quotes_content = {}
        for quote in quotes:
            quotes_content[quote] = bitstamp_requests(
                request_parameter = 'ticker',
                currency_pair = quote
            )
        return quotes_content

    def grab_single_current_quote(self, symbol: str = 'ethusd') -> dict:
        quotes_content = {}
        quotes_content[symbol] = bitstamp_requests(
            request_parameter = 'ticker',
            currency_pair = symbol
        )
        return quotes_content

    # 4h bar by default with 1 week of data
    def grab_historical_prices(self, symbols: List[str] = None, step: str = '3600', limit: str ='500'):
        self._step = step
        self._limit = limit
        data = {'step' : step, 'limit' : limit}

        new_prices = []

        if not symbols:
            symbols = self.portfolio.positions

        for symbol in symbols:

            historical_prices_response = bitstamp_requests(
                request_parameter = 'ohlc',
                currency_pair = symbol,
                data = data
            )

            self.historical_prices[symbol] = {}
            self.historical_prices[symbol]['candles'] = historical_prices_response['data']['ohlc']

            for candle in historical_prices_response['data']['ohlc']:

                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = symbol
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['timestamp']
                new_prices.append(new_price_mini_dict)

            self.historical_prices['aggregated'] = new_prices

        return self.historical_prices

    def get_latest_quote(self) -> List[dict]:
        data = {'step' : self._step, 'limit' : 1}

        for symbol in self.portfolio.positions:

            last_bar_response = bitstamp_requests(
                request_parameter = 'ohlc',
                currency_pair = symbol,
                data = data
            )

            if 'error' in last_bar_response:
                time.sleep(2)
                last_bar_response = bitstamp_requests(
                request_parameter = 'ohlc',
                currency_pair = symbol,
                data = data
                )
            last_bar_response = string_to_float(last_bar_response['data']['ohlc'][0])

            latest_prices = {}
            latest_prices['symbol'] = symbol
            latest_prices['open'] = last_bar_response['open']
            latest_prices['close'] = last_bar_response['close']
            latest_prices['high'] = last_bar_response['high']
            latest_prices['low'] = last_bar_response['low']
            latest_prices['volume'] = last_bar_response['volume']
            latest_prices['datetime'] = last_bar_response['timestamp']

        return latest_prices

    def wait_until_next_bar(self, latest_bar_timestamp: pd.DatetimeIndex) -> None:

        last_bar_time = latest_bar_timestamp.to_pydatetime()[0].replace(tzinfo=timezone.utc)
        next_bar_time = last_bar_time + timedelta(seconds=(int(self._step)))
        curr_bar_time = datetime.now(tz=timezone.utc)

        last_bar_timestamp = int(last_bar_time.timestamp())
        next_bar_timestamp = int(next_bar_time.timestamp())
        curr_bar_timestamp = int(curr_bar_time.timestamp())

        _time_to_wait_bar = next_bar_timestamp - last_bar_timestamp
        time_to_wait_now = next_bar_timestamp - curr_bar_timestamp

        if time_to_wait_now < 0:
            time_to_wait_now = 0

        print("="*80)
        print("Pausing for the next bar")
        print("-"*80)
        print("Curr Time: {time_curr}".format(
            time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        )
        print("Next Time: {time_next}".format(
            time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        )

        print("Sleep until next bar: {seconds} seconds".format(seconds=time_to_wait_now))
        time.sleep(time_to_wait_now)

    def execute_signals(self, signals: List[pd.Series], trades_to_execute: dict) -> List[dict]:
        pass
