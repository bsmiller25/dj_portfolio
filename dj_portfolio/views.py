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
    #model = Portfolio
    queryset = Portfolio.objects.prefetch_related('holding_set', 'holding_set__stock')
        
    def get_context_data(self, **kwargs):
        context = super(PortfolioDetail, self).get_context_data(**kwargs)
        context['holdingForm'] = forms.HoldingForm()
        context['start'] = datetime.datetime.strftime(
            datetime.datetime(2020, 9, 28),
            '%Y-%m-%d')
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
        stock.refresh_info()
        stock.get_sector_industry()
        
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

        fins = pd.read_json(json.dumps(self.object.history))
        
        divs = fins['Dividends'][fins['Dividends'] != 0]
        splits = fins['Stock Splits'][fins['Stock Splits'] != 0]
        for date, split in splits.iteritems():
            divs[divs.index <= date] = divs[divs.index <= date]/split

        context['start'] = datetime.datetime.strftime(
             datetime.datetime(datetime.datetime.today().year - 1,
                               datetime.datetime.today().month,
                               datetime.datetime.today().day),
            '%Y-%m-%d')
        context['divs_chart'] = json.loads(divs.to_json(orient='split'))
        
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
                         request.GET['start'],
                         datetime.datetime.strftime(
                             datetime.datetime.today() + datetime.timedelta(days=1), '%Y-%m-%d'))
    return JsonResponse(json.loads(prices['Close'].to_json(orient='split')))

def get_portfolio_value(request, pk):

    port = Portfolio.objects.prefetch_related('holding_set', 'holding_set__stock').get(pk=pk)
    start = request.GET['start']

    if port.holding_set.all().count() == 0:
        return JsonResponse(
            json.loads(json.dumps({'msg': 'No stocks'}
            )))

    if port.holding_set.all().count() >= 1:

        prices_full = pd.DataFrame(Stock.objects.filter(holding__portfolio=port).order_by('ticker').values('ticker', 'history__Close'))

        df = pd.DataFrame()
        for ind, row in prices_full.iterrows():
            new = pd.DataFrame({row['ticker']: row['history__Close']})
            df = df.merge(new, "outer", left_index=True, right_index=True)
            
        prices_full = df
        prices_full.index = prices_full.index.astype('datetime64[ns]')
        prices_full = prices_full[prices_full.index >= start]
        prices = prices_full.dropna()

        try:
            if prices_full.isna().iloc[0,0]:
                prices_full = prices_full.iloc[1:,:]
        except IndexError:
            pass
        
        quants = port.holding_set.all().order_by('stock__ticker').values_list('quantity', flat=True)
            
        if quants.count() > 1:
            values = (prices * quants).sum(axis=1)
        else:
            values = (prices * quants)

        values = (values/values[0]).to_json(orient='split')

        port_data = json.loads(values)
        port_data['port'] = port_data.pop('data')
        
        new_start = datetime.datetime.strftime(prices.index[0], '%Y-%m-%d')
        orig_start = datetime.datetime.strftime(prices_full.index[0], '%Y-%m-%d')

        if new_start != orig_start:
            fault = prices_full.iloc[prices_full.index.get_loc(prices.index[0]) -1,]
            fault = fault[fault.isna()].index[0]

            port_data['msg'] = 'Earliest available: {}. No data for {}.'.format(
                new_start, fault)
 
        # get benchmark values
        sp500 = yf.download('^GSPC',
                          new_start,
                          datetime.datetime.strftime(
                              datetime.datetime.today() + datetime.timedelta(days=1), '%Y-%m-%d'))['Close'].dropna()

        sp500 = sp500/sp500[0]
        port_data['sp500'] = sp500.tolist()

        return JsonResponse(port_data)

def get_sector_balance(request, pk):
    port = Portfolio.objects.get(pk=pk)
    sect = {}

    # get sector sums
    for holding in port.holding_set.all():
        if holding.stock.sector not in sect.keys():
            sect[holding.stock.sector] = holding.value
        else:
            sect[holding.stock.sector] += holding.value

    # get ratios
    total = port.value
    sect = {key: round(val / total, 2) for key, val in sect.items()}

    sect = {'labels': list(sect.keys()),
            'data': list(sect.values())
            }
    
    return JsonResponse(json.loads(json.dumps(sect)))
    

