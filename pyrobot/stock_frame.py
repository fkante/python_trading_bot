import numpy as np
import pandas as pd

from datetime import datetime
from datetime import time
from datetime import timezone

from typing import List
from typing import Dict
from typing import Union

from pandas.core.groupby import DataFrameGroupBy
import pandas.core.window.rolling
import pprint

class StockFrame():

    def __init__(self, data: List[dict]) -> None:

        self._data = data
        self._frame = self.create_frame()
        self._symbol_groups = None
        self._symbol_rolling_groups = None

    @property
    def frame(self) -> pd.DataFrame:
        return self._frame

    @property
    def symbol_groups(self) -> DataFrameGroupBy:

        self._symbol_groups = self._frame.groupby(
            by = "symbol",
            as_index = False,
            sort = True
        )
        return self._symbol_groups

    def create_frame(self) -> pd.DataFrame:

        price_df = pd.DataFrame(data = self._data)
        price_df = self._parse_datetime_column(price_df = price_df)
        price_df = self._set_multi_index(price_df = price_df)
        price_df[['open', 'close', 'high', 'low', 'volume']] = \
            price_df[['open', 'close', 'high', 'low', 'volume']].apply(pd.to_numeric)
        return price_df


    def symbol_rolling_groups(self, size: int):

        if not self._symbol_groups:
            self.symbol_groups

        self._symbol_rolling_groups = self._symbol_groups.rolling(size)

        return self._symbol_rolling_groups

    def _parse_datetime_column(self, price_df: pd.DataFrame) -> pd.DataFrame:

        price_df['datetime'] = pd.to_datetime(price_df['datetime'], unit='s', origin='unix')

        return price_df

    def _set_multi_index(self, price_df: pd.DataFrame) -> pd.DataFrame:

        price_df = price_df.set_index(['symbol', 'datetime'])

        return price_df

    def add_rows(self, quote: dict) -> None:

        column_names = ['open', 'close',  'high', 'low', 'volume']


        time_stamp = pd.to_datetime(
            quote['datetime'],
            unit = 's',
            origin = 'unix'
        )
        row_id = (quote['symbol'], time_stamp)
        row_values = [
            quote['open'],
            quote['close'],
            quote['high'],
            quote['low'],
            quote['volume']
        ]
        new_row = pd.Series(data = row_values)
        self.frame.loc[row_id, column_names] = new_row.values
        self.frame.sort_index(inplace=True)

    def do_indicators_exist(self, column_names: List[str]) -> bool:

        if set(column_names).issubset(self._frame.columns):
            return True
        else:
            raise KeyError(
                'The following indicators are missing from the StockFrame: \
                {missing}'.format(
                    missing = set(column_names).difference(self._frame.columns)
                )
            )
    def _check_signals(self, indicators: dict) -> Union[pd.Series, None]:

        last_row = self._symbol_groups.tail(1)
        conditions = []

        if self.do_indicators_exist(column_names = indicators.keys()):

            for indicator in indicators:

                column = last_row[indicator]
                buy_condition_target = indicators[indicator]['buy']
                sell_condition_target = indicators[indicator]['sell']

                buy_condition_operator = indicators[indicator]['buy_operator']
                sell_condition_operator = indicators[indicator]['sell_operator']

                condition_1: pd.Series = buy_condition_operator(column, buy_condition_target)
                condition_2: pd.Series = sell_condition_operator(column, sell_condition_target)

                condition_1 = condition_1.where(lambda x: x == True).dropna()
                condition_2 = condition_2.where(lambda x: x == True).dropna()

                conditions.append(('buys', condition_1))
                conditions.append(('sells', condition_2))

            return conditions
