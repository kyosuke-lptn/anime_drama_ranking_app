from django.contrib import admin
from django.urls import path
from django.shortcuts import render

from .models import Content
from .models import Category
from .models import TwitterUser
from .models import TwitterApi
from .models import ScrapingContent
from .models import Staff

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
               f"【ツイート合計】{user.all_tweet_count:,}" \
               f"【フォロワー数】{user.followers_count:,}"

    get_tw_user_data.short_description = 'ツイッター情報'

    def latest_tweet_date(self, obj):
        return obj.twitteruser.latest_tweet().tweet_date.strftime(
            '%Y年%m月%d日%H:%M')

    latest_tweet_date.short_description = '最新ツイート日'

    def latest_tweet_text(self, obj):
        return obj.twitteruser.latest_tweet().text

    latest_tweet_text.short_description = '最新のツイート内容'

    def latest_tweet_create_date(self, obj):
        create_datetime = obj.twitteruser.latest_tweet().\
            latest_tweet_count().create_date
        return create_datetime.strftime('%Y年%m月%d日%H:%M')

    latest_tweet_create_date.short_description = '以前データ取得した日'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        api = TwitterApi()
        if obj.has_tweets():
            api.update_data(obj)
        else:
            api.get_and_store_twitter_data(obj)

    def get_urls(self):
        urls = super().get_urls()
        add_urls = [
            path('auto_creation/',
                 self.admin_site.admin_view(self.auto_creation_view),
                 name="auto_creation"),
            path('do_auto_creation/',
                 self.admin_site.admin_view(self.do_auto_creation_view),
                 name="do_auto_creation"),
        ]
        return add_urls + urls

    def auto_creation_view(self, request):
        context = None
        return render(request, 'admin/ranking/content/auto_create.html',
                      context)

    def do_auto_creation_view(self, request):
        # 処理が失敗したときのエラー表示をかく
        content_getter = ScrapingContent().get_anime_data()
        api = TwitterApi()
        for content in content_getter.contents:
            api.get_and_store_twitter_data(content)
        context = {'contents_data': content_getter.contents_data,
                   'default_data_list': content_getter.default_data_list}
        return render(request, 'admin/ranking/content/result.html', context)


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

    get_contents.short_description = 'コンテンツ'



