from .models import Category


def common(request):
    categories = Category.objects.all()
    return {"categories": categories}
