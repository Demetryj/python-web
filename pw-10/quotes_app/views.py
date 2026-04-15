from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Quote, Author

PER_PAGE = 10


# Create your views here.
def main(request):
    quote_list = Quote.objects.all().order_by("id")
    paginator = Paginator(quote_list, PER_PAGE)  # Show PER_PAGE contacts per page.

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "quotes_app/main.html", {"page_obj": page_obj})


def about_author(request, author_id):
    author_obj = get_object_or_404(Author, id=author_id)
    return render(request, "quotes_app/author.html", {"author_obj": author_obj})