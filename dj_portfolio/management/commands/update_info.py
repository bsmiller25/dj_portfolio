from django.core.management.base import BaseCommand, CommandError
from dj_portfolio.models import *

class Command(BaseCommand):
    help = 'Refresh stock data'

    def handle(self, *args, **kwargs):
        stocks = Stock.objects.all()

        for stk in stocks:
            stk.refresh_info()

    
