# %% Preamble.

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# %% Import Packages.

import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns

# %% Long Position Class.

class Long():
    
    def __init__(self, id, size, sl=0):
        
        self.id = id
        self.status = 0
        self.size = size
        self.value = 0.0
        self.sl = sl
        
        return None
    
    def check(self, timestamp, open, high, low, close):
        
        # Entry. #
        
        # Market buy.
        
        if (self.status == 0):
            
            self.status = 1
            self.entry_price = open
            self.entry_time = timestamp
            self.orig_value = self.size * open
            self.value = self.orig_value
            
            # Return cost of purchase, at bar open.
            
            print("{} #{} Long Open: {} market buy at {} for {}." \
                  "".format(timestamp,
                            self.id,
                            self.size,
                            open,
                            self.orig_value)
                  )
            
            return -self.orig_value
        
        # Position open. #
        
        elif (self.status == 1):
            
            # Update price-to-market position value.
            
            self.value = self.size*close
            
            # Stop loss.
            
            if (low <= self.sl):
                
                # Convert stop loss to market sell at next bar open.
                
                print("{} # {} Long SL Hit: converting to market sell." \
                      "".format(timestamp,
                                self.id)
                      )
                
                self.status = 2
                
                return 0.0
            
            else:
                
                return 0.0
            
            return 0.0
        
        # Market sell.
        
        elif (self.status == 2):
            
            self.status = 3
            self.exit_price = open
            self.exit_time = timestamp
            self.final_value = self.size * open
            self.value = 0.0
            
            # Return proceeds of sale, at bar open.
            
            print("{} #{} Long Close: {} market sell at {} for {}." \
                  "".format(timestamp,
                            self.id,
                            self.size, 
                            open, 
                            self.final_value)
                  )
            
            return self.final_value
        
        else:
            
            return 0.0
        
    # Market sell order.
    
    def sell(self):
        
        self.status = 2
        
        return None
            
        
                
 
# %% Test Dataset.

#  Import Historical Data from FXCM HDD Basic.

csv1 = pd.read_csv(r'E:\Google Drive\Python\Quantitative Finance\ADX Flash BB Analysis FXCM\EURUSD_m1_Y1_BidAndAsk.csv')
                   
# %% Transform FXCM HDD Basic Price Series to Bid OHLCV.

def fxcm_bid(df):
    '''
    Transforms raw FXCM HDD Basic Historical price series to a simple six 
    column bid price series. Columns: timestamp, open, high, low, close, vol.
    
    Dependencies: datetime, pandas.

    Parameters
    ----------
    df : pandas DataFrame
        Raw FXCM HDD Basic .csv read into a pandas DataFrame. Any timeframe.

    Returns
    -------
    df : pandas DataFrame
        Six column bid price series, see function description. 'timestamp' is
        a datetime54[ns] object.

    '''
    
    df = df.copy()
    
    # Combine Date and Time into datetime 'timestamp'.
    
    df['timestamp'] = None
    
    for row in tqdm(df.itertuples()):

        df.at[row.Index, 'timestamp'] = datetime(int(row.Date[6:10]),
                                                 int(row.Date[0:2]),
                                                 int(row.Date[3:5]),
                                                 int(row.Time[0:2]),
                                                 int(row.Time[3:5]),
                                                 int(row.Time[6:8])
                                                 )
        
    df['timestamp'] = pd.to_datetime(df['timestamp'], 
                                     format='%Y-%m-%d %H:%M:%S')
        
    
    
    # Rename Bid OHLC to 'OHLC'.
    
    df['open'] = df['OpenBid']
    df['high'] = df['HighBid']
    df['low'] = df['LowBid']
    df['close'] = df['CloseBid']
    
    # Rename Total Ticks to 'vol' and move to end.
    
    df['vol'] = df['Total Ticks']
    
    # Drop Bid OHLC, Ask OHLC, Date, Time and Total Ticks.
    
    df = df.drop(columns = ['OpenBid', 
                            'HighBid', 
                            'LowBid', 
                            'CloseBid',
                            'OpenAsk', 
                            'HighAsk', 
                            'LowAsk', 
                            'CloseAsk',
                            'Total Ticks',
                            'Date',
                            'Time'
                            ])
    
    return df            
 
