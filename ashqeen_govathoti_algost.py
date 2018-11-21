import tradersbot as tt
import time, threading

# news trading
t = tt.TradersBot('52.90.204.149', 'UTexas2', '45396823')

prices = {}

history = {}  # ticker : [isBuy, quantity, price]

order_id = []
info = []
last_trade = 0.0
last = time.time()

# Initialize variables: positions, expectations, future customer orders, etc
position_limit = 5000
case_length = 450
cash = 0
position_lit = 0
position_dark = 0
topBid = 0
topAsk = 0

# Keeps track of prices
SECURITIES = {}
UNDERLYINGS = {}
MARKET_STATES = {}
TRADER_STATE = {}

end_time = None

count = 0

SPREAD = 0.05
spot = 0
lit = []
dark = []

threshold = 0
spot_lit = 0
spot_dark = 0


def ack_register(msg, order):
    global SECURITIES
    security_dict = msg['case_meta']['securities']
    underlying_dict = msg['case_meta']['underlyings']
    market_states = msg['market_states']
    trader_state = msg['trader_state']

    for security in security_dict.keys():
        if not (security_dict[security]['tradeable']):
            continue
        SECURITIES[security] = security_dict[security]['starting_price']

    for underlying in underlying_dict.keys():
        UNDERLYINGS[underlying] = underlying_dict[underlying]

    for mkt_state in market_states.keys():
        MARKET_STATES[mkt_state] = market_states[mkt_state]
    TRADER_STATE = trader_state


def market_update(msg, order):
    global last_trade
    global last

    security_state = msg['market_state']
    security = security_state['ticker']
    security_bids = security_state['bids']
    security_asks = security_state['asks']
    security_price = security_state['last_price']
    security_time = security_state['time']
    security_type = security[-1]  # T = TRDRS.LIT and K = TRDRS.DARK

    if security_type == 'K':
        spot_dark = security_price
        prices[security_type] = security_price
        dark.append(security_price)
    elif security_type == 'T':
        spot_lit = security_price
        prices[security_type] = security_price
        lit.append(security_price)

    # elapsed = time.time() - last
    # if time.time() - last_trade > 1:# and elapsed < 10:
    #         print('trade')
    #         last_trade = time.time()
    #         for d in dark:
    #                 price = prices[d[0:3]][d[3:6]]
    #                 if price > 0.01:
    #                         print('buyz' ,d, price * .995)
    #                         print('sellz',d, price * 1.005)
    #                         #makeTrade(d, True, 10, price * .999 - .01 + 199, order)
    #                         makeTrade(d, True, 1000, price * .92 - .01, order)
    #                         makeTrade(d, False, 1000, price * 1.08 + .01, order)


#     if elapsed > 10:
#         print("LIQUIDATING")
#         #liquidateToUsd(order)
#         print("post liquidation")
# #            last = time.time()
#
#     cancelOrders(order)

#
# def printVals():
#         print('---------')
#         for v in vals:
#                 for vv in vals:
#                         print(v, vv, prices[v][vv])


def makeTrade(ticker, isBuy, quantity, price, order):
    if ticker not in history:
        history[ticker] = []
    history[ticker].append([isBuy, quantity, price])
    order.addTrade(ticker, isBuy, quantity, None, None)


def trader_update(msg, order):
    pass


buyticker = ''
newsbuys = {}


def news_buy(ticker, quantity, order):
    global newsbuys, buyticker
    time.sleep(.2)
    makeTrade(ticker, False, 200, None, order)
    newsbuys[ticker] = int(int(quantity) * .05)
    buyticker = ticker
    historical = 'buy'


sellticker = ''
newssells = {}


def news_sell(ticker, quantity, order):
    global newssells, sellticker
    time.sleep(.2)
    makeTrade(ticker, True, 200, None, order)
    newssells[ticker] = int(int(quantity) * .05)
    historical = 'sell'
    sellticker = ticker


historical = ''
historicals = {}


def news(msg, order):
    print(msg['news']['headline'])
    global historical, historicals
    global buyticker, newsbuys
    global newssells, sellticker
    check = msg['news']['headline']

    if historical == 'buy':
        news_sell(buyticker, newsbuys[buyticker], order)
        historical = ''
        buyticker = ''
    elif historical == 'sell':
        news_buy(sellticker, newsbuys[sellticker], order)
        historical = ''
        sellticker = ''
    else:
        pass

    if 'buy' in check:
        ticker = ''
        quantity = ''
        beg = check.rfind('of') + 3
        end = check.rfind('!')
        ticker = check[beg:end]

        beg = check.rfind('ing') + 4
        end = check.rfind('shares') - 1
        quantity = check[beg:end]
        historicals[ticker] = spot
        print(ticker, quantity)
        news_buy(ticker + '.LIT', quantity,
                 order)  # if customer is buying in dark, then competitors will buy from LIT to sell in DARK

    elif 'sell' in check:
        ticker = ''
        quantity = ''
        beg = check.rfind('of') + 3
        end = check.rfind('!')
        ticker = check[beg:end]

        beg = check.rfind('ing') + 4
        end = check.rfind('shares') - 1
        quantity = check[beg:end]
        historicals[ticker] = spot
        print(ticker, quantity)
        news_sell(ticker + '.LIT', quantity, order)

    print(msg['news'])


def trade(msg, order):
    print(msg)


def ack_modify_order(msg, order):
    print(msg)


t.onMarketUpdate = market_update
t.onTrade = trade
t.onAckModifyOrders = ack_modify_order
t.onTraderUpdate = trader_update
t.onAckRegister = ack_register
t.onNews = news
t.run()
