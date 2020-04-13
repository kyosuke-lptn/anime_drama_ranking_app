from django.db import models

# Create your models here.


class Content(models.Model):
    content_name = models.CharField('作品名', max_length=50, unique=True,
                                    db_index=True)
    description = models.CharField('詳細説明', max_length=500)
    release_date = models.DateTimeField('リリース日', db_index=True)
    maker = models.CharField('作り手', max_length=50, db_index=True)
    tweets_total = models.PositiveIntegerField('ツイート総数', null=True,
                                               blank=True)
    aggregation_start_date = models.DateTimeField('集計開始日', null=True,
                                                  blank=True)
    update_date = models.DateTimeField('更新日', auto_now=True)

    def __str__(self):
        return self.content_name


class Category(models.Model):
    category_name = models.CharField('カテゴリー名', max_length=20, unique=True)
    content = models.ManyToManyField(Content, verbose_name='作品名')

    def __str__(self):
        return self.category_name


class TwitterData(models.Model):
    tweets_count = models.PositiveIntegerField('ツイート数', default=0)
    aggregation_period = models.DateTimeField('集計日')
    content = models.ForeignKey(Content, on_delete=models.CASCADE,
                                verbose_name='作品名')
    create_date = models.DateTimeField('作成日', auto_now_add=True)
    update_date = models.DateTimeField('更新日', auto_now=True)
