from django.core.paginator import Paginator

from yatube.settings import SAMPLING


def get_paginator(posts, request):
    paginator = Paginator(posts, SAMPLING)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
