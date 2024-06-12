from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery, Account
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from django.http import HttpResponse

from sklearn.neighbors import NearestNeighbors
import numpy as np


# k = numero de resultados
def recommend_products_knn(user_name, knn_model, ratings_matrix, user_index_map, product_index_map, num_users, productos, excluded_products=None, category=None, k=3):
    if k <= 1:
        print("k deberia ser mayor a 1 para las recomendaciones")
        return []

    if user_name is None:
        top_products = []
        product_ratings = np.mean(ratings_matrix, axis=0)
        sorted_product_indices = np.argsort(product_ratings)[::-1]
        for product_index in sorted_product_indices:
            product_name = list(product_index_map.keys())[list(product_index_map.values()).index(product_index)]
            product = productos[product_name]
            if excluded_products and product in excluded_products:
                continue
            top_products.append(product)
            if len(top_products) == k:
                break
        return top_products

    user_index = user_index_map[user_name]

    # encontrar los k-neighbors del usuario
    distances, neighbor_indices = knn_model.kneighbors([ratings_matrix[user_index]], n_neighbors=min(k, num_users))
    neighbor_indices = neighbor_indices[0]  # Extract neighbor indices

    # encontrar los productos no calificados por el usuario pero si por los usuarios similares
    unrated_products = np.where(ratings_matrix[user_index] == 0)[0]
    recommendations = []
    for product_index in unrated_products:
        product_name = list(product_index_map.keys())[list(product_index_map.values()).index(product_index)]
        product = productos[product_name]
        if excluded_products and product in excluded_products:
            continue
        if category and product.category != category:
            continue
        if ratings_matrix[neighbor_indices, product_index].any():  # Verificar si algun usuario similar ha calificado
            product_name = list(product_index_map.keys())[list(product_index_map.values()).index(product_index)]
            recommendations.append(productos[product_name])  # Agregar data
    return recommendations[:k] 

# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True).order_by('id')
        paginator = Paginator(products, 9)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 9)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    context =  {
        'products' : paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None


    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
 
    allUsers = Account.objects.all()
    allProducts = Product.objects.all()
    allReviews = ReviewRating.objects.all()

    usuarios = {user.email for user in allUsers}
    productos = {product.product_name: product for product in allProducts}
    calificaciones = {(review.user.email, review.product.product_name): review.rating for review in allReviews}
        
    # Inicio / obtener el numero de usuarios y productos
    num_users = len(usuarios)
    num_products = len(productos)

    # Matriz de usuarios en filas y productos en columnas
    ratings_matrix = np.zeros((num_users, num_products)) #iniciar matriz de ceros con la funcion zeros de la libreria numpy
    user_index_map = {user: i for i, user in enumerate(usuarios)}
    product_index_map = {product: i for i, product in enumerate(productos)}

    for (user, product), rating in calificaciones.items():
        user_index = user_index_map[user]
        product_index = product_index_map[product]
        ratings_matrix[user_index, product_index] = rating

    # knn
    k = min(3, num_users)  # Numero de nn 
    if k <= 1:
        print("No hay suficientes usuarios para ejecutar el algoritmo.")
    else:
        knn_model = NearestNeighbors(n_neighbors=k, metric='cosine') #inicializacion del modelo knn de la libreria scikit
        knn_model.fit(ratings_matrix)

    # 
    user_name = request.user.email if request.user.is_authenticated else None
    recommended_products = recommend_products_knn(user_name, knn_model, ratings_matrix, user_index_map, product_index_map, num_users, productos, excluded_products=[single_product], category=category)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'recomendaciones': recommended_products,
        'user_name': user_name
    }

    return render(request, 'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Muchas gracias!, tu comentario ha sido actualizado')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Muchas gracias, tu comentario fue enviado con exito!')
                return redirect(url)
