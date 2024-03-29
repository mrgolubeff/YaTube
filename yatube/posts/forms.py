from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }

        labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

        labels = {
            'text': 'Комментарий'
        }
