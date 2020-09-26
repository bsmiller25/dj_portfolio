from django.db import models
from django.urls import reverse
import yfinance as yf
import datetime
import json
import pandas as pd
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
    sector = models.CharField(max_length=50, null=True, blank=True)
    industry = models.CharField(max_length=50, null=True, blank=True)
    div_yield = models.FloatField(null=True, blank=True)
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
