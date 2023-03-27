import requests
import pandas as pd
from django.db import IntegrityError
from django.db import transaction
from django.shortcuts import render, redirect
from django.db import models
from django.urls import reverse
from django.conf import settings
from django import forms
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import Permission, User
from math import isnan


class Stock(models.Model):
    api_key = settings.API_KEY
    id = models.AutoField(primary_key=True)
    user_symbol = models.CharField(max_length=10, unique=True, null=True)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=50, default="")
    date = models.DateField(default=None, null=True)
    close = models.DecimalField(max_digits=6, decimal_places=2, default=None, null=True)
    volume = models.IntegerField(default=0)
    exchange = models.CharField(max_length=6)

    def __str__(self):
        return self.symbol

    @classmethod
    def get_all(cls):
        return cls.objects.all()

    @classmethod
    def get_by_symbol(cls, symbol):
        try:
            stock = cls.objects.prefetch_related('stockprice_set').get(symbol=symbol)
            return stock, stock.stockprice_set.all()
        except cls.DoesNotExist:
            return None

    @classmethod
    def add_stock(cls, symbol, name):
        stock = cls(symbol=symbol, name=name)
        stock.save()
        return stock

    def delete_stock(self):
        self.delete()

    def save(self, request, *args, **kwargs):
        if not self.user_symbol:
            current_user = request.user
            self.user_symbol = f"{current_user}_{self.symbol}"

        if self.get_by_symbol(self.symbol) == None:
            with transaction.atomic():
                try:
                    super().save(request, *args, **kwargs)
                except IntegrityError:
                    existing = Stock.objects.get(symbol=self.symbol)
                    existing.name = self.name
                    existing.date = self.date
                    existing.close = self.close
                    existing.volume = self.volume
                    existing.exchange = self.exchange
                    existing.save()


class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    userId = models.IntegerField(default=0)
    user_stock_date = models.CharField(max_length=10, unique=True, null=True)
    date = models.DateField(default=None, null=True)
    open = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    high = models.DecimalField(max_digits=6, decimal_places=2,default=None, null=True)
    low = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    close = models.DecimalField(max_digits=6, decimal_places=2,default=None, null=True)
    volume = models.IntegerField(default=0, null=True)
    adj_high = models.DecimalField(max_digits=6, decimal_places=2,default=None, null=True)
    adj_low = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    adj_close = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    adj_open = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    adj_volume = models.IntegerField(default=0, null=True)
    split_factor = models.DecimalField(max_digits=4, decimal_places=2, default=None,null=True)
    dividend = models.DecimalField(max_digits=5, decimal_places=2, default=None, null=True)
    symbol = models.CharField(max_length=10)
    exchange = models.CharField(max_length=6)


    def __str__(self):
        return f"{self.stock.id}: {self.close} ({self.date})"

    def save(self, request, *args, **kwargs):
        if not self.user_stock_date:
            current_user = request.user
            self.user_stock_date = f"{current_user}_{self.symbol}_{self.date.strftime('%Y-%m-%d')}"

        # Check for NaN values and replace them with None
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if isinstance(value, float) and isnan(value):
                setattr(self, field.name, None)

         # Save the related stock object if it hasn't been saved yet
        if self.stock.pk is None:
            self.stock.save(request)

        existing_record = StockPrice.objects.filter(user_stock_date=self.user_stock_date).first()
        if not existing_record:
            with transaction.atomic():
                try:
                    super().save(request, *args, **kwargs)
                except IntegrityError:
                    existing = StockPrice.objects.get(stock_date=self.stock_date)
                    existing.date = self.date
                    existing.open = self.open
                    existing.high = self.high
                    existing.low = self.low
                    existing.close = self.close
                    existing.volume = self.volume
                    existing.adj_high = self.adj_high
                    existing.adj_low = self.adj_low
                    existing.adj_close = self.adj_close
                    existing.adj_open = self.adj_open
                    existing.adj_volume = self.adj_volume
                    existing.split_factor = self.split_factor
                    existing.dividend = self.dividend
                    existing.symbol = self.symbol
                    existing.exchange = self.exchange
                    existing.save()


class UserStock(models.Model):
    userId= models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.userId}: {self.stock.symbol}"

    @classmethod
    def add_user_stock(cls, request, symbol):
        current_user = request.user
        user_stock = cls(userId=current_user, symbol=symbol)
        user_stock.save()
        return user_stock

    @classmethod
    def get_user_stocks(cls, request):
        current_user = request.user
        user_stocks = cls.objects.filter(userId=current_user)
        return [user_stock.symbol for user_stock in user_stocks]
