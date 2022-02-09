from functools import wraps

from django.shortcuts import get_object_or_404, redirect

from .models import Post


def author_required(func):
    @wraps(func)
    def is_author(request, post_id, *args, **kwargs):
        post = get_object_or_404(Post, pk=post_id)
        if post.author.id == request.user.id:
            return func(request, post_id, *args, **kwargs)
        return redirect('posts:post_detail', post_id=post_id)
    return is_author
