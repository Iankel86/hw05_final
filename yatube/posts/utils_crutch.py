from yatube.settings import SAMPLING
from django.core.paginator import Paginator


def get_paginator_crutch(queryset, request):
    paginator = Paginator(queryset, SAMPLING)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
