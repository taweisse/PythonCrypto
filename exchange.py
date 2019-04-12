# Interacts with the cryptocurrency exchange for trading, or simulates such actions in debug mode.

from glob import glob
import os
import time
import re
from types import MethodType
from pprint import pprint
import helpers
from enum import Enum

class OrderTypes(Enum):
    market = 0
    limit = 1

class TifType(Enum):
    GTC = 0
    IOC = 1
    FOK = 2

class Side(Enum):
    buy = 0
    sell = 1

class Exchange:
    def __init__(self, debug = True, startTime = None, hours = None, stepTime = 5):
        self._names = None
        self._curTime = None
        self._curPrices = None # A dictionary of the current exchange market prices.
        
        # Set up debug-only variables.
        if debug:
            endTime = None
            if startTime and hours:
                endTime = startTime + (hours * 3600)
            self._curPricesIterator = _readHistoricalPrices('../Price Recording/prices-*.csv', startTime, endTime, stepTime)
            self._wallet = None

        def d_updatePrices(self):
            self._curTime, self._curPrices = next(self._curPricesIterator, (None, None))

            # Initialize the names list and debug wallet on first call.
            if not self._names:
                self.updateNames()
                self._wallet = {name: float(0) for name in self._names}
            
            return self._curPrices

        def p_updatePrices(self):
            print('Production mode update prices function goes here.')

        # ----------

        def d_order(self, symbol, side, quantity, type = OrderTypes.market, price = None, timeInForce = TifType.FOK, RecWindow = 1000):
            # Determine the 2 currencies in question.
            cur1 = helpers.huffmanDecode(symbol, self._names)
            cur2 = symbol.replace(cur1, '')

            # Determine how much of each currency we will be trading.
            amt1 = quantity
            amt2 = quantity * self._curPrices[symbol]

            if side == Side.buy:
                if self._wallet[cur2] < amt2:
                    return False
                self._wallet[cur1] += amt1
                self._wallet[cur2] -= amt2
            
            else:
                if self._wallet[cur1] < amt1:
                    return False
                self._wallet[cur1] -= amt1
                self._wallet[cur2] += amt2

        def p_order(self, symbol, side, quantity, type = OrderTypes.market, price = None, timeInForce = TifType.FOK, RecWindow = 1000):
            print('Production mode order function goes here.')

        # ----------

        def d_deposit(self, currency, quantity):
            self._wallet[currency] += float(quantity)

        # Assign the correct functions depending on weather or not we are in debug mode.
        if debug:
            self.updatePrices = MethodType(d_updatePrices, self)
            self.order = MethodType(d_order, self)
            self.deposit = MethodType(d_deposit, self)
        else:
            self.updatePrices = MethodType(p_updatePrices, self)
            self.order = MethodType(p_order, self)

    def updatePrices(self):
        pass

    def order(self, symbol, side, quantity, type = OrderTypes.market, price = None, timeInForce = TifType.FOK, RecWindow = 1000):
        """Attempts to execute an order on a given market.
        
        Arguments:
            symbol {str} -- The symbol for the desired market.
            side {Side} -- The side of the chosen market, e.g. buy or sell.
            quantity {float} -- The amount of currency to buy or sell.
        
        Keyword Arguments:
            type {OrderType} -- The type of order to be executed, e.g. Market or Limit. (default: {OrderTypes.market})
            price {float} -- The desired price to buy or sell at. Required for limit orders. (default: {None})
            timeInForce {TifType} -- The time in force of the order, e.g. Good Till Cancelled (GTC), Immediate or Cancel (IOC), or Fill or Kill (FOK) (default: {TifType.FOK})
            RecWindow {int} -- The time in milliseconds which the order must be processed in before it is cancelled automatically. (default: {1000})
        """

        pass

    def deposit(self, currency, quantity):
        """Deposits some amount of some currency to the virtual wallet when running in debug mode.
        
        Arguments:
            currency {str} -- The name of the currency to deposit.
            quantity {float} -- The quantity to deposit.
        """

        pass

    def getPrice(self, market = None):
        if not market:
            return self._curPrices
        try:
            return self._curPrices[market]
        except:
            return None

    def getPriceUSD(self, name):
        if self._curPrices == None:
            return None

        priceSum = 0
        for market in ['BTCUSDT', 'BTCTUSD', 'BTCUSDC', 'BTCUSDS']:
            priceSum += float(self._curPrices[market])
        btcPrice = priceSum / 4
        
        if name == 'BTC':
            return btcPrice
        else:
            return btcPrice * self.getPrice(name + 'BTC')

    def getNames(self):
        return self._names

    def getUpdateTime(self):
        return self._curTime

    def updateNames(self):
        self._names = ['BTC']
        for market in self._curPrices:
            if re.match(r'.+BTC', market):
                self._names.append(market.replace(r'BTC', ''))
        self._names.sort()

def _readHistoricalPrices(format, startTime, endTime, stepTime):
    """Generates price information over time from historical data stored on disk.
    
    Arguments:
        format {str} -- A regex which matches the files containing historical price information.
        startTime {int} -- The UNIX timestamp to start historical prices at. 'None' for the epoch.
        endTime {Number} -- The UNIX timestamp to end historical prices at. 'None' for the current time.
    """

    def skipToTimestamp(f, ts):
        while True:
            line = f.readline()
            if line == '':
                return
            elif int(line.split(', ')[0]) > ts:
                f.seek(f.tell() - len(line), os.SEEK_SET)
                break

    # Get a list of all files matching the format string.
    files = glob(format)

    # Do not include the last file if it is still being appended to.
    if abs(time.time() - os.path.getmtime(files[-1])) < 600:
        del files[-1]

    # Default start and end timestamps.
    if not startTime:
        startTime = 0
    if not endTime:
        endTime = time.time()

    # Define variables to track the relevent files for this time period.
    startIdx = 0
    endIdx = len(files)

    # Determine which files fall within our time period.
    for idx, curFile in enumerate(files):
        with open(curFile, 'r') as f:
            firstTs = int(f.readline().split(', ')[0])
            lastTs = int(helpers.readLastLine(f).split(', ')[0])
            if firstTs > endTime and idx < endIdx:
                endIdx = idx
            if lastTs < startTime:
                startIdx = idx + 1

    # Remove files which dont fall in the time period.
    files = files[startIdx:endIdx]

    curTs = startTime
    for curFile in files:
        with open(curFile, 'r', newline = '') as f:
            while True:
                # Skip to the next timestamp step.
                skipToTimestamp(f, curTs)
                curTs += stepTime

                # Read all lines with the same timestamp and add them to a dictionary object.
                prices = {}
                ts = None
                eof = False
                while True:
                    line = f.readline()
                    if line == '':
                        eof = True
                        break

                    parts = line.split(', ')

                    # Ensure we dont keep overwritting the timestamp each read.
                    if not ts:
                        ts = int(parts[0])

                        # Stop yielding if we have reached the end timestamp.
                        if ts > endTime:
                            eof = True
                            break
                    
                    # We have read all current prices if the timestamp changes.
                    if ts != int(parts[0]):
                        f.seek(f.tell() - len(line), os.SEEK_SET)
                        break

                    # Add prices to the dictionary.
                    prices[parts[1]] = float(parts[2])

                if eof:
                    break
                yield parts[0], prices
