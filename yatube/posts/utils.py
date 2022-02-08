from django.core.paginator import Paginator


def paginator_func(request, post_list, posts_by_page):
    paginator = Paginator(post_list, posts_by_page)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return page_obj
