from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .models import Quote, Author, Tag
from .forms import AuthorForm, QuoteForm

PER_PAGE = 10


# Create your views here.
def main(request):
    """Render the main page with paginated quotes."""
    quote_list = Quote.objects.all().order_by("id")
    paginator = Paginator(quote_list, PER_PAGE)  # Show PER_PAGE contacts per page.

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "quotes_app/main.html", {"page_obj": page_obj})


def about_author(request, author_id):
    """Render details page for a single author."""
    author_obj = get_object_or_404(Author, id=author_id)
    return render(request, "quotes_app/author.html", {"author_obj": author_obj})


@login_required
def add_author(request):
    """Handle creation of a new author via AuthorForm."""
    if request.method == "POST":
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to='quotes_app:main')
        else:
            return render(request, 'quotes_app/add_author.html', {'form': form})
        
    return render(request, "quotes_app/add_author.html", {'form': AuthorForm()})


@login_required
def add_quote(request):
    """Handle creation of a new quote with author and tags."""
    if request.method == "POST":
        form = QuoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("quotes_app:main")
    else:
        form = QuoteForm()

    return render(request, "quotes_app/add-quote.html", {"form": form})


def show_quotes_by_tag(request, tag_id):
    """Render paginated quotes filtered by a specific tag."""
    tag_obj = get_object_or_404(Tag, id=tag_id)
    quotes = Quote.objects.filter(tags=tag_obj).order_by("id")
    
    page_number = request.GET.get("page")
    paginator = Paginator(quotes, PER_PAGE)  # Show PER_PAGE contacts per page.
    quotes_obj = paginator.get_page(page_number)
    
    return render(
        request,
        "quotes_app/quotes_by_tag.html",
        {"tag_obj": tag_obj, "quotes_obj": quotes_obj},
    )

    
