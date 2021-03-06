# encoding: UTF-8
# FROK FROM: https://github.com/zb2017/api

import hashlib
import zlib
import json
from time import sleep
from threading import Thread

import websocket    
import urllib.request as urllib2
import hashlib, struct, time


ZB_WS_URL = "wss://api.zb.com/websocket"#"wss://api.zb.com:9999/websocket"

class ZB_Spot_WS_Api(object):
    """基于Websocket的API对象"""
    def __init__(self, apiKey, secret, quick_symbol = '/eth', onMessage = None, onError = None, onClose = None, onOpen = None):
        """Constructor"""
        self.host = ZB_WS_URL
        self.quick_host = ZB_WS_URL + quick_symbol
        self.apiKey = apiKey        # apiKey
        self.secretKey = secret     # secretKey

        self.ws_sub_spot = None          # websocket应用对象  现货对象
        self.ws_sub_quick_spot = None          # websocket快速行情推送

        if onMessage: 
            self.onMessage = onMessage 
        if onError:
            self.onError = onError
        if onClose:
            self.onClose = onClose
        if onOpen:
            self.onOpen = onOpen

        self.connect_Subpot(trace=False)
        time.sleep(3)

    #----------------------------------------------------------------------
    def reconnect(self):
        """重新连接"""
        # 首先关闭之前的连接
        try:
            self.close()
        except Exception as e:
            print(e)

        sleep(5)
        
        # 再执行重连任务
        self.ws_sub_spot = websocket.WebSocketApp(self.host, 
                                             on_message=self.onMessage,
                                             on_error=self.onError,
                                             on_close=self.onClose,
                                             on_open=self.onOpen)        

        self.ws_sub_quick_spot = websocket.WebSocketApp(self.quick_host, 
                                             on_message=self.onMessage,
                                             on_error=self.onError,
                                             on_close=self.onClose,
                                             on_open=self.onOpen)   
            
        self.thread = Thread(target=self.ws_sub_spot.run_forever, kwargs={'ping_interval':10, 'ping_timeout':5})
        self.thread.start()
        self.thread_quick = Thread(target=self.ws_sub_quick_spot.run_forever, kwargs={'ping_interval':10, 'ping_timeout':5})
        self.thread_quick.start()
    
    #----------------------------------------------------------------------
    def connect_Subpot(self, trace = False):
        #self.host = zb_usd_url
        #self.apiKey = apiKey
        #self.secretKey = secretKey

        websocket.enableTrace(trace)

        self.ws_sub_spot = websocket.WebSocketApp(self.host, 
                                             on_message=self.onMessage,
                                             on_error=self.onError,
                                             on_close=self.onClose,
                                             on_open=self.onOpen)        

        self.ws_sub_quick_spot = websocket.WebSocketApp(self.quick_host, 
                                             on_message=self.onMessage,
                                             on_error=self.onError,
                                             on_close=self.onClose,
                                             on_open=self.onOpen)   
            
        self.thread = Thread(target=self.ws_sub_spot.run_forever, kwargs={'ping_interval':10, 'ping_timeout':5})
        self.thread.start()
        self.thread_quick = Thread(target=self.ws_sub_quick_spot.run_forever, kwargs={'ping_interval':10, 'ping_timeout':5})
        self.thread_quick.start()

    #----------------------------------------------------------------------
    def readData(self, evt):
        """解压缩推送收到的数据"""
        # # 创建解压器
        # decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        
        # # 将原始数据解压成字符串
        # inflated = decompress.decompress(evt) + decompress.flush()
        
        # 通过json解析字符串
        data = json.loads(evt)
        
        return data

    #----------------------------------------------------------------------
    def close(self):
        """关闭接口"""
        if self.thread and self.thread.isAlive():
            self.ws_sub_spot.close()
            #self.thread.join()

        if self.thread_quick and self.thread_quick.isAlive():
            self.ws_sub_quick_spot.close()
            #self.thread_quick.join()

    #----------------------------------------------------------------------
    def onMessage(self, ws, evt):
        """信息推送""" 
        print(evt)
        
    #----------------------------------------------------------------------
    def onError(self, ws, evt):
        """错误推送"""
        print('onError:', evt)
        
    #----------------------------------------------------------------------
    def onClose(self, ws, *arg):
        """接口断开"""
        print('onClose:', arg)
        
    #----------------------------------------------------------------------
    def onOpen(self, ws):
        """接口打开"""
        print('onOpen')

    #----------------------------------------------------------------------
    def subscribeSpotTicker(self, symbol_pair):
        # 现货的 ticker
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_ticker'}" % symbol_pair
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotDepth(self, symbol_pair):
        # 现货的 市场深度
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_depth'}" % symbol_pair
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotTrades(self, symbol_pair):
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_trades'}" % symbol_pair
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotQuickDepth(self, symbol_pair):
        # 现货的 快速市场深度
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_quick_depth'}" % symbol_pair
        self.ws_sub_quick_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotQuickUserRecord(self, symbol_pair):
        # 现货的 订单变更
        symbol_pair = symbol_pair.replace('_','')
        params = {
            'market': symbol_pair + 'default'
        }
        self.sendTradingRequest('push_user_record', params, quick=True)

    #----------------------------------------------------------------------
    def subscribeSpotQuickUserIncrRecord(self, symbol_pair):
        # 现货的 增量订单变更
        symbol_pair = symbol_pair.replace('_','')
        params = {
            'market': symbol_pair + 'default'
        }
        self.sendTradingRequest('push_user_incr_record', params, quick=True)

    #----------------------------------------------------------------------
    def subscribeSpotQuickUserAsset(self, symbol_pair):
        # 现货的 资产变更
        params = {}
        self.sendTradingRequest('push_user_asset', params, quick=True)

    #----------------------------------------------------------------------
    def subscribeSpotQuickUserIncrAsset(self, symbol_pair):
        # 现货的 增量资产变更
        params = {}
        self.sendTradingRequest('push_user_incr_asset', params, quick=True)

    #----------------------------------------------------------------------
    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize
    #----------------------------------------------------------------------
    def __doXOr(self, s, value):
        slist = list(s)
        for index in range(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)
    #----------------------------------------------------------------------
    def __hmacSign(self, aValue, aKey):
        keyb   = struct.pack("%ds" % len(aKey), aKey).decode('ascii')
        value  = struct.pack("%ds" % len(aValue), aValue)
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54).encode('ascii')
        k_opad = self.__fill(k_opad, 64, 92).encode('ascii')
        m = hashlib.md5()
        m.update(k_ipad)
        m.update(value)
        dg = m.digest()
        
        m = hashlib.md5()
        m.update(k_opad)
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    #----------------------------------------------------------------------
    def __digest(self, aValue):
        value  = struct.pack("%ds" % len(aValue), aValue)
        #h = sha.new()
        h = hashlib.sha1()
        h.update(value)
        dg = h.hexdigest()
        return dg

    #----------------------------------------------------------------------
    def generateSign(self, params):
        """生成签名"""
        '''
        {"accesskey":"0f39fb8b-d95d-4afe-b2a9-94f5f4d9fdb5","channel":"getaccountinfo","event":"addChannel"}
        '''
        l = []
        for key in sorted(params.keys()):
            l.append('"%s":"%s"' %(key, params[key]))
        sign = ','.join(l)
        sign = '{' + sign + '}'

        SHA_secret = self.__digest(self.secretKey.encode('ascii'))
        return self.__hmacSign( sign.encode('ascii'), SHA_secret.encode('ascii'))
        # return hashlib.md5(sign.encode('utf-8')).hexdigest().upper()

    #----------------------------------------------------------------------
    def sendTradingRequest(self, channel, params, quick = False):
        """发送交易请求"""
        # 在参数字典中加上api_key和签名字段
        params['accesskey'] = self.apiKey
        params['channel'] = channel
        params['event'] = "addChannel"

        params['sign'] = self.generateSign(params)
        
        # 使用json打包并发送
        j = json.dumps(params)
        
        # 若触发异常则重连
        try:
            if quick:
                self.ws_sub_quick_spot.send(j)
            else:
                self.ws_sub_spot.send(j)
        except websocket.WebSocketConnectionClosedException:
            pass 

    #----------------------------------------------------------------------
    def spotTrade(self, symbol_pair, type_, price, amount, no='0'):
        """现货委托"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['tradeType'] = str(type_)
        params['price'] = str(price)
        params['amount'] = str(amount)
        params['no'] = no
        
        channel = symbol_pair.lower() + "_order"
        
        self.sendTradingRequest(channel, params)

    #----------------------------------------------------------------------
    def spotCancelOrder(self, symbol_pair, orderid):
        """现货撤单"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['id'] = str(orderid)
        
        channel = symbol_pair.lower() + "_cancelorder"

        self.sendTradingRequest(channel, params)
    
    #----------------------------------------------------------------------
    def spotUserInfo(self):
        """查询现货账户"""
        channel = 'getaccountinfo'
        self.sendTradingRequest(channel, {})

    #----------------------------------------------------------------------
    def spotOrderInfo(self, symbol_pair, orderid):
        """查询现货委托信息"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['id'] = str(orderid)
        
        channel = symbol_pair.lower() + "_getorder"
        
        self.sendTradingRequest(channel, params)

    #----------------------------------------------------------------------
    def spotGetOrders(self, symbol_pair , orderid):
        pass