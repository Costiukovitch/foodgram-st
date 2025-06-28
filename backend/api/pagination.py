from rest_framework.pagination import PageNumberPagination

from utils.constants import PAGE_SIZE


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
    max_page_size = 100
    page_query_param = 'page'
