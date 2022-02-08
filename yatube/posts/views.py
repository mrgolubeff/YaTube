from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.base import TemplateView

from yatube.settings import POSTS_BY_PAGE

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import paginator_func


class PostCreatedView(TemplateView):
    template_name = 'posts/post_created.html'


def author_required(func):
    @wraps(func)
    def is_author(request, post_id, *args, **kwargs):
        post = get_object_or_404(Post, pk=post_id)
        if post.author.id == request.user.id:
            return func(request, post_id, *args, **kwargs)
        return redirect('posts:post_detail', post_id=post_id)
    return is_author


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_func(request, post_list, POSTS_BY_PAGE)

    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = group.posts.all()
    page_obj = paginator_func(request, post_list, POSTS_BY_PAGE)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    post_list = user_profile.posts.all()
    page_obj = paginator_func(request, post_list, POSTS_BY_PAGE)

    post_count = user_profile.posts.count()

    context = {
        'user_profile': user_profile,
        'page_obj': page_obj,
        'post_count': post_count,
    }

    if request.user.is_authenticated and user_profile is not request.user:
        following = Follow.objects.filter(
            user=request.user,
            author=user_profile
        ).exists()
        context['following'] = following
    else:
        context['following'] = None

    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_count = post.author.posts.count()
    post_preview = post.__str__()
    comments = Comment.objects.filter(post=post)

    if request.user.id == post.author.id:
        is_author = True
    else:
        is_author = False

    form = CommentForm(
        # request.POST or None
    )

    context = {
        'post': post,
        'post_count': post_count,
        'post_preview': post_preview,
        'is_author': is_author,
        'form': form,
        'comments': comments,
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    elif form.is_bound:
        return render(request, template, {'form': form})
    else:
        form = PostForm()
        context = {
            'form': form
        }
        return render(request, template, context)


@author_required
@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'

    post = get_object_or_404(Post, pk=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    elif form.is_bound:
        return render(request, template, {'form': form})
    else:
        context = {
            'form': form,
            'is_edit': True,
            'post': post
        }

        return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    )

    page_obj = paginator_func(request, post_list, POSTS_BY_PAGE)

    context = {
        'page_obj': page_obj,
    }
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)

    if (
        request.user != following
        and not Follow.objects.filter(
            user=request.user, author=following
        ).exists()
    ):
        Follow.objects.create(user=request.user, author=following)
        return redirect('posts:profile', username=following.username)
    else:
        return redirect('posts:index')


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)

    if (
        request.user != following
        and Follow.objects.filter(
            user=request.user, author=following
        ).exists()
    ):
        Follow.objects.filter(user=request.user, author=following).delete()
        return redirect('posts:profile', username=following.username)
    else:
        return redirect('posts:index')
