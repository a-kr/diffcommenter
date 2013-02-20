# coding: utf-8

from django.shortcuts import render

def index(request):
    c = {
    }
    return render(request, "index.html", c)
