from django.urls import path
from django.contrib.auth.decorators import login_required

from dj_portfolio import views

app_name='portfolio'
urlpatterns = [
    # portfolio CRUD
    path('create/', views.PortfolioCreate.as_view(), name='portfolio-create'),
    path('', views.PortfolioList.as_view(), name='portfolio-list'),
    path('<int:pk>/', views.PortfolioDetail.as_view(), name='portfolio-detail'),
    path('<pk>/update', views.PortfolioUpdate.as_view(), name='portfolio-update'),
    path('<pk>/delete', views.PortfolioDelete.as_view(), name='portfolio-delete'),

    path('<pk>/value', views.get_portfolio_value, name='portfolio-value'),
    path('<pk>/sector', views.get_sector_balance, name='portfolio-sector'),

    path('<pk>/sector-comp/<sector>', views.sector_comp, name='sector-comp'),
    path('<pk>/sector-comp-data/<sector>', views.sector_comp_data, name='sector-comp-data'),
    
    # helper
    path('add-holding', views.PortfolioAddHolding, name='portfolio-add-holding'),

    # holding CRUD
    path('holding/create/', views.HoldingCreate.as_view(), name='holding-create'),
    path('holding/all/', views.HoldingList.as_view(), name='holding-list'),
    path('holding/<pk>/', views.HoldingDetail.as_view(), name='holding-detail'),
    path('holding/<pk>/update', views.HoldingUpdate.as_view(), name='holding-update'),
    path('holding/<pk>/delete', views.HoldingDelete.as_view(), name='holding-delete'),

    # stock
    path('stock/create/', views.StockCreate.as_view(), name='stock-create'),
    path('stock/all/', views.StockList.as_view(), name='stock-list'),
    path('stock/<pk>/', views.StockDetail.as_view(), name='stock-detail'),
    path('stock/<pk>/update', views.StockUpdate.as_view(), name='stock-update'),
    path('stock/<pk>/delete', views.StockDelete.as_view(), name='stock-delete'),

    path('stocky/get-price/', views.get_stock_price, name='get-stock-price'),

]

