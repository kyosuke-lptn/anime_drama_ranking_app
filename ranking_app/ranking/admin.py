from django.contrib import admin
#
from .models import Content, Category, TwitterUser, TwitterApi

# Register your models here.


class TwitterUserInline(admin.StackedInline):
    model = TwitterUser
    extra = 0
    readonly_fields = ('name', 'description', 'official_url',
                       'icon_url', 'banner_url', 'followers_count',
                       'all_tweet_count', 'all_retweet_count',
                       'all_favorite_count', 'create_date', 'update_date')


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('name', 'update_date', 'twitteruser', 'get_tw_user_data')
    fieldsets = [
        (None, {'fields': ['name', 'screen_name', 'description',
                           ('maker', 'release_date', 'update_date')]}),
        ('カテゴリー', {'fields': ['category']})]
    readonly_fields = ('update_date', )
    inlines = [TwitterUserInline]

    def get_tw_user_data(self, obj):
        user = obj.twitteruser
        return f"【いいね合計】{user.all_favorite_count:,}" \
               f"【リツイート合計】{user.all_retweet_count:,}" \
               f"【ツイート合計】{user.all_tweet_count:,}" \
               f"【フォロワー数】{user.followers_count:,}"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        api = TwitterApi()
        api.get_and_store_twitter_data(obj.screen_name)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_contents')
    fields = ('name', 'get_contents')
    readonly_fields = ('get_contents', )

    def get_contents(self, obj):
        if obj.content_set.all().exists():
            return ", ".join(
                [content.name for content in obj.content_set.all()])
        else:
            return '該当なし'
