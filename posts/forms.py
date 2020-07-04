from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {
            'group': ("Группа"),
            'text': ("Текст записи"),
            'image': ("Изображение"),
        }
        help_texts = {
            'group': ("Выберите группу, в которой будет размещена Ваша запись (необязательно):"),
            'text': ("Введите текст Вашей записи:"),
            'image': ("Загрузите Ваше изображение (если, конечно, хотите):"),
        }
    
    def clean_post(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError("Вы что-то хотели сказать?")

        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        # labels = {
        #     'text': ("Текст комментария"),
        # }
        # help_texts = {
        #     'text': ("Введите текст Вашего комментария:"),
        # }
    
    def clean_comment(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError("Вы что-то хотели сказать?")

        return data