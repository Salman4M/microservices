from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    General purpose pagination with default page size 10.
    Allows client to override page size up to max_page_size.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

