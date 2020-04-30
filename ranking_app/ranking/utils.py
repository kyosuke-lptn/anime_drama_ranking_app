from django.core.paginator import Paginator


def paging(request, objs, display_number):
    """
    インスタンス集合であるobjsをページングに対応させる
    :param request:
    :param objs: インスタンスの集合
    :param display_number: １ページ当たりの表示数
    :return:
    """
    paginator = Paginator(objs, display_number)
    p = request.GET.get('p')
    return paginator.get_page(p)
