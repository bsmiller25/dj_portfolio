from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from bs4 import BeautifulSoup
import yfinance as yf
import datetime
import json
import pandas as pd
import requests
import pdb


class Portfolio(models.Model):
    name = models.CharField(max_length=100)

    def get_absolute_url(self):
        return reverse('portfolio:portfolio-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return(self.name)

    @property
    def value(self):
        return(sum([i.value for i in self.holding_set.all()]))

    
    @property
    def display_value(self):
        return('${:,.2f}'.format(self.value))

    @property
    def div(self):
        return('{:.2f}%'.format(
            sum([i.share * i.stock.div_yield for i in self.holding_set.all() if i.stock.div_yield])))
    
            


class Holding(models.Model):
    portfolio = models.ForeignKey('Portfolio', on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    quantity = models.FloatField()
    
    def __str__(self):
        return('{} - {}'.format(self.portfolio, self.stock.ticker))

    @property
    def value(self):
        return(self.stock.price * self.quantity)

    @property
    def display_value(self):
        return('{:.2f}'.format(self.value))
        
    @property
    def share(self):
        return((self.value / self.portfolio.value) * 100)

    @property
    def display_share(self):
        return('{:.2f}%'.format(self.share))

    def get_absolute_url(self):
        return reverse('portfolio:portfolio-detail', kwargs={'pk': self.portfolio.pk})


class Stock(models.Model):
    ticker = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)
    sector = models.CharField(max_length=50, null=True, blank=True)
    industry = models.CharField(max_length=50, null=True, blank=True)
    div_yield = models.FloatField(null=True, blank=True)
    payoutRatio = models.FloatField(null=True, blank=True)
    clean200 = models.BooleanField(default=False)
    history = models.JSONField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('portfolio:stock-detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return(self.ticker)

    @property
    def price(self):
        try:
            return(self.history['data'][-1][3])
        except:
            return(0)

    @property
    def div(self):
        if self.div_yield:
            return('{:.2f}%'.format(self.div_yield * 100))
        else:
            return('0%')

    def get_sector_industry(self):

        url = 'https://eresearch.fidelity.com/eresearch/goto/evaluate/snapshot.jhtml?symbols=' + self.ticker
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content)

        self.sector = soup.findAll('div', {'class': 'sub-heading'})[0].find_all(text=True)[2]
        self.industry = soup.findAll('div', {'class': 'sub-heading'})[1].find_all(text=True)[2]
        
        self.save()

    def refresh_info(self):

        # https://www.asyousow.org/report-page/2020-clean200
        clean200 = ['AYI', 'APD', 'GOOG', 'AWK', 'ADI',
                    'AMAT', 'AUD', 'AGR', 'BLL', 'CSCO',
                    'CSX', 'DHR', 'DOV', 'EBAY', 'ECL',
                    'EMR', 'AQUA', 'FTV', 'GPK', 'GPRE',
                    'HPE', 'HPQ', 'INTC', 'ITRI', 'KSU',
                    'KMB', 'MKC', 'ON', 'PH', 'TSLA',
                    'UNFI', 'VMW', 'WM', 'WY', 'WDAY']

        if self.ticker in clean200:
            self.clean200 = True
        
        ystock = yf.Ticker(self.ticker)
        try:
            self.name = ystock.info['shortName']
        except:
            # if you are here, maybe install https://github.com/siavashadpey/yfinance
            pdb.set_trace()

        self.summary = ystock.info['longBusinessSummary']
        self.div_yield = ystock.info['dividendYield']
        self.payoutRatio = ystock.info['payoutRatio']
        self.logo_url = ystock.info['logo_url']
        self.history = json.loads(json.dumps(ystock.history(period='max').dropna().to_dict(orient='split'), cls=DjangoJSONEncoder))
        self.save()
