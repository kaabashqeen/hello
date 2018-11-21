import tradersbot as tt
import time
import mibian
import scipy.stats as ss
import math
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
#import py_vollib.black_scholes.implied_volatility as iv

import sys

down_volSpread_trade_flag = False
up_volSpread_trade_flag = False

tracker_spot = 0
import sys

t = tt.TradersBot('52.90.204.149', 'UTexas2', '45396823')

cancelcount = 0
canceltickers = []
cancelids = []

# Keeps track of prices
SECURITIES = {}
UNDERLYINGS = {}
MARKET_STATES = {}
TRADER_STATE = {}

end_time = None

count = 0

SPREAD = 0.05
spot = 100
puts = {}
calls = {}
puts_ivs = {}
calls_ivs = {}
put_greeks = {}
call_greeks = {}
start = time.time()

threshold = 0

order_id = []
info = []

history = {} # ticker : [isBuy, quantity, price]


spots = []
vols = []
# class VolCurve():
#
#     def __init__(self, sec_state):
#         self.name = sec_state['ticker']
#         self.bids = sec_state['bids']
#         self.asks = sec_state['asks']
#         self.price = sec_state['price']
#         self.time = sec_state['time']
#         self.volcurve = None
#
#
#     def calc_volcurve(self):
#         volcurve = None
#
#         self.volcurve = volcurve
#

volchangedownincoming = False
volchangeupincoming = False
def vol_change(order):
    if len(integralskews)>2 and down_volSpread_trade_flag is False and up_volSpread_trade_flag is False:
        # if integralskews[0]>integralskews[1]<integralskews[2]:
        #     pass
        # elif integralskews[0]<integralskews[1]>integralskews[2]:
        #     pass
        if integralskews[-1]<.4:
            st = 'T'+str(int(spot))+'P'
            order.addBuy(st, quantity=500)
            pass
        elif integralskews[-1]>1.5:
            st = 'T' + str(int(spot)) + 'C'
            order.addBuy(st, quantity=500)
        else:
            if integralskews[-1]>integralskews[-2]:
                volchangeupincoming = True
                marketMake('TMXFUT', '', 'C', spot, order)
            elif integralskews[-1]<integralskews[-2]:
                volchangedownincoming = True
                marketMake('TMXFUT', '', 'P', spot, order)




def ack_register(msg, order):
    global SECURITIES
    security_dict = msg['case_meta']['securities']
    underlying_dict = msg['case_meta']['underlyings']
    market_states = msg['market_states']
    trader_state = msg['trader_state']

    for security in security_dict.keys():
        if not(security_dict[security]['tradeable']):
            continue
        SECURITIES[security] = security_dict[security]['starting_price']

    for underlying in underlying_dict.keys():
        UNDERLYINGS[underlying] = underlying_dict[underlying]

    for mkt_state in market_states.keys():
        MARKET_STATES[mkt_state] = market_states[mkt_state]
    TRADER_STATE = trader_state

#     print(SECURITIES)
#     print(UNDERLYINGS)
#     print(MARKET_STATES)
#     print(TRADER_STATE)
#     print()


