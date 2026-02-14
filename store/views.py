from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Profile, Cart, Order, OrderItem
from .forms import SignupForm, LoginForm

def home(request):
    # 1. Get all active products (for general listing if needed)
    products = Product.objects.filter(is_active=True)
    
    # 2. Get Trending (For the Top Slider)
    trending = Product.objects.filter(is_trending=True, is_active=True)[:10]
    
    # 3. GET THE SPECIAL SECTIONS (Crucial for your specific request)
    signature_items = Product.objects.filter(is_signature=True, is_active=True)
    gift_packages = Product.objects.filter(is_gift_package=True, is_active=True)
    weekly_offers = Product.objects.filter(is_weekly_offer=True, is_active=True)
    monthly_offers = Product.objects.filter(is_monthly_offer=True, is_active=True)
    
    # 4. Get All Categories (For the bottom sections)
    all_categories = Category.objects.all()

    # 5. Send everything to the template
    return render(request, 'home.html', {
        'products': products,
        'trending': trending,
        'signature_items': signature_items,
        'gift_packages': gift_packages,
        'weekly_offers': weekly_offers,
        'monthly_offers': monthly_offers,
        'all_categories': all_categories,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

# --- AUTHENTICATION ---

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # Create Profile (Phone/Address)
            Profile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            login(request, user) # Log them in immediately
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# --- CART SYSTEM ---

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id)
    if cart_item.user == request.user: # Security check
        cart_item.delete()
    return redirect('cart')

@login_required
def update_cart(request, cart_id, action):
    cart_item = get_object_or_404(Cart, id=cart_id)
    
    if cart_item.user != request.user:
        return redirect('cart') # Security check

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity > 0:
            cart_item.save()
        else:
            cart_item.delete() # Remove if quantity becomes 0
            
    return redirect('cart')

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.total_cost for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

# --- CHECKOUT & ORDERS ---

# ... keep your existing imports ...

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('home')

    total_price = sum(item.total_cost for item in cart_items)
    
    # Get or Create Profile (With EMPTY defaults now)
    user_profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'phone': '', 'address': ''}
    )

    # AUTO-FIX: If database already has "No Phone", clear it for the user
    if user_profile.phone == "No Phone":
        user_profile.phone = ""
    if user_profile.address == "No Address":
        user_profile.address = ""

    if request.method == 'POST':
        # 1. Create Order
        new_order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name', request.user.username),
            phone=request.POST.get('phone', user_profile.phone),
            address=request.POST.get('address', user_profile.address),
            total_amount=total_price
        )

        # 2. Save these details to Profile for next time (Auto-Save)
        user_profile.phone = new_order.phone
        user_profile.address = new_order.address
        user_profile.save()

        # 3. Move Cart to Order Items
        for item in cart_items:
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
        cart_items.delete()
        return redirect('order_success', order_id=new_order.order_id)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'profile': user_profile
    })

# --- NEW FUNCTION FOR PROFILE POPUP ---
@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)

        # Update User Model (First/Last Name)
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()

        # Update Profile Model (Phone/Address)
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        profile.save()

        return redirect(request.META.get('HTTP_REFERER', 'home')) # Go back to same page
    return redirect('home')
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})