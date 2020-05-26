from invest.collect import *


class Collect(object):
    """
    数据采集
    """
    def __init__(self):
        pass

    def get_etoro_data(self, vol, period, instrument_ID):
        """
        获取etoro数据
        :param vol: 量
        :param period: 周期
        :return:
        """
        url = 'https://candle.etorocn.com.cn/candles/desc.json/'+period+'/'+str(vol)+'/' + str(instrument_ID) + '?client_request_id=42cb406b-1f91-4f3e-8b54-145b964126ac'
        data = requests.get(url)
        result = json.loads(data.text)
        price = pd.DataFrame(result['Candles'][0]['Candles'])
        price['Period'] = period
        price['FromDate'] = pd.to_datetime(price['FromDate'])
        return price