def market_update(msg, order):

    global count
    global spot
    global puts
    global calls
    global cancelcount
    global puts_ivs
    global calls_ivs
    global up_volSpread_trade_flag
    global down_volSpread_trade_flag

    global cancelids, canceltickers
    option_state = msg['market_state']
    option_ticker = option_state['ticker']
    option_bids = option_state['bids']
    option_asks = option_state['asks']
    option_price = (option_state['last_price'])
    option_time = option_state['time']

    option_type = option_ticker[-1]
    option_strike = option_ticker[1:-1]
    #print(option_ticker, option_time)

    time_left = 7.5 * 60 - (time.time() - start)
    if option_type == 'P':
        put = option_strike
        puts[option_strike] = option_price
        bs = mibian.BS([spot, int(put), 0, time_left / 15.0], putPrice=puts[put])
        # iv_put = iv.implied_volatility(puts[put], spot, float(put), days_left/365, 0, 'p')
        # print(val.impliedVolatility)
        iv_put = bs.impliedVolatility
        puts_ivs[put] = round(iv_put, 5)
        d1 = (math.log(spot/int(put),2) + iv_put/2*time_left/15)/((iv_put**1/2)*(time_left**(1/2)))-1
        delta = ss.norm.cdf(d1)
        vega = ss.norm.pdf(d1)/(spot*(iv_put**(1/2))*(time_left**(1/2)))
        put_greeks[put] = [delta, vega]
    elif option_type == 'C':
        call = option_strike
        calls[option_strike] = option_price
        bs = mibian.BS([spot, int(call), 0, time_left / 15.0], callPrice=calls[call])
        # iv_call = iv.implied_volatility(calls[call], spot, float(call), days_left/365, 0, 'c')
        # print(val.impliedVolatility)
        iv_call = bs.impliedVolatility
        d1 = (math.log(spot/int(call),2) + iv_call/2*time_left/15)/((iv_call**1/2)*(time_left**(1/2)))
        delta = ss.norm.cdf(d1)
        vega = ss.norm.pdf(d1)/(spot*(iv_call**(1/2))*(time_left**(1/2)))
        call_greeks[call] = (delta, vega)
        calls_ivs[call] = round(iv_call, 5)
        call_greeks[call] = [delta, vega]
    elif option_ticker == 'TMXFUT':
        count +=1
        cancelcount+=1
        spot = option_price
    else:
        print('unexpected security state')

    price = option_price
    asks = option_asks.keys()
    # if option_ticker!= 'TMXFUT':
    #     if abs(price - float(min((asks))))/ price >= SPREAD:
    #        marketMake(option_ticker, option_strike, option_type, price, order)
    if cancelcount==2:
        for id in range(len(cancelids)):
            order.addCancel(canceltickers[id],cancelids[id])
        cancelids, canceltickers =[], []
        cancelcount=0
    if len(calls)+len(puts)==82 and count==1:
        count = 0
        checkup = up_integralSkew(spot, calls_ivs, puts_ivs)
        checkdown = down_integralSkew(spot, calls_ivs, puts_ivs)
        if up_volSpread_trade_flag is False and checkup == "up":
            up_volSpreadTrade(order)
        if up_volSpread_trade_flag is True and checkup == "close":
            close_up_volSpreadTrade(order)
        if down_volSpread_trade_flag is False and checkdown == "down":
            down_volSpreadTrade(order)
        if down_volSpread_trade_flag is True and checkdown == "close":
            close_down_volSpreadTrade(order)

        vol_change(order)

    # do we still want to keep all the old puts/calls?
    #smileTrade(order)

    #cancelOrders(order)



def vol_smile(calls_calc, puts_calc):
    global puts_ivs
    global calls_ivs
    global spot
    callstrikes = []
    callstrikes_ivs = []
    # print('call')
    for i in range(80,121):
        callstrikes.append(i)
        callstrikes_ivs.append(calls_ivs[str(i)])
    # plt.plot(callstrikes, callstrikes_ivs)
    # plt.show()
    #plt.show()
    #3print(callstrikes_ivs, spot)
    # print('put')
    putstrikes = []
    putstrikes_ivs = []
    for i in range(80,121):
        putstrikes.append(i)
        putstrikes_ivs.append(puts_ivs[str(i)])
    # plt.plot(putstrikes, putstrikes_ivs)
    # plt.show()


def marketMake(ticker, val, direction, mid, order):
    if ticker=='TMXFUT':
        if direction=="C":
            order.addSell(ticker=ticker, quantity=15, price=mid*1.02)
            order.addSell(ticker=ticker, quantity=25, price=mid*1.01)
            # makeTrade(ticker, False, 5, None, order)
            time.sleep(.25)
            order.addBuy(ticker=ticker, quantity=15,price=mid*.98)
            order.addBuy(ticker=ticker, quantity=25, price=mid*.99)
            # makeTrade(ticker, True, 5, None, order)
        elif direction =="P":
            order.addBuy(ticker=ticker, quantity=15, price=mid*.98)
            order.addBuy(ticker=ticker, quantity=25, price=mid*.99)
            # if ((spot-mid*.99)/mid*.99)
            # makeTrade(ticker, True, 5, None, order)
            time.sleep(.25)
            order.addSell(ticker=ticker, quantity=15, price=mid*1.02)
            order.addSell(ticker=ticker, quantity=25, price=mid*1.01)
            # makeTrade(ticker, False, 5, None, order)
        return
    if direction == 'P':
        delta = put_greeks[val][0]
    else:
        delta = call_greeks[val][0]
    if delta > 0:
        # make a put offer if delta favors calls
        makeTrade(ticker[:-1] + 'P', True, 5, int(mid * 0.95), order)
    else:
        makeTrade(ticker[:-1] + 'C', True, 5, int(mid * 1.05), order)

