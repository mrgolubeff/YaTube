from http import HTTPStatus as hs

from django.shortcuts import render


def page_not_found(request, exception):
    return render(
        request,
        'core/404.html',
        {'path': request.path},
        status=hs.NOT_FOUND.value
    )


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')


def server_error(request):
    return render(
        request,
        'core/500.html',
        status=hs.INTERNAL_SERVER_ERROR.value
    )
