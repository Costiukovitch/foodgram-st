from rest_framework.pagination import PageNumberPagination

from utils.constants import PAGE_SIZE


class CustomPagination(PageNumberPagination):
    """
    Кастомная пагинация с поддержкой параметра `limit`.
    
    Позволяет клиенту указывать размер страницы через параметр запроса limit,
    с ограничением до `max_page_size`. Номер страницы задается через page.
    """

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        Переопределение ответа для включения метаданных пагинации.
        """
        return super().get_paginated_response(data)