# Страница - Новой записи
from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["text", "group", 'image']
        help_texts = {
            "text": "Прописываем текст поста",
            "group": "Группа для опубликования"}
        labels = {
            "text": "Текст поста",
            "group": "Группа"}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
