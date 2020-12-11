# 50行代码实现并发获取所有币安U本位永续合约交易对(目前78对)K线
# 并且按交易额排序，然后得到前一小半交易活跃的币对
# 再在这些活跃交易的币对里找出短线可能要突破或者跌破的币对序列
# wechat: rus-fpq

import ccxt,time
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

bn = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

symbols = [market['symbol'] for market in bn.fetchMarkets()]
all_sym_cnt = len(symbols)
print('共有交易对数量:',all_sym_cnt)
# print('交易对列表:',symbols)
pool = ThreadPoolExecutor(all_sym_cnt)
pool_res_dict = {}
kline_dict = {}
while 1:
    for sym in symbols:
        pool_res_dict[sym] = pool.submit(bn.fetch_ohlcv,sym,'15m')
    for sym in symbols:
        kline_dict[sym] = pool_res_dict[sym].result()

    quote_vols = {}
    for k,v in kline_dict.items():
        quote_vols[k] = v[-1][4]*v[-1][5]
    
    # 按交易额排序
    sorted_vols = dict(sorted(quote_vols.items(), key=lambda item: item[1], reverse=True))
    cnt = round(all_sym_cnt*(1-0.618)) #去掉黄金分割下的不活跃币种
    top_syms = list(sorted_vols.keys())[:cnt]
    print(f'交易额头{cnt}名:',top_syms)

    points = {}
    for sym in top_syms:
        klines = kline_dict[sym][-16:]
        highest = max(map(lambda x: x[2], klines))
        lowest  = min(map(lambda x: x[3], klines))
        ltp = klines[-1][4]
        points[sym] = round((ltp-lowest)/(highest-lowest),4)
    sorted_pts = OrderedDict(sorted(points.items(), key=lambda item: item[1], reverse=True))
    n = 5
    # 过去4小时上涨前n名
    tops = dict(list(sorted_pts.items())[:n])
    # 过去4小时下跌前n名
    btms = dict(list(sorted_pts.items())[-n:])
    pt_mean = round(sum(sorted_pts.values())/len(sorted_pts),4)

    print(f"短期涨幅前{n}",tops)
    print(f"短期均值: {pt_mean}")
    print(f"短期跌幅前{n}",btms)

    time.sleep(900)