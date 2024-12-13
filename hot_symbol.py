import requests
import json
import time

def get_available_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange info: {e}")
        return []

    available_symbols = []
    if 'symbols' in data:
      for symbol_info in data['symbols']:
          if symbol_info['status'] == 'TRADING':
              available_symbols.append(symbol_info['symbol'])
    return available_symbols

def is_futures_tradable(symbol):
    available_symbols = get_available_futures_symbols()
    return symbol in available_symbols

def get_top_tradable_gainers():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

    futures_data = [item for item in data if item['symbol'].endswith('USDT')]
    sorted_data = sorted(futures_data, key=lambda x: float(x['priceChangePercent']), reverse=True)

    tradable_gainers = []
    for item in sorted_data:
        if is_futures_tradable(item['symbol']):
            tradable_gainers.append(item)
            if len(tradable_gainers) >= 30:
                break
    return tradable_gainers

def get_30day_high_low(symbol):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": "1d",
        "limit": 30
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Klines data for {symbol}: {e}")
        return None, None
        
    if not data: # check if data is empty
        print(f"No Klines data for {symbol}")
        return None, None

    high_prices = [float(item[2]) for item in data]
    low_prices = [float(item[3]) for item in data]

    if not high_prices or not low_prices:
        print(f"Missing high or low price data for {symbol}")
        return None, None
    
    high = max(high_prices)
    low = min(low_prices)
    return high, low

def get_ticker_info(symbol):
  url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
  try:
        response = requests.get(url)
        response.raise_for_status()
        data = json.loads(response.text)
        return data
  except requests.exceptions.RequestException as e:
        print(f"Error fetching ticker data for {symbol}: {e}")
        return None

def format_volume(volume):
    volume = float(volume)
    if volume >= 100000000:  # 1亿
        return f"{volume/100000000:.2f}亿"
    elif volume >= 10000:    # 1万
        return f"{volume/10000:.2f}万"
    else:
        return f"{volume:.2f}"

def main():
    top_gainers = get_top_tradable_gainers()

    if not top_gainers:
        print("未能获取到可交易的涨幅榜币种。")
        return

    print("做空备选，涨幅榜过去30天涨幅超200%的币种:")
    displayed_count = 0
    for gainer in top_gainers:
        symbol = gainer['symbol']
        high, low = get_30day_high_low(symbol)
        if high is None or low is None:
            print(f"无法获取{symbol}的30天高低价信息。")
            continue

        ticker_info= get_ticker_info(symbol)
        if ticker_info is None:
            print(f"无法获取{symbol}的24小时交易额信息。")
            continue

        current_price = float(gainer['lastPrice'])
        change_percent = (high / low) * 100 if low !=0 else 0 # avoid division by zero
        current_increase = (current_price / low) * 100 if low !=0 else 0
        
        # Skip if current increase is less than 200%
        if current_increase < 200:
            continue

        displayed_count += 1
        print(f"币种：{symbol}")
        print(f"  30天最高价：{high}")
        print(f"  30天最低价：{low}")
        print(f"  当前价格：{current_price}")
        print(f"  24小时涨跌幅：{float(ticker_info['priceChangePercent']):.2f}%")
        print(f"  最高涨幅（最高/最低）：{change_percent:.2f}%")
        print(f"  当前涨幅（当前/最低）：{current_increase:.2f}%")
        print(f"  24小时成交额：{format_volume(ticker_info['quoteVolume'])}")
        time.sleep(0.2) # 降低请求频率
        
    if displayed_count == 0:
        print("没有找到当前涨幅超过200%的币种。")

if __name__ == "__main__":
    main()