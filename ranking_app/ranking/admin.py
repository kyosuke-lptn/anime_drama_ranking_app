from django.contrib import admin
#
from .models import Content, Category, TwitterUser, TwitterApi, Staff

# Register your models here.


class TwitterUserInline(admin.StackedInline):
    model = TwitterUser
    extra = 0
    readonly_fields = ('name', 'description', 'official_url',
                       'icon_url', 'banner_url', 'followers_count',
                       'create_date', 'update_date')


class StaffInline(admin.StackedInline):
    model = Staff
    extra = 0


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('name', 'update_date', 'twitteruser', 'get_tw_user_data')
    fieldsets = [
        (None, {'fields': ['name', 'screen_name', 'description',
                           ('maker', 'img_url'), ('release_date', 'update_date')]}),
        ('カテゴリー', {'fields': ['category']}),
        ('最新ツイート', {'fields': ['latest_tweet_text', 'latest_tweet_date',
                               'latest_tweet_create_date']})]
    readonly_fields = ('update_date', 'latest_tweet_text', 'latest_tweet_date',
                       'latest_tweet_create_date')
    inlines = [StaffInline, TwitterUserInline]

    def get_tw_user_data(self, obj):
        user = obj.twitteruser
        return f"【いいね平均】{user.favorite_avg():,}" \
               f"【リツイート平均】{user.retweets_avg():,}" \
               f"【ツイート合計】{user.all_tweet_count():,}" \
               f"【フォロワー数】{user.followers_count:,}"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        api = TwitterApi()
        if obj.has_tweets():
            api.update_data(obj)
        else:
            api.get_and_store_twitter_data(obj)

    def latest_tweet_date(self, obj):
        return obj.twitteruser.latest_tweet().tweet_date.strftime(
            '%Y年%m月%d日%H:%M')

    def latest_tweet_text(self, obj):
        return obj.twitteruser.latest_tweet().text

    def latest_tweet_create_date(self, obj):
        return obj.twitteruser.latest_tweet().create_date.strftime(
            '%Y年%m月%d日%H:%M')


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