def calcNetDeltaVega(positions):
    net_delta = 0
    net_vega = 0
    print(positions)
    print(put_greeks)
    print(call_greeks)
    for ticker in positions:
        if ticker[-1] == 'P' and ticker[1:-1] in put_greeks and put_greeks[ticker[1:-1]][1] != None:
            net_delta += put_greeks[ticker[1:-1]][1]
            net_vega += put_greeks[ticker[1:-1]][2]
        elif ticker[-1] == 'C' and ticker[1:-1] in call_greeks and call_greeks[ticker[1:-1]][1] != None:
            print(call_greeks[ticker[1:-1]])
            net_delta += call_greeks[ticker[1:-1]][1]
            net_vega += call_greeks[ticker[1:-1]][2]
    return net_delta, net_vega

def smileTrade(order):
    index = 80
    difference = 1000
    call_ll = sorted(list(call_greeks))
    put_ll = sorted(list(put_greeks))
    for i in range(len(call_ll)):
        diff = abs(spot - call_greeks[call_ll[i]][0])
        if diff < difference:
                index = i
                difference = diff

    print(call_greeks)

    for i in range(index, len(call_ll) - 1):
        print(i)
        #if the volatility
        print(call_greeks[call_ll[i]][0])
        if ( call_greeks[call_ll[i+1]][0] < call_greeks[call_ll[i]][0]):
            ticker = "T"+str(call_ll[i+1])+"C"

            print(ticker)
            print (calls[call_ll[i+1]]*1.05)
            makeTrade(ticker, True, 1, calls[call_ll[i+1]]*1.05, order)

    index = 80
    difference = 1000
    print(put_ll)
    for i in range(len(put_ll)):
        print(put_greeks[put_ll[i]])
        diff = abs(spot - put_greeks[put_ll[i]][0])
        if diff < difference:
                index = i
                difference = diff
    for i in range(min(len(put_ll) - 1, index), 1, -1):
        print(i)
        #if the volatility
        print(put_greeks[put_ll[i]][0])
        if (put_greeks[put_ll[i-1]][0] > put_greeks[put_ll[i]][0]):
            ticker = "T"+str(put_ll[i-1])+"P"
            print(ticker)
            print (puts[put_ll[i-1]]*0.95)
            makeTrade(ticker, True, 1, puts[put_ll[i-1]]*0.95, order)

integralskews = []
def up_integralSkew(spot, calls_ivs, puts_ivs):
    iv_call_sum = 0
    iv_put_sum = 0
    for i in range(int(spot),121):
        iv_c = calls_ivs[str(i)]
        iv_call_sum += iv_c

    for i in range(80, int(spot) + 1):
        iv_p = puts_ivs[str(i)]
        iv_put_sum += iv_p

    integral_factor = iv_call_sum / iv_put_sum
    spots.append(spot)
    vols.append(integral_factor)
    print(integral_factor, spot)
    integralskews.append(integral_factor)
    if integral_factor > 1.25:
        return "up"
    elif integral_factor <= 1.15:
        return "close"
    else:
        return "neither"


def down_integralSkew(spot, calls_ivs, puts_ivs):
    iv_call_sum = 0
    iv_put_sum = 0
    for i in range(int(spot),121):
        iv_c = calls_ivs[str(i)]
        iv_call_sum += iv_c

    for i in range(80, int(spot) + 1):
        iv_p = puts_ivs[str(i)]
        iv_put_sum += iv_p

    integral_factor = iv_call_sum / iv_put_sum

    if integral_factor < .50:
        return "down"
    elif integral_factor >= 0.55:
        return "close"
    else:
        return "neither"


