from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone

from .models import Category, Product, Tag
from .utils import cutoff_label, countdown_text, next_cutoff

FEATURED_COLLECTIONS = [
    ("premium-meat-game", "hero-medallions.png"),
    ("premium-seafood", "king-salmon-fillet-ora-king-nz-500g.webp"),
]


def home(request):
    now = timezone.localtime()
    cutoff = next_cutoff(now)

    collections = []
    for slug, image in FEATURED_COLLECTIONS:
        category = Category.objects.filter(slug=slug).first()
        if category:
            collections.append(
                {"category": category, "image_url": static(f"store/assets/{image}")}
            )

    context = {
        "popular_products": Product.objects.filter(is_active=True, is_popular=True)[:3],
        "collections": collections,
        "cutoff_label": cutoff_label(cutoff),
        "cutoff_ms": int(cutoff.timestamp() * 1000),
        "countdown_text": countdown_text(cutoff, now),
    }
    return render(request, "store/home.html", context)


def catalog(request):
    q = request.GET.get("q", "").strip()
    active_cat = request.GET.get("cat", "").strip()
    active_tag = request.GET.get("tag", "").strip()

    categories = list(Category.objects.all())
    base_qs = Product.objects.filter(is_active=True).select_related("category")
    if q:
        base_qs = base_qs.filter(name__icontains=q)
    if active_cat:
        base_qs = base_qs.filter(category__slug=active_cat)

    tag_groups = []
    seen_groups = {}
    for tag in Tag.objects.filter(products__in=base_qs).distinct():
        group_name = tag.group or "Filter"
        if group_name not in seen_groups:
            seen_groups[group_name] = {"name": group_name, "tags": []}
            tag_groups.append(seen_groups[group_name])
        seen_groups[group_name]["tags"].append(tag)

    products = base_qs
    if active_tag:
        products = products.filter(tags__slug=active_tag)
    products = list(products.prefetch_related("tags").distinct())

    sections = []
    for category in categories:
        if active_cat and category.slug != active_cat:
            continue
        items = [p for p in products if p.category_id == category.id]
        if items:
            sections.append(
                {
                    "category": category,
                    "products": items,
                    "number": f"{len(sections) + 1:02d}",
                }
            )

    context = {
        "q": q,
        "active_cat": active_cat,
        "active_tag": active_tag,
        "categories": categories,
        "tag_groups": tag_groups,
        "sections": sections,
        "result_count": len(products),
        "active_nav": "catalog",
    }
    return render(request, "store/catalog.html", context)


def _placeholder(request, title, active_nav="none"):
    return render(
        request,
        "store/placeholder.html",
        {"page_title": title, "active_nav": active_nav},
    )


def product_detail(request, slug):
    return _placeholder(request, "Product")


def cart(request):
    return _placeholder(request, "Cart", active_nav="cart")


def my_orders(request):
    return _placeholder(request, "My Orders", active_nav="orders")


def account(request):
    return _placeholder(request, "Account")
