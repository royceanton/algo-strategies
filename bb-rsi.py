
'''
    bbands= data.bbands(20,2) 
    rsi_ind = data.rsi(7)
    sma_ind = data.sma(200)

    Perfect for Sideways-1h-2 Markets

'''

def initialize(state):
    state.number_offset_trades = 0;

@schedule(interval="5m", symbol="BTCUSDT",window_size=200)

def handler(state, data):

#initialize indicators

    bbands= data.bbands(20,2) 
    rsi_ind = data.rsi(7)
    sma_ind = data.sma(200)

    if rsi_ind is None or bbands is None or sma_ind is None:
        return

#extract last values of each indicators

    current_price = data.close_last
    rsi = rsi_ind.last
    sma_200 = sma_ind.last
    bbands_lower=bbands["bbands_lower"].last
    bbands_middle=bbands["bbands_middle"].last
    bbands_upper=bbands["bbands_upper"].last

#create portfolio

    portfolio = query_portfolio()
    balance_quoted = portfolio.excess_liquidity_quoted
    # we invest only 80% of available liquidity
    buy_value = float(balance_quoted) * 0.80

    position = query_open_position_by_symbol(data.symbol,include_dust=False)
    has_position = position is not None

#trading algo logic for initialized indicators

    if data.close_last > sma_200 and not has_position:
        if data.close_last <= bbands_lower:
            if rsi < 30:
                order_market_value(symbol=data.symbol, value=buy_value)

    elif data.close_last >= bbands_upper and has_position:
        
        close_position(data.symbol)

# Check strategy profitability

    if state.number_offset_trades < portfolio.number_of_offsetting_trades:
        pnl = query_portfolio_pnl()
        state.number_offset_trades = portfolio.number_of_offsetting_trades
