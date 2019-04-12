from exchange import Exchange, Side
from pprint import pprint
import re
import helpers
import statistics

import cProfile
import re

def profileFunction():
    cur = 'ETH'
    priceStep = 10
    ex = Exchange(debug = True, startTime = 1554681601, hours = 12, stepTime = priceStep)

    # Price stat variables to feed our neural network.
    avgTime = 600 # 600 second (10 minute) moving average.
    movAvg = None

    prePrices = []
    maxPrePrices = int(avgTime / priceStep)

    while True:
        # Get a new price list.
        ex.updatePrices()
        curPrice = ex.getPriceUSD('ETH')
        if curPrice == None:
            break

        prePrices.append(curPrice)
        if len(prePrices) > maxPrePrices:
            prePrices.pop(0)
        
        if len(prePrices) == maxPrePrices:
            movAvg = helpers.expMovingAvg(prePrices, .5)

    print('Done.')

cProfile.run('profileFunction()')