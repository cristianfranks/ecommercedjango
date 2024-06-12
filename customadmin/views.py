from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from store.models import Product, ReviewRating, ProductGallery, Account, Variation
from category.models import Category
from .forms import ProductForm, ProductGalleryForm, VariationForm
from orders.models import Order, OrderProduct, Payment
from accounts.models import Account
from django.contrib import auth, messages
from .decorators import admin_required
from django.core.serializers import serialize
from django.db.models import Sum, Count, Avg, Q
import openpyxl
from django.http import HttpResponse
from orders.models import Order
from django.views.decorators.http import require_POST
# Create your views here.

def admin_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None and user.is_staff:
            auth.login(request, user)

            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('admin_productos')
        else:
            messages.error(request, 'Las credenciales son incorrectas')
            return redirect('admin_login')

    return render(request, 'login.html')

@admin_required
def admin_productos(request):
    query = request.GET.get('search')
    if query:
        products = Product.objects.filter(Q(id__icontains=query) | Q(product_name__icontains=query)).order_by('id')
    else:
        products = Product.objects.order_by('id')
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    paged_products = paginator.get_page(page_number)
    context = {
        'products': paged_products,
        'search_query': query,
    }
    return render(request, 'productos.html', context)

def product_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        if product_form.is_valid():
            product = product_form.save()
            variations = request.POST.getlist('variations')
            for variation in variations:
                category, value, is_active = variation.split(':')
                Variation.objects.create(
                    product=product,
                    variation_category=category,
                    variation_value=value,
                    is_active=is_active == 'true'
                )
            images = request.FILES.getlist('gallery_images')
            for image in images:
                ProductGallery.objects.create(product=product, image=image)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': product_form.errors.as_json()})
    else:
        product_form = ProductForm()
        gallery_form = ProductGalleryForm()
        variation_form = VariationForm()

    context =  {
        'form' : product_form,
        'gallery_form': gallery_form,
        'variation_form': variation_form,
        'categories': categories
    }

    return render(request, 'product_form.html', context)

def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product_gallery = ProductGallery.objects.filter(product_id=product.id)
    categories = Category.objects.all()
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES, instance=product)
        if product_form.is_valid():
            product = product_form.save()
            product.variation_set.all().delete()
            variations = request.POST.getlist('variations')
            for variation in variations:
                category, value, is_active = variation.split(':')
                Variation.objects.create(
                    product=product,
                    variation_category=category,
                    variation_value=value,
                    is_active=is_active == 'true'
                )
            images = request.FILES.getlist('gallery_images')
            for image in images:
                ProductGallery.objects.create(product=product, image=image)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': product_form.errors.as_json()})
    else:
        product_form = ProductForm(instance=product)
        gallery_form = ProductGalleryForm()
        variation_form = VariationForm()
        existing_variations = product.variation_set.all()

    context =  {
        'form' : product_form,
        'categories': categories,
        'gallery_form': gallery_form,
        'variation_form': variation_form,
        'existing_variations': serialize('json', existing_variations),
        'product_gallery': product_gallery
    }

    return render(request, 'product_form.html', context)

def product_delete(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Petición inválida'})

@admin_required
def admin_orders(request):
    status = request.GET.get('status')
    search_query = request.GET.get('search')
    orders = Order.objects.all()

    if status in ['New', 'Completed']:
        orders = orders.filter(status=status)

    if search_query:
        orders = orders.filter(Q(order_number__icontains=search_query) | Q(email__icontains=search_query))

    orders = orders.order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    paged_orders = paginator.get_page(page_number)

    context = {
        'orders': paged_orders,
        'status': status,
        'search_query': search_query,
    }
    return render(request, 'ordenes.html', context)

def complete_order(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = "Completed"
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Petición inválida'})

@admin_required
def download_orders_excel(request):
    status = request.GET.get('status')
    orders = Order.objects.all().order_by('-created_at')  # Ordenar por fecha de creación en orden descendente

    if status in ['New', 'Completed']:
        orders = orders.filter(status=status).order_by('-created_at')  # Mantener el mismo orden al filtrar

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Orders'

    # Add the headers
    headers = [
        'Número de orden', 'Nombre', 'Teléfono', 'E-mail', 'Ciudad',
        'Total', 'Impuestos', 'Estado', 'Pagado'
    ]
    ws.append(headers)

    # Add the order data
    for order in orders:
        ws.append([
            order.order_number,
            order.first_name,
            order.phone,
            order.email,
            order.city,
            order.order_total,
            order.tax,
            order.get_status_display(),
            'Sí' if order.is_ordered else 'No'
        ])

    # Prepare the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ordenes.xlsx'
    wb.save(response)  # Save the workbook directly to the response

    return response

@admin_required
def view_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order_id=order.id)
    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price
    context = {
        'order': order,
        'order_products': order_products,
    }
    return render(request, 'view_order.html', context)


def product_gallery_delete(request, pk):
    if request.method == 'POST':
        product_gallery = get_object_or_404(ProductGallery, pk=pk)
        product_gallery.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Petición inválida'})

@admin_required
def admin_logout(request):
    auth.logout(request)
    messages.success(request, 'Sesión cerrada')
    return redirect('admin_login')

@admin_required
def dashboard(request):
    most_ordered_products = OrderProduct.objects.values('product__product_name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:5]
    users_with_most_orders = Order.objects.values('user__first_name', 'user__last_name').annotate(order_count=Count('id')).order_by('-order_count')[:5]
    best_rated_products = ReviewRating.objects.values('product__product_name').annotate(average_rating=Avg('rating')).order_by('-average_rating')[:5]
    total_users = Account.objects.count()
    total_orders = Order.objects.count()
    new_orders = Order.objects.filter(status='New').count()
    orders_total_amount = Payment.objects.filter(status='COMPLETED').aggregate(total_amount=Sum('amount_id'))

    context = {
        'most_ordered_products': list(most_ordered_products),
        'users_with_most_orders': list(users_with_most_orders),
        'best_rated_products': list(best_rated_products),
        'total_users': total_users,
        'orders_total_amount': orders_total_amount['total_amount'],
        'total_orders': total_orders,
        'new_orders': new_orders,
    }
    return render(request, 'dashboard.html', context)
