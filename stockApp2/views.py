import requests
import pandas as pd
from datetime import datetime, date, timedelta
from django.contrib import messages
# from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http.response import HttpResponse
from django.db import IntegrityError
from django.template import loader
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import dateformat, formats, timezone
from django.views import View
from django.views import generic
from stockApp2.forms import AddStockForm, DeleteStockForm
from .models import Stock, StockPrice
from .utils import MarketStack


def index(request):
    return render(request, 'index.html')


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class StockController(View):
    def __init__(self):
        self.api_key = settings.API_KEY

    @method_decorator(login_required(login_url='/accounts/login/'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def stock_list(self, request):
        print("Stock: GET ALL")
        stocks = Stock.get_all()
        if stocks:
            for stock in stocks:
                stock2, stock_prices = Stock.get_by_symbol(stock.symbol)
                if stock_prices:
                    stock_prices = sorted(stock_prices, key=lambda stock_prices: stock_prices.date, reverse=True)
                    stock.close = stock_prices[0].close
                    stock.date = stock_prices[0].date
                    stock.volume = stock_prices[0].volume
                    stock.save(request)
        context = {'stocks': sorted(stocks, key=lambda stock: stock.symbol)}
        return render(request, 'stock_list.html', context)


    def stock_detail(self, request, symbol):
        stock, stock_prices = Stock.get_by_symbol(symbol)
        if stock and stock_prices:
            stock_prices = sorted(stock_prices, key=lambda stock_prices: stock_prices.date, reverse=True)
            stock.close = stock_prices[0].close
            stock.date = stock_prices[0].date
            stock.volume = stock_prices[0].volume
            stock.save(request)
            context = {'stock': stock, 'stock_prices': sorted(stock_prices, key=lambda stock_prices: stock_prices.date, reverse=True)}
            return render(request, 'stock_detail.html', context)
        else:
            messages.error(request, f"{symbol} does not exist")
            return redirect(reverse('stock_list'))


    # @login_required
    def get_api_stock_history(self, symbol, date_from):
        # Use the MarketStack class to retrieve the historical data
        stock_df = MarketStack.get_price_history(symbol, date_from)
        if stock_df is not None:
            return stock_df
        else:
            return None

    # @login_required
    def get_api_list_history(self, symbol_lst, date_from_lst):
        # Use the MarketStack class to retrieve the historical data
        stock_df = MarketStack.get_price_history(symbol_lst, date_from_lst)
        if stock_df is not None:
            return stock_df
        else:
            return None

    def update_stock(self, request, symbol, name, date, isStockList=False):
        stock, stock_prices = Stock.get_by_symbol(symbol)
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d").date()
        date_from = date + timedelta(days=1)
        stock_df = self.get_api_stock_history(symbol, date_from)
        print(stock_df)
        if stock_df is not None and len(stock_df) > 0:
            stock_df.sort_values(by=['date'], inplace=True, ascending=False)
            print("Sucessfully retrieved update data from API")
            print(len(stock_df), "rows retrieved")
            print(stock_df)
            # If the API call was successful, save the stock and its price history
            stock.close = stock_df.iloc[0]['close']
            stock.name = name
            stock.volume = stock_df.iloc[0]['volume']
            stock.date = stock_df.iloc[0]['date']
            stock.save(request)
            stock_prices = []
            for index, row in stock_df.iterrows():
                stock_price = StockPrice(stock=stock,
                                        open=row['open'],
                                        high=row['high'],
                                        low=row['low'],
                                        close=row['close'],
                                        volume=row['volume'],
                                        adj_high=row['adj_high'],
                                        adj_low=row['adj_low'],
                                        adj_close=row['adj_close'],
                                        adj_open=row['adj_open'],
                                        adj_volume=row['adj_volume'],
                                        split_factor=row['split_factor'],
                                        dividend=row['dividend'],
                                        symbol=row['symbol'],
                                        exchange=row['exchange'],
                                        date=row['date'].date())
                stock_price.save(request)
                stock_prices.append(stock_price)
            # Sort the stock prices in descending order by date
            stock_prices.sort(key=lambda x: x.date, reverse=True)
        if not isStockList:
            return redirect(reverse('stock_detail', kwargs={'symbol': symbol}))
        else:
            return


    def update_stock_list(self, request):
        stocks = Stock.get_all()
        symbol_lst = []
        date_from_lst = []
        name_lst = []
        for stock in stocks:
            symbol_lst.append(stock.symbol)
            date_from_lst.append(stock.date)
            name_lst.append(stock.name)
        for i in range(len(symbol_lst)):
            self.update_stock(request, symbol_lst[i], name_lst[i], date_from_lst[i], True)
        return redirect(reverse('stock_list'))


    # @login_required(login_url='/accounts/login/')
    def add_stock(self, request):
        if request.method == 'POST':
            form = AddStockForm(request.POST)
            if form.is_valid():
                stock_df = None
                symbol = form.cleaned_data['symbol']
                name = form.cleaned_data['name']
                date_to = date.today()
                date_from = date_to.replace(year=date_to.year - 1)
                stock_df = self.get_api_stock_history(symbol, date_from)
                if stock_df is not None and len(stock_df) > 0:
                    # If the API call was successful, save the stock and its price history
                    stock = Stock(symbol=symbol, name=name, close=stock_df.iloc[0]['close'], 
                                  date=stock_df.iloc[0]['date'], volume=stock_df.iloc[0]['volume'],
                                  exchange=stock_df.iloc[0]['exchange'])
                    stock.save(request)
                    for index, row in stock_df.iterrows():
                        stock_price = StockPrice(stock=stock,
                                                open=row['open'],
                                                high=row['high'],
                                                low=row['low'],
                                                close=row['close'],
                                                volume=row['volume'],
                                                adj_high=row['adj_high'],
                                                adj_low=row['adj_low'],
                                                adj_close=row['adj_close'],
                                                adj_open=row['adj_open'],
                                                adj_volume=row['adj_volume'],
                                                split_factor=row['split_factor'],
                                                dividend=row['dividend'],
                                                symbol=row['symbol'],
                                                exchange=row['exchange'],
                                                date=row['date'])
                        stock_price.save(request)
                    return redirect(reverse('stock_detail', kwargs={'symbol': symbol}))
                else:
                    # If there's an error with the API call, use a default value of 0 for the price
                    # msg = f"Error retrieving stock history for {symbol}"
                    form.add_error('symbol', f'No data found for {symbol}')
            else:
                form = AddStockForm()
        else:
            form = AddStockForm()
        context = {'form': form}
        return render(request, 'add_stock.html', context)


    def delete_stock(self, request, symbol):
        # stock = Stock.get_by_symbol(symbol)
        stock = Stock.get_by_symbol(symbol)[0]
        if request.method == 'POST':
            form = DeleteStockForm(request.POST, instance=stock)
            if form.is_valid():
                stock.delete()
                return redirect('stock_list')
        else:
            form = DeleteStockForm(instance=stock)
        context = {'form': form, 'stock': stock}
        return render(request, 'delete_stock.html', context)