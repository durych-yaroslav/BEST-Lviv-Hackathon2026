from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'size'
    page_query_param = 'page'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('items', data),
            ('total', self.page.paginator.count),
            ('page', self.page.number),
            ('size', len(data)),
        ]))
