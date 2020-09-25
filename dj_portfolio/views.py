from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy

import datetime
import json
import pandas as pd
import requests
import threading
import yfinance as yf

from dj_portfolio.models import *
import dj_portfolio.forms as forms
import pdb


def index(request):

    portfolios = Portfolio.objects.all()
    context = {
        'portfolios': portfolios
        }
    
    return render(request, 'dj_portfolio/index.html', context)

class PortfolioCreate(CreateView):
    model = Portfolio
    fields = "__all__"

class PortfolioDetail(DetailView):
    model = Portfolio
        
    def get_context_data(self, **kwargs):
        context = super(PortfolioDetail, self).get_context_data(**kwargs)
        context['holdingForm'] = forms.HoldingForm()
        
        return context
 
class PortfolioList(ListView):
    model = Portfolio
    
class PortfolioUpdate(UpdateView):
    model = Portfolio
    fields = "__all__"

class PortfolioDelete(DeleteView):
    model = Portfolio
    success_url="/portfolio/"

def PortfolioAddHolding(request):

    portfolio = Portfolio.objects.get(pk=request.POST.get('portfolio'))
    stock, created = Stock.objects.get_or_create(ticker=request.POST.get('stock'))
    if created:
        ystock = yf.Ticker(stock.ticker)
        info = {}
        try:
            stock.name = ystock.info['shortName']
        except:
            # if you are here, maybe install https://github.com/siavashadpey/yfinance
            pdb.set_trace()

        stock.sector = ystock.info['sector']
        stock.industry = ystock.info['industry']
        stock.div_yield = ystock.info['dividendYield']
        stock.history = json.loads(json.dumps(ystock.history(period='max').to_dict(orient='split'), cls=DjangoJSONEncoder))
        stock.save()
            
    Holding.objects.get_or_create(
        portfolio=portfolio,
        stock=stock,
        quantity=request.POST.get('quantity'),
        )

        
    
    return(HttpResponse(True))


class HoldingCreate(CreateView):
    model = Holding
    fields = "__all__"

class HoldingDetail(DetailView):
    model = Holding

class HoldingList(ListView):
    model = Holding
    
class HoldingUpdate(UpdateView):
    model = Holding
    fields = "__all__"

class HoldingDelete(DeleteView):
    model = Holding

    def get_success_url(self):
        return reverse_lazy('portfolio:portfolio-detail', kwargs={'pk': self.object.portfolio.id})

class StockCreate(CreateView):
    model = Stock
    fields = "__all__"    

class StockDetail(DetailView):
    model = Stock
    
    def get_context_data(self, **kwargs):
        context = super(StockDetail, self).get_context_data(**kwargs)

        fins = pd.read_json(json.dumps(self.object.history), orient='split')

        context['divs'] = pd.DataFrame(
            (fins
             .groupby(fins.index.year)
             .sum()['Dividends'][-11:])
            ).T.to_html(table_id='dividends',
                        index=False,
                        border=0,
                        justify='left',
                        classes='table table-bordered',
                        escape=False
            )
        
        
        return context
    

class StockList(ListView):
    model = Stock
    
class StockUpdate(UpdateView):
    model = Stock
    fields = "__all__"

class StockDelete(DeleteView):
    model = Stock

    def get_success_url(self):
        return reverse_lazy('portfolio:portfolio-detail', kwargs={'pk': self.object.portfolio.id})


def get_stock_price(request):

    prices = yf.download(request.GET['ticker'],
                         '2018-09-01',
                         datetime.datetime.strftime(
                             datetime.datetime.today(), '%Y-%m-%d'))

    return JsonResponse(json.loads(prices['Close'].to_json(orient='split')))

def get_portfolio_value(request, pk):

    port = Portfolio.objects.get(pk=pk)
    start = '2019-01-01'

    if port.holding_set.all().count() == 0:
        return JsonResponse(
            json.loads(json.dumps({'msg': 'No stocks'}
            )))

    if port.holding_set.all().count() >= 1:
        # get portfolio values
        tickers = ' '.join(port.holding_set.all().values_list('stock__ticker', flat=True))
        prices = yf.download(tickers,
                             start,
                             datetime.datetime.strftime(
                                 datetime.datetime.today(), '%Y-%m-%d'))['Close']
        quants = port.holding_set.all().values_list('quantity', flat=True)

        if quants.count() > 1:
            values = (prices * quants).sum(axis=1)
        else:
            values = (prices * quants)
            
        values = (values/values[0]).to_json(orient='split')

        port_data = json.loads(values)
        port_data['port'] = port_data.pop('data')

        # get benchmark values
        spy = yf.download('SPY',
                          start,
                          datetime.datetime.strftime(
                              datetime.datetime.today(), '%Y-%m-%d'))['Close']
        spy = spy/spy[0]
        port_data['spy'] = spy.tolist()
        
        return JsonResponse(port_data)
