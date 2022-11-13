import numpy as np
from trality.indicator import vwma

@parameter(name='rsi_period', type='categorical', default= 14, categories=[8,14,21,34,55])
@parameter(name='vwma_period', type='categorical', default = 21, categories=[8,14,21,34,55])

def initialize(state, params):
    state.number_offset_trades = 0;
    pass

def align(*args):
    ''' make multiple lists the same length '''
    N = min([len(x) for x in args])
    return [x[-N:] for x in args]

@schedule(interval="5m", symbol="BTCUSDT", window_size=200)

def handler(state, data, params):
    
    rsi = data.rsi(int(params.rsi_period)).to_numpy()[0]
    vols = data.volume.to_numpy()[0]
    rsi, vols = align(rsi, vols)
    
    stacked = np.vstack((rsi,vols))
    rsi_vwma = vwma(stacked, int(params.vwma_period))[0]
    sma_200_ind = data.sma(200)
    sma_12_ind = data.sma(12)
 
    # compute crossover
    crossover = 0
    if rsi[-1] > rsi_vwma[-1] and rsi[-2] < rsi_vwma[-2]:
        crossover = +1
    elif rsi[-1] < rsi_vwma[-1] and rsi[-2] > rsi_vwma[-2]:
        crossover = -1

    if rsi is None or sma_200_ind is None or sma_12_ind is None or rsi_vwma is None:
            return

    current_price = data.close_last
    rsi = rsi[-1]
    rsi_vwma = rsi_vwma[-1]
    sma_200 = sma_200_ind.last
    sma_12 = sma_12_ind.last

    portfolio = query_portfolio()
    balance_quoted = portfolio.excess_liquidity_quoted

    buy_value = float(balance_quoted) * 0.80
    position = query_open_position_by_symbol(data.symbol,include_dust=False)
    has_position = position is not None

    if crossover == 1 and data.close_last > sma_200 and data.close_last > sma_12 and rsi < 50 and not has_position:
        print('crossover found-buy')
        order_market_value(symbol=data.symbol, value=buy_value)

    elif rsi > 80 and has_position:
        print('crossover found-sell')
        close_position(data.symbol)

    if state.number_offset_trades < portfolio.number_of_offsetting_trades:
        pnl = query_portfolio_pnl()
        state.number_offset_trades = portfolio.number_of_offsetting_trades
