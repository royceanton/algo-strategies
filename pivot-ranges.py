import pandas
import numpy as np
import datetime
import math
import operator

from functools import reduce

pandas.set_option('display.max_columns', None)
pandas.set_option('display.width', None)


def make_double_barrier(symbol,amount,take_profit,stop_loss,state):

    with OrderScope.one_cancels_others():
        order_upper = order_take_profit(symbol,amount,take_profit,subtract_fees=True)
        order_lower = order_stop_loss(symbol,amount,stop_loss,subtract_fees=True)

    if order_upper.status != OrderStatus.Pending:
        errmsg = "make_double barrier failed with: {}"
        raise ValueError(errmsg.format(order_upper.error))

    # saving orders
    state["order_upper"] = order_upper
    state["order_lower"] = order_lower
    state["created_time"] = order_upper.created_time

    return order_upper, order_lower

def compute_percentage(x1,y1):
    val = abs((x1-y1)/x1)
    return val

def initialize(state):
    state.trend = None
    state.number_offset_trades = 0
    state.first_daily_trade = None
    state.first_daily_trade_ids = []



@schedule(interval= "1d", symbol="BTCUSDT",window_size=5)
def handler_1d(state, data):

    df = data.to_pandas()
    df['date'] = df.index

    df['pivot'] = (df['high'][-1]+ df['low'][-1] + df['close'][-1])/3
    df['bc'] = (df['high'][-1] + df['low'][-1]) /2
    df['tc'] = (df['pivot'] - df['bc']) + df['pivot']

    df['pdh'] = df['high'].iloc[-1]
    df['pdl'] = df['low'].iloc[-1]

    df['r1'] = 2*df['pivot'][-1] - df['low'][-1]
    df['s1'] = 2*df['pivot'][-1] - df['high'][-1]

    df['r2'] = df['pivot'][-1] + (df['r1'][-1] - df['s1'][-1])
    df['s2'] = df['pivot'][-1] - (df['r1'][-1] - df['s1'][-1])
    
    state.pp =  df['pivot'][-1]
    state.bc = df['bc'][-1]
    state.tc = df['tc'][-1]

    state.pr1 = df['r1'][-1]
    state.ps1 = df['s1'][-1]

    state.pr2 = df['r2'][-1]
    state.ps2 = df['s2'][-1]

    state.pdh = df['pdh'][-1]
    state.pdl = df['pdl'][-1]

    state.daily_open = df['open'][-1]
    state.one_day_timestamp = df['date'][-1].date()



@schedule(interval= "15m", symbol="BTCUSDT",window_size=4)
def handler_15m(state, data):

    df = data.to_pandas()
    df['date'] = df.index
    state.fifteen_min_timestamp = df['date'][-1]


