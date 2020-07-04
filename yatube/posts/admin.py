from django.contrib import admin

# Register your models here.
from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "__empty__"


class GroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug", "description")
    search_fields = ("description",)
    list_filter = ("title",)
    empty_value_display = "-пусто-"

admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
