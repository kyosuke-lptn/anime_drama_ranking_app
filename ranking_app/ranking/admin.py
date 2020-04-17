from django.contrib import admin

from .models import Content, Category, TwitterData

# Register your models here.


class TwitterDataInline(admin.StackedInline):
    model = TwitterData
    extra = 0
    readonly_fields = ('tw_screen_name', 'tw_description', 'content_url',
                       'profile_image_url_https', 'profile_banner_url',
                       )


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('content_name', 'get_data')
    fieldsets = [
        (None, {'fields': ['content_name', 'description',
                           'maker', 'release_date', 'update_date']}),
         ('ツイッター集計結果(1ツイートあたり）', {'fields': ['get_data']}),
    ]
    readonly_fields = ('get_data', 'update_date')
    inlines = [TwitterDataInline]

    def get_data(self, obj):
        data_list = [
            "{} -【いいね】 {}  【リツイート】 {} 【リスト数】{} 【フォロワー数】{} 【ツイート数】{}".format(
                create_date, data[0], data[1], data[2], data[3], data[4])
            for (create_date, data) in obj.data().items()
        ]
        return "\n".join(data_list)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    filter_horizontal = ['contents']
    list_display = ('category_name', 'get_contents')

    def get_contents(self, obj):
        if obj.contents.all().exists():
            return ", ".join(
                [content.content_name for content in obj.contents.all()])
        else:
            return '該当なし'