# %% Independent strategy functions.

# Fast/Slow Moving Averages Technical Indicator.

def ta_ma(df, fast, slow):
    
    df = df.copy()
    
    df['fast_ma'] = df.close.rolling(window=fast).mean()
    df['slow_ma'] = df.close.rolling(window=slow).mean()
    
    df['ma_temp'] = np.where(df.fast_ma > df.slow_ma, 1, 0)
    df['ma_signal'] = df.ma_temp.diff()
    df['ma_long'] = np.where(df.ma_signal == 1, True, False)
    df['ma_short'] = np.where(df.ma_signal == -1, True, False)
    
    df = df.drop(columns=['ma_temp', 'ma_signal'])
    
    return df

# Moving Averages Strategy Logic.

def ma_strategy_long_entry(row):
    
    if (row.ma_long == True):
        
        sl = row.close - 0.001
        
        return True
    
    else:
        
        return False
    
def ma_strategy_long_exit(row):
    
    if (row.ma_short == True):
        
        return True
    
    else:
        
        return False
    


# %% Plot Price Series and Equity Curve.

def ma_plot(df):
    
    # Price series.
    
    #fig, ax1, ax2 = plt.subplots(figsize=(15,5))
    
    fig = plt.figure(figsize=(15,15))
    
    #ax = fig.add_subplot(111)
   # ax1.set_xlabel('Timestamp', fontsize=10)

    

    
    # Bid close and on-chart studies.
    
    ax1 = fig.add_subplot(311)
    
    ax1.plot(df.timestamp, df.close, 'b')
    ax1.plot(df.timestamp, df.fast_ma, 'r')
    ax1.plot(df.timestamp, df.slow_ma, 'g')

    #ax1.ylabel('Bid Close', fontsize=10)
    
    # Strategy. #
    
    # Position tracker.
    
    ax2 = fig.add_subplot(312)
    
    ax2.plot(df.timestamp, df.open_longs, 'b')
    ax2.plot(df.timestamp, df.closed_longs, 'r')
    
    #ax2.ylabel('Positions', fontsize=10)
    
    # Cash and Account Value.
    
    ax3 = fig.add_subplot(313)
    
    ax3.plot(df.timestamp, df.cash, 'b')
    ax3.plot(df.timestamp, df.positions_value, 'r')
    ax3.plot(df.timestamp, df.account, 'g')
    

    plt.tight_layout()
    plt.show()
    
    return None

# %% Basic Backtest Engine.

def backtest(df):
    
    df = df.copy()
    
    position_no = 1
    fee = 0.001
    cash = 1000000.00
    margin = 30
    margin_debt = 0.0
    restricted_cash = 0.0

    
    df['cash'] = cash
    df['restricted_cash'] = restricted_cash
    df['margin_debt'] = margin_debt
    df['open_longs'] = 0
    df['closed_longs'] = 0
    
    
    open_longs = []
    closed_longs = []
    
    for row in tqdm(df.itertuples()):
        
        # Iterate through open positions. #
        
        for long in reversed(open_longs):
            
            transfer = long.check(row.timestamp, 
                                  row.open,
                                  row.high,
                                  row.low,
                                  row.close
                                  )
            
            margin_debt += transfer - fee * abs(transfer)
            

            
            if (long.status == 3):
                
                closed_longs.append(open_longs.pop(open_longs.index(long)))
                
            else:
                
                None
                
        # Open position. #
        
        # Open long position.
        
        if (ma_strategy_long_entry(row) == True):
            
            size = (row.cash / row.close)*0.95
            new_long = Long(position_no, size)
            position_no += 1
            
            open_longs.append(new_long)
            
        # Close position. #
            
        # Close long position.
        
        if (len(open_longs) != 0):
            
            if (ma_strategy_long_exit(row) == True):
            
                for long in open_longs:
                    
                    long.sell()
                    
        # Update strategy analytics.
        
        df.at[row.Index, 'cash'] = cash
        df.at[row.Index, 'open_longs'] = len(open_longs)
        df.at[row.Index, 'closed_longs'] = len(closed_longs)
        
    return df, open_longs, closed_longs
            
             
        