@schedule(interval= "5m", symbol="BTCUSDT",window_size=100)
def handler_5m(state, data):

    current_price = data.close[-1]

    df = data.to_pandas()
    df['date'] = df.index

    low_list = list(data.low)
    last10_low = min(low_list[-10:])

   
    portfolio = query_portfolio()
    has_position = has_open_position(data.symbol, include_dust=False)
    balance_quoted = float(query_balance_free(data.quoted))
    balance_base = float(query_balance_free(data.base))
    buy_amount = (balance_quoted / data.close_last)*0.8

    def make_order_map():

        order = query_open_orders()
        return {x: x for x in order}

    def compute_percentage(x1,y1):
        val = round(abs((x1-y1)/x1),4)
        return val
    
    if some_condition that sets a limit order:

        state.first_limit_order = order_limit_amount(symbol=data.symbol, amount=buy_amount, limit_price= *some price it triggers*)
        state.first_limit_order_id.append(state.first_limit_order) #gets the id like you mentioned before

    #how can I trigger a SL and TP for that specific order once it triggers?

        with OrderScope.sequential(fail_on_error=True, wait_for_entire_fill=False):
            if some condition to check if order id's match:
                #set SL & TP for that exact first limit order 





    if df['date'][-1].hour == 00 and df['date'][-1].minute == 15:
        if data.close[-1] > state.pp and data.close[-2] > state.pp and data.close[-3] > state.pp:
            if data.close[-1] > state.bc and data.close[-2] > state.bc and data.close[-3] > state.bc:
                if data.close[-1] > state.tc and data.close[-2] > state.tc and data.close[-3] > state.tc:
                    if data.close[-1] < state.pdh and data.close[-2] < state.pdh and data.close[-3]< state.pdh:
                        if data.close[-1] < state.pr1 and data.close[-2] < state.pr1 and data.close[-3]< state.pr1 and not has_position:

                            tp = float(compute_percentage(state.pdh-20, data.close[-1]))
                            sl = float(compute_percentage(state.pr1-20, data.close[-1]))
                            
                            buy_order = order_market_amount(data.symbol, buy_amount*0.5)
                            order_upper, order_lower = make_double_barrier(buy_order.symbol,
                                                                float(buy_order.quantity),
                                                                tp,sl,state)

                            state.first_daily_trade = order_limit_amount(symbol=data.symbol, amount=buy_amount*0.5, limit_price= state.bc+10)
                            state.first_daily_trade_ids.append(state.first_daily_trade)


    if state.current_position != []:
        print(state.current_position)
        for position in state.current_position:
            state.current_position_ids= position.id

        if state.trigger_status is None and state.current_position_ids is not None:
            print('A limit order is now an active position, placing a TP & SL order')
            with OrderScope.one_cancels_others():
                state.limit_sl = order_limit_amount(symbol=data.symbol, amount= -buy_amount*0.5, limit_price= state.bc-10)
                state.limit_tp = order_limit_amount(symbol=data.symbol, amount= -buy_amount*0.5, limit_price= state.pdh-10)
                state.limit_sl_ids.append(state.limit_sl)
                state.limit_tp_ids.append(state.limit_tp)



            
            state.trigger_status = 'Order placed'
            print(state.trigger_status)
            print(f'There is a sequential tp and sl placed at: TP:{state.pr1} and SL:{state.tc-10}')

        if df['date'][-1].hour==23 and df['date'][-1].minute== 55:
            if state.trigger_status is not None:
                    

                print('Resetting trigger status to none')
                print(f'Based on condition at: {df.date[0].hour==23}')
                state.trigger_status = None
                state.current_position_ids = None
                print(f'This is the recent order status {state.current_position_ids}')


    if data.high[-1] >= state.pdh or data.high[-1] >= state.pr1 or df['date'][-1].hour == 23 and not has_position:

        if state.first_daily_trade_id != []:
            for order in state.first_daily_trade_ids:
                cancel_order(order.id)

                                tp = float(compute_percentage(state.pdh-20, data.close[-1]))
                            sl = float(compute_percentage(data.close[-1],state.tc-50)) #adding reduces distance
                            print(f'Executing buy order at {data.close[-1]} , tp at {tp}, sl at {sl} percentage')
                            print(f'tc is at {state.tc}, adding 50 gives {state.tc+50}, sub 50 gives {state.tc-50}')
                            buy_order = order_market_amount(data.symbol, buy_amount*0.5)
                            order_upper, order_lower = make_double_barrier(buy_order.symbol,
                                                                float(buy_order.quantity),
                                                                tp,sl,state)

    if state.first_daily_trade_ids != []:
            for order in state.first_daily_trade_ids:
                print(order)
                #cancel_order(order.id)

    if last10_low <= state.ps1 and data.open[-1] > state.ps1 and not has_position:

        tp = float(compute_percentage(state.pp-30, data.close[-1]))
        sl = float(compute_percentage(last10_low-30, data.close[-1]))
        buy_order = order_market_amount(data.symbol, buy_amount)
        order_upper, order_lower = make_double_barrier(buy_order.symbol,
                                                float(buy_order.quantity),
                                                tp,sl,state)



    if data.high[-1] >= state.pdh or data.high[-1] >= state.pr1 or df['date'][-1].hour == 23 and not has_position:

        if state.first_daily_trade_id != []:
            for order in state.first_daily_trade_ids:
                cancel_order(order.id)
    
    if data.open[-2] < state.pp and data.high[-1] >= state.bc 

    to do: create a function to dynalically compute distance in percentage

    if data.high.last >= state.pdh or data.high.last >= state.pr1 and has_position:

        close_position(data.symbol)


    if df['date'][-1].hour == 23 and df['date'][-1].minute == 55 and has_position:

        close_position(data.symbol)
           




    if data.high[-1] >= state.pdh or data.high[-1] >= state.pr1 or df['date'][-1].hour == 23 and not has_position:

        if state.first_daily_trade_id != []:
            for order in state.first_daily_trade_ids:
                cancel_order(order.id)

    
    if last10_low <= state.ps1 and data.open[-1] > state.ps1 and not has_position:

        tp = float(compute_percentage(state.pp-30, data.close[-1]))
        sl = float(compute_percentage(state.pr1-30, data.close[-1]))

        buy_order = order_market_amount(data.symbol, buy_amount)
        order_upper, order_lower = make_double_barrier(buy_order.symbol,
                                              float(buy_order.quantity),
                                              tp,sl,state)
    #to do: create a function to dynalically compute distance in percentage

    if data.high.last >= state.pdh or data.high.last >= state.pr1 and has_position:

        close_position(data.symbol)


    # if df['date'][-1].hour == 23 and df['date'][-1].minute == 55 and has_position:

    #     close_position(data.symbol)
           


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


