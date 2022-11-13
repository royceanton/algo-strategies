@parameter(name="aroon", type="int", default=11, min=2, max=20, enabled=True)
@parameter(name="sma", type="int", default=5, min=5, max=20, enabled=True)
@parameter(name="rsi", type="int", default=9, min=5, max=20, enabled=True)

def initialize(state, params):
    state.number_offset_trades = 0;

def align(*args):
    ''' make multiple lists the same length '''
    N = min([len(x) for x in args])
    return [x[-N:] for x in args]

@schedule(interval="15m", symbol="BTCUSDT")
def handler(state, data, params):

    aroon= data.aroon(params.aroon) # Aggregate data container for all indicator outputs
    sma = data.sma(params.sma)
    rsi_ind = data.rsi(params.rsi)

    # on erroneous data return early (indicators are of NoneType)
    if rsi_ind is None or sma is None or aroon is None:
        return

    sma = sma.last
    aroon_down = aroon["aroon_down"].last
    aroon_up = aroon["aroon_up"].last
    rsi = rsi_ind.last

    current_price = data.close_last

    portfolio = query_portfolio()
    balance_quoted = portfolio.excess_liquidity_quoted
    # we invest only 80% of available liquidity
    buy_value = float(balance_quoted) * 0.80


    position = query_open_position_by_symbol(data.symbol,include_dust=False)
    has_position = position is not None

    # compute crossover
    crossover = 0
    if aroon["aroon_up"][-1] > aroon["aroon_down"][-1] and aroon["aroon_up"][-2] < aroon["aroon_down"][-2]:
        crossover = +1
    elif aroon["aroon_up"][-1] < aroon["aroon_down"][-1] and aroon["aroon_up"][-2] > aroon["aroon_down"][-2]:
        crossover = -1


    if rsi > 50:
        if current_price > sma:
            if crossover == 1 and not has_position:
                        
                print("-------")
                print("Buy Signal: creating market order for {}".format(data.symbol))
                print("Buy value: ", buy_value, " at current market price: ", data.close_last)

                order_market_value(symbol=data.symbol, value=buy_value)  # creating market order

    elif current_price < data.low[-2] and has_position:
        print("-------")
        logmsg = "Sell Signal: closing {} position with exposure {} at current market price {}"
        print(logmsg.format(data.symbol,float(position.exposure),data.close_last))

        close_position(data.symbol)  # closing position

    '''
    5) Check strategy profitability
        > print information profitability on every offsetting trade
    '''

    if state.number_offset_trades < portfolio.number_of_offsetting_trades:

        pnl = query_portfolio_pnl()
        print("-------")
        print("Accumulated Pnl of Strategy: {}".format(pnl))

        offset_trades = portfolio.number_of_offsetting_trades
        number_winners = portfolio.number_of_winning_trades
        print("Number of winning trades {}/{}.".format(number_winners,offset_trades))
        print("Best trade Return : {:.2%}".format(portfolio.best_trade_return))
        print("Worst trade Return : {:.2%}".format(portfolio.worst_trade_return))
        print("Average Profit per Winning Trade : {:.2f}".format(portfolio.average_profit_per_winning_trade))
        print("Average Loss per Losing Trade : {:.2f}".format(portfolio.average_loss_per_losing_trade))
        # reset number offset trades
        state.number_offset_trades = portfolio.number_of_offsetting_trades
