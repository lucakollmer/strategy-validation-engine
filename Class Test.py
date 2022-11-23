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

# %% Long Position Class.

class Long():
    
    def __init__(self, size, lim_buy=0, tp=0, sl=0):
        
        self.status = 0
        self.size = size
        self.lim_buy = lim_buy
        self.tp = tp
        self.sl = sl
        
        return None
    
    def check(self, open, high, low, close, maker_fee, taker_fee):
        '''
        Every tick check longs for satisfaction of entry and exit orders,
        excluding market sell orders.

        Parameters
        ----------
        open : TYPE
            DESCRIPTION.
        high : TYPE
            DESCRIPTION.
        low : TYPE
            DESCRIPTION.
        close : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        
        # Long entry. #
        
        if (self.status == 0):
            
            # Market buy.
                
            if (self.lim_buy == 0):
                
                self.status += 1
                
                # Return cost of purchase, assuming purchase at open.
                
                return -(1 + taker_fee) * self.size * open
            
            # Limit buy.
            
            elif (self.lim_buy != 0 and low <= self.lim_buy):
                
                self.status += 1
                
                # Return cost of purchase, assuming zero slippage.
                
                return -(1 + maker_fee) * self.size * self.lim_buy
            
            # Limit fails.
            
            else:
                
                return 0
            
        # Planned long exit. #
        
        elif (self.status == 1):
            
            # Stop loss.
            
            if (self.sl != 0 and low <= self.sl):
                
                self.status += 1
                
                # Return proceeds of sale, assuming zero slippage.
                
                return (1 + taker_fee) * self.size * self.sl
            
            # Take profit.
            
            elif (self.tp != 0 and high >= self.tp):
                
                self.status += 1
                
                # Return proceeds of sale, assuming zero slipage.
                
                return (1 + maker_fee) * self.size * self.tp
            
            # Neither stop loss or take profit satisfied.
            
            else:
                
                return 0
            
        # Long closed. #
        
        else:
            
            return 0
        
    def sell(self, open, taker_fee):
        '''
        Market sell order at open of current tick. Assumes sale at open price
        with zero slippage.

        Parameters
        ----------
        open : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        
        # Long open.
        
        if (self.status == 1):
            
            self.status += 1
            
            # Return proceeds of sale, assuming sale at open.
            
            return (1 + taker_fee) * self.size * open
        
        # Long not entered or closed.
        
        else:
            
            return 0
        
    # Modify Long properties. #
            
    def mod_lim_buy(self, lim_buy):
        self.lim_buy = lim_buy
        
    def mod_tp(self, tp):
        self.tp = tp
        
    def mod_sl(self, sl):
        self.sl = sl
                
 
# %% Test Dataset.

#  Import Historical Data from FXCM HDD Basic.

csv1 = pd.read_csv(r'E:\Google Drive\Python\Quantitative Finance\ADX Flash BB Analysis FXCM\EURUSD_m1_Y1_BidAndAsk.csv')
                   
#  Transform FXCM HDD Basic Price Series to OHLC.

def transform_data(df):
    
    df = df.copy()
    
    # Combine Date and Time, then drop Date.
    df['time'] = df['Date'] + " " + df['Time']
    df = df.iloc[:,1:]
    
    # Rename Bid OHLC to OHLC
    df['open'] = df['OpenBid']
    df['high'] = df['HighBid']
    df['low'] = df['LowBid']
    df['close'] = df['CloseBid']
    
    # Drop Bid and Ask OHLC and rename Total Ticks to Volume.
    df = df.drop(columns = ['OpenBid', 
                            'HighBid', 
                            'LowBid', 
                            'CloseBid',
                            'OpenAsk', 
                            'HighAsk', 
                            'LowAsk', 
                            'CloseAsk'
                            ])
    
    df = df.rename(columns = {'Total Ticks': 'vol'})    
    
    return df            
 
# %% Mock engine for testing.

def ta_ma(df, fast, slow):
    
    df = df.copy()
    
    df['fast_ma'] = df.close.rolling(window=fast).mean()
    df['slow_ma'] = df.close.rolling(window=slow).mean()
    
    df['ma_temp'] = np.where(df.fast_ma > df.slow_ma, 1, 0)
    df['ma_signal'] = df.ma_temp.diff()
    
    df = df.drop(columns=['ma_temp'])
    
    return df



def backtest(df):
    
    df = df.copy()
    
    cash = 100000.0
    df['cash'] = 0.0
    df['longs'] = 0
    
    open_longs = []
    closed_longs = []
    
    for tick in tqdm(df.itertuples()):
        
        # Check open longs for exit satisfaction.
        
        
        for long in reversed(open_longs):
            
            pnl = Long.check(self=long,
                               open=tick.open,
                               high=tick.high,
                               low=tick.low,
                               close=tick.close,
                               maker_fee=0.0,
                               taker_fee=0.0
                               )
            
            cash += pnl
            
            # Remove closed long from 
            
            if (long.status == 2):
                
                closed_longs.append(
                    open_longs.pop(
                        open_longs.index(long)))
                
            else:
                
                None
         
        # Check long entry conditions.
        
        if (tick.ma_signal == 1):
            
            new_long_tp = tick.close * 1.005
            new_long_sl = tick.close * 0.99
            new_long_lim_buy = tick.close * 0.995
            
            new_long = Long(100, lim_buy = new_long_lim_buy,
                            tp=new_long_tp, sl=new_long_sl)
            open_longs.append(new_long)
            
        else:
            
            None
            
        # Update series analytics.
        
        df.at[tick.Index, 'cash'] = cash
        df.at[tick.Index, 'longs'] = len(open_longs)
            
    return df







