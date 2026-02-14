from .models import Cart, Category

def website_content(request):
    # 1. Cart Count Logic
    count = 0
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            count += item.quantity
            
    # 2. Categories Logic (For the Dropdown)
    categories = Category.objects.all()
    
    return {'cart_count': count, 'categories': categories}