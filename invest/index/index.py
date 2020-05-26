from invest.index import *


class SMA(object):
    """
    简单移动平均线
    """

    def index(self, data, timeperiod=30):
        """
        指标计算
        """
        temp = list(data)
        temp.reverse()
        result = talib.SMA(np.asarray(temp), timeperiod=timeperiod)
        temp = list(result)
        temp.reverse()
        return temp

    def profit(self, money, data, fast_period=5, slow_period=20):
        """
        计算该指标下利润
        """
        product = data.copy()
        product['fast'] = pd.Series(SMA(product['Close'], timeperiod=fast_period))
        product['slow'] = pd.Series(SMA(product['Close'], timeperiod=slow_period))
        product = product.loc[(product['slow'].notnull()), :].reset_index(drop=True)

        signal = []
        for i in range(0, len(product) - 1):
            if (product['fast'][i] > product['slow'][i]) & (product['fast'][i + 1] <= product['slow'][i + 1]):
                signal.append('buy')
            elif (product['fast'][i] < product['slow'][i]) & (product['fast'][i + 1] >= product['slow'][i + 1]):
                signal.append('sell')
            else:
                signal.append('hold')
        product['signal'] = pd.Series(signal)

        money = money
        status = 'out'
        vol = 0
        hold_price = 0
        for i in list(reversed(range(len(product)))):
            if product['signal'][i] == 'buy':
                if status == 'out':
                    vol = money / product['Close'][i]
                    hold_price = product['Close'][i]
                    status = 'buy'
                elif status == 'buy':
                    pass
                elif status == 'sell':
                    money = money + vol * (hold_price - product['Close'][i])
                    status = 'out'
            elif product['signal'][i] == 'sell':
                if status == 'out':
                    vol = money / product['Close'][i]
                    hold_price = product['Close'][i]
                    status = 'sell'
                elif status == 'sell':
                    pass
                elif status == 'buy':
                    money = money + vol * (product['Close'][i] - hold_price)
                    status = 'out'
        return money, fast_period, slow_period

    def best_period(self, data):
        """
        计算最佳交叉周期
        """
        pair = []
        for i in range(3, 31):
            for j in range(i + 1, 71):
                pair.append([i, j])

        money = []
        period = []
        for fast_period, slow_period in pair:
            a, b, c = self.profit(10000, data, fast_period=fast_period, slow_period=slow_period)
            money.append(a)
            period.append([b, c])
        return max(money), period[money.index(max(money))]

    def signal(self, data, fast_period=5, slow_period=20):
        """
        计算该指标下利润
        """
        product = data.copy()
        product['fast'] = pd.Series(self.index(product['Close'], timeperiod=fast_period))
        product['slow'] = pd.Series(self.index(product['Close'], timeperiod=slow_period))
        product = product.loc[(product['slow'].notnull()), :].reset_index(drop=True)

        signal = []
        for i in range(0, len(product) - 1):
            if (product['fast'][i] > product['slow'][i]) & (product['fast'][i + 1] <= product['slow'][i + 1]):
                signal.append('buy')
            elif (product['fast'][i] < product['slow'][i]) & (product['fast'][i + 1] >= product['slow'][i + 1]):
                signal.append('sell')
            else:
                signal.append('hold')
        product['signal'] = pd.Series(signal)
        return product['signal'][0], product['signal'][1]


class MACD(object):
    """
    MACD
    """

    def index(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
        """
        指标计算
        """
        temp = list(data)
        temp.reverse()
        result = talib.MACD(np.asarray(temp), fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        temp = list(result)
        macd = list(temp[0])
        macd.reverse()
        macdsignal = list(temp[1])
        macdsignal.reverse()
        macdhist = list(temp[2])
        macdhist.reverse()
        return macd, macdsignal, macdhist

    def trend(self, close, timeperiod=7):
        if (timeperiod % 2) == 0:
            raise ValueError('timeperiod 必须是奇数！')
        _, _, data = self.index(close)
        p = 0  # 正斜率
        n = 0  # 负斜率
        for i in range(0, timeperiod):
            if data[i] >= data[i + 1]:
                p = p + 1
            else:
                n = n + 1
        if p >= n:
            return 'up', "{:.2f}".format(float(p / (p + n)))
        else:
            return 'down', "{:.2f}".format(float(n / (p + n)))


class RSI(object):
    """
    RSI
    """

    def index(self, data, timeperiod=14):
        """
        指标计算
        """
        temp = list(data)
        temp.reverse()
        result = talib.RSI(np.asarray(temp), timeperiod=timeperiod)
        temp = list(result)
        temp.reverse()
        return temp

    def direction(self, close):
        data = self.index(close)
        if data[0] >= 50:
            return 'up', data[0]
        else:
            return 'down', data[0]


class STOCH(object):
    """
    随机指标
    """

    def index(self, high, low, close, fastk_period=14):
        """
        指标计算
        """
        high = list(high)
        low = list(low)
        close = list(close)
        high.reverse()
        low.reverse()
        close.reverse()
        result = talib.STOCH(np.asarray(high), np.asarray(low), np.asarray(close), fastk_period=fastk_period)
        temp = list(result)
        slowk = list(temp[0])
        slowk.reverse()
        slowd = list(temp[1])
        slowd.reverse()
        return slowk, slowd

    def direction(self, high, low, close):
        slowk, slowd = self.index(high, low, close)
        if (slowk[0] >= 50) & (slowd[0] >= 50):
            return 'up', slowk[0], slowd[0]
        elif (slowk[0] < 50) & (slowd[0] < 50):
            return 'down', slowk[0], slowd[0]
        else:
            return 'no_direction', slowk[0], slowd[0]


class TripleFilterSystem(object):
    """
    三重滤网系统
    """

    def is_open_position(self, long_data, midline_data, short_data):
        """
        是否开仓,三重滤网
        """
        # 根据长线MACD判断趋势，决定多空
        trend, _ = MACD.trend(long_data, timeperiod=7)

        # 开盘价之上不空，开盘价之下不多
        if trend == 'up':
            if short_data['Open'] > short_data['Close']:
                return False
        elif trend == 'down':
            if short_data['Open'] < short_data['Close']:
                return False
        else:
            return False

        # 中线技术指标kdj，rsi判断是否开仓
        rsi_direction, _ = RSI.direction(midline_data['Close'])
        stoch_direction, _, _ = STOCH.direction(midline_data['Close'])
        if trend == 'up':
            if (rsi_direction == 'down') | (stoch_direction == 'down'):
                return False
        elif trend == 'down':
            if (rsi_direction == 'up') | (stoch_direction == 'up'):
                return False
        else:
            return False

        # 短线盘中突破
        pass

        # 满足三重滤网条件可开仓
        return True

    def set_position(self, PL_ratio, win_rate):
        """
        设置仓位
            凯利公式：
                每次下注占总资产的比例 = (盈亏比 × 获胜概率 - 失败概率) / 盈亏比
        """
        return (PL_ratio * win_rate - (1-win_rate)) / PL_ratio

    def set_stop_loss():
        """
        设置止损
        """
        pass

    def is_close_out(self, status, long_data, short_data):
        """
        是否平仓
        """
        long_trend, _ = MACD.trend(long_data, timeperiod=7)
        short_trend, _ = MACD.trend(short_data, timeperiod=7)
        # 根据长线MACD判断趋势是否反转,短线趋势反转
        if status == 'buy':
            if (long_trend == 'down') & (short_trend == 'down'):
                return True
        elif status == 'sell':
            if (long_trend == 'up') & (short_trend == 'up'):
                return True
        # 继续持有
        return False