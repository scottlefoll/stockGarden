from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from stockApp2.models import Stock
import requests
import pandas as pd


class AddStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['symbol', 'name']
        labels = {
            'symbol': 'Symbol',
            'name': 'Name'
        }
        widgets = {
            'symbol': forms.TextInput(attrs={'required': True}),
            'name': forms.TextInput(attrs={'required': True})
        }


class DeleteStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = []
        widgets = {'id': forms.HiddenInput()}