def up_volSpreadTrade(order):
    print('uptrade')
    global spot
    global up_volSpread_trade_flag
    global tracker_spot
    long_call_strike = int(spot)
    tracker_spot = long_call_strike
    # print(spot)
    ticker = "T" + str(long_call_strike) + "C"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    short_call_strike = 120
    ticker = "T" + str(short_call_strike) + "C"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)

    short_put_strike = int(spot)
    ticker = "T" + str(short_put_strike) +"P"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)

    long_put_strike = 80
    ticker = "T" + str(long_put_strike) + "P"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)
    # print(call_greeks[str(short_call_strike)])
    # print(put_greeks[str(long_put_strike)])

    #makeTrade("TMXFUT", False, delta quantity, None, order)

    up_volSpread_trade_flag = True


def close_up_volSpreadTrade(order):
    print("CLOSEUP")
    global spot
    global tracker_spot
    global up_volSpread_trade_flag
    short_call_strike = tracker_spot
    ticker = "T" + str(short_call_strike) + "C"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)

    long_call_strike = 121
    ticker = "T" + str(long_call_strike) + "C"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    long_put_strike = tracker_spot
    ticker = "T" + str(long_put_strike) +"P"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    short_put_strike = 80
    ticker = "T" + str(short_put_strike) + "P"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)
    # makeTrade("TMXFUT", True, delta quantity, None, order)

    up_volSpread_trade_flag = False


def down_volSpreadTrade(order):
    print("down trade")
    global spot
    global down_volSpread_trade_flag
    global tracker_spot
    short_call_strike = int(spot)
    tracker_spot = short_call_strike
    # print(spot)
    ticker = "T" + str(short_call_strike) + "C"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)

    long_call_strike = 120
    ticker = "T" + str(long_call_strike) + "C"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    long_put_strike = int(spot)
    ticker = "T" + str(long_put_strike) +"P"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    short_put_strike = 80
    ticker = "T" + str(short_put_strike) + "P"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)
    # print(call_greeks[str(short_call_strike)])
    # print(put_greeks[str(long_put_strike)])

    #makeTrade("TMXFUT", False, delta quantity, None, order)

    down_volSpread_trade_flag = True


def close_down_volSpreadTrade(order):
    print("CLOSEDOWN")
    global spot
    global down_volSpread_trade_flag
    global tracker_spot
    long_call_strike = tracker_spot
    ticker = "T" + str(long_call_strike) + "C"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    short_call_strike = 120
    ticker = "T" + str(short_call_strike) + "C"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)

    short_put_strike = tracker_spot
    ticker = "T" + str(short_put_strike) +"P"
    order.addSell(ticker, 20)
    # makeTrade(ticker, False, 20, None, order)

    long_put_strike = 80
    ticker = "T" + str(long_put_strike) + "P"
    order.addBuy(ticker, 20)
    # makeTrade(ticker, True, 20, None, order)

    # makeTrade("TMXFUT", True, delta quantity, None, order)

    down_volSpread_trade_flag = False


def makeTrade(ticker, isBuy, quantity, price, order):
    global threshold
    if threshold < 10:
        if ticker not in history:
                history[ticker] = []
        history[ticker].append([isBuy, quantity, price])
        order.addTrade(ticker, isBuy, quantity, None, None)
        threshold += 1


def ack_modify_order(msg, order):
    global cancelids, canceltickers
    orders = msg['orders']
    for order in orders:
        cancelids.append(order['order_id'])
        canceltickers.append(order['ticker'])
    print('msg', msg)

def trade(msg, order):
    print('msg', msg)

def news(msg, order):
    print('msg', msg)



t.onMarketUpdate = market_update
t.onTrade = trade
t.onAckModifyOrders = ack_modify_order
# t.onTraderUpdate = trader_update
t.onAckRegister = ack_register
t.onNews = news
t.run()
