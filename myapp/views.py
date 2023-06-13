import time
import pyttsx3 # for Windows
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, auth
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
from decimal import Decimal
from django.db.models import F, Count, Avg
from django.utils import timezone
from django.contrib import messages
from django.utils.safestring import mark_safe
from .models import Contact, Product, Review, Cart, Customer, OrderPlaced, Favorite
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import get_user_model
import secrets
import hashlib
import hmac
import stripe
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage

# Create your views here.
engine = pyttsx3.init()

def index(request):
    products = Product.objects.all()

    # Paginate trendyproducts
    trendyproducts = products.annotate(
        order_count=Count('orderplaced')).order_by('-order_count')
    trendy_paginator = Paginator(trendyproducts, 4)
    trendy_page_number = request.GET.get('trendy_page', 1)
    trendy_page_number = int(trendy_page_number)
    trendyproducts = trendy_paginator.get_page(trendy_page_number)

    # Paginate latestproducts
    latestproducts = products.order_by('productcreated_at')
    latest_paginator = Paginator(latestproducts, 4)
    latest_page_number = request.GET.get('latest_page', 1)
    latest_page_number = int(latest_page_number)
    latestproducts = latest_paginator.get_page(latest_page_number)

    # Get product category counts
    men = Product.objects.filter(category='md').count()
    women = Product.objects.filter(category='wd').count()
    baby = Product.objects.filter(category='bd').count()

    # Get cart product count
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity

    # Get favorite product count
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()

    # Update pagination URLs based on latest or trendy pagination
    trendy_pagination_url = f'?trendy_page={trendy_page_number}&latest={request.GET.get("latest", "false")}'
    latest_pagination_url = f'?latest_page={latest_page_number}&latest={request.GET.get("latest", "false")}'

    return render(request, 'index.html', {
        'trendyproducts': trendyproducts,
        'latestproducts': latestproducts,
        'product_count': product_count,
        'favorite_count': favorite_count,
        'men': men,
        'women': women,
        'baby': baby,
        'trendy_page_number': trendy_page_number,  # pass page number to template
        'latest_page_number': latest_page_number,  # pass page number to template
        'trendy_pagination_url': trendy_pagination_url,
        'latest_pagination_url': latest_pagination_url,
    })




def shop(request):
    # Fetch all the products
    products = Product.objects.all()

    # Initialize product_count to zero
    product_count = 0

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Get the cart items for the user
        cart_products = Cart.objects.filter(user=request.user)
        # Calculate the total quantity of products in the cart
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()

    # Check for the sort parameter in the request
    sort_param = request.GET.get('sort')

    # Apply sorting based on the selected option
    if sort_param == 'latest':
        products = products.order_by('productcreated_at')
    elif sort_param == 'popularity':
        products = products.annotate(order_count=Count(
            'orderplaced')).order_by('-order_count')
    elif sort_param == 'best_rating':
        products = products.annotate(average_rating=Avg(
            'reviews__rating')).order_by('-average_rating')

    # Pagination logic
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    page_number = int(page_number)
    products = paginator.get_page(page_number)

    # Search logic
    query = request.GET.get('q')
    results = []
    if query:
        results = Product.objects.filter(productname__icontains=query)
        paginator = Paginator(results, 6)
        page_number = request.GET.get('page', 1)
        page_number = int(page_number)
        results = paginator.get_page(page_number)

    # Render the template with the sorted products and other context data
    return render(request, 'shop.html', {'products': products, 'product_count': product_count, 'favorite_count': favorite_count, 'query': query, 'results': results})



def men(request):
    mendress = Product.objects.filter(category='md')
    for men in mendress:
        men = mendress.count()
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()

    # pagintion logic

    paginator = Paginator(mendress, 6)
    page_number = request.GET.get('page', 1)
    page_number = int(page_number)
    products = paginator.get_page(page_number)

    query = request.GET.get('q')
    results = []
    if query:
        results = Product.objects.filter(category="md", productname__icontains=query)
        paginator = Paginator(results, 6)
        page_number = request.GET.get('page', 1)
        page_number = int(page_number)
        results = paginator.get_page(page_number)
    return render(request, 'men.html', {'mendress': mendress, 'product_count': product_count, 'favorite_count': favorite_count, 'men': men, 'query':query, 'results':results, 'products':products})


def women(request):
    womendress = Product.objects.filter(category='wd')
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    
    # pagintion logic

    paginator = Paginator(womendress, 6)
    page_number = request.GET.get('page', 1)
    page_number = int(page_number)
    products = paginator.get_page(page_number)

    query = request.GET.get('q')
    resultss = []
    if query:
        resultss = Product.objects.filter(category='wd', productname__icontains=query)
        paginator = Paginator(resultss, 6)
        page_number = request.GET.get('page', 1)
        page_number = int(page_number)
        resultss = paginator.get_page(page_number)
    return render(request, 'women.html', {'womendress': womendress, 'product_count': product_count, 'favorite_count': favorite_count, 'query':query, 'resultss':resultss, 'products':products})


def baby(request):
    babydress = Product.objects.filter(category='bd')
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    
    # pagintion logic

    paginator = Paginator(babydress, 6)
    page_number = request.GET.get('page', 1)
    page_number = int(page_number)
    products = paginator.get_page(page_number)

    query = request.GET.get('q')
    resultsss = []
    if query:
        resultsss = Product.objects.filter(category='bd', productname__icontains=query)
        paginator = Paginator(resultsss, 6)
        page_number = request.GET.get('page', 1)
        page_number = int(page_number)
        resultsss = paginator.get_page(page_number)

    return render(request, 'baby.html', {'babydress': babydress, 'product_count': product_count, 'favorite_count': favorite_count, 'products':products, 'query':query, 'resultsss':resultsss})


def review(request, id):
    product = Product.objects.get(id=id)
    if request.method == 'POST':
        review = request.POST['review']
        reviewname = request.POST['reviewname']
        reviewemail = request.POST['reviewemail']
        stars = request.POST['stars']
        if request.user.is_authenticated:
            reviewss = Review(user=request.user, stars=stars, review=review,
                              name=reviewname, email=reviewemail, product=product)
        else:
            reviewss = Review(stars=stars, review=review,
                              name=reviewname, email=reviewemail, product=product)
        reviewss.save()
        # revieww = Review.objects.get(id=id)
        messages.success(request, 'Thanks For Your Review')
        return redirect('detail', id)


def update_review(request, id):
    review = Review.objects.get(id=id)
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    if review.email == request.user.email:
        if request.method == 'POST':
            review.stars = request.POST['stars']
            review.review = request.POST['review']
            review.name = request.POST['reviewname']
            review.email = request.POST['reviewemail']
            review.created_at = datetime.now()
            review.save()
            messages.success(
                request, 'Your review has been updated successfully!')
            return redirect('detail', id=review.product.id)
    return render(request, 'updatereview.html', {"review": review, 'product_count': product_count, 'favorite_count': favorite_count})


def delete_review(request, id):
    review = Review.objects.get(id=id)

    # check if the email of the user and reviewer is the same
    if review.email == request.user.email:
        review.delete()
        messages.success(request, 'Your review has been deleted successfully!')
        return redirect('detail', id=review.product.id)
    else:
        messages.error(request, 'You are not allowed to delete this review.')
        return redirect('detail', id=review.product.id)


def detail(request, id):
    products = Product.objects.get(id=id)
    review_count = Review.objects.filter(
        product=products).aggregate(count=Count('id'))['count']
    recents = Product.objects.filter(
        ~Q(id=id)).order_by('-productcreated_at')[:5]
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
        
    return render(request, 'detail.html', {'products': products, 'product_count': product_count, "recents": recents, 'review_count': review_count, 'favorite_count': favorite_count})


@login_required(login_url='/login')
def addtocart(request):
    user = request.user
    product_id = request.GET.get('prod-id')
    product = Product.objects.get(id=product_id)
    cart = Cart.objects.filter(product=product, user=user).first()

    if cart:
        cart.quantity += 1
        cart.save()
        messages.success(
            request, f'{product} quantity increased to {cart.quantity} in Cart')
    else:
        if user.is_anonymous:
            messages.warning(request, 'please Login First')
            return redirect('/login')
        else:
            messages.success(request, f'{product} added to Cart')
            Cart(user=user, product=product).save()

    return redirect('/cart')


@login_required(login_url='/login')
def showcart(request):
    user = request.user
    carts = Cart.objects.filter(user=user)
    for cart in carts:
        if cart.quantity > 3:
            cart.discount = True
            
            cart.save()
        elif cart.quantity <= 3:
            cart.discount = False
            cart.save()
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
        user = request.user
        carts = Cart.objects.filter(user=user)
        amount = 0
        shipping_amount = 10
        discount = 0
        total_amount = 0
        discount_message_displayed = False
        cart_product = [p for p in Cart.objects.all() if p.user ==
                        request.user]
        if cart_product:
            for p in cart_product:
                tempamount = (p.quantity * p.product.productprice)
                if p.discount:
                    discount = Decimal(tempamount) * Decimal('0.1')
                    tempamount = tempamount - discount
                    messages.success(
                        request, f'Congratulations! You got 10% discount on"{p.product.productname}" product')
                    engine = pyttsx3.init()
                    engine.say(f'Congratulations! You got 10% discount on"{p.product.productname}" product')
                    t = threading.Thread(target=engine.runAndWait)
                    t.start()
                    engine.endLoop()
                    engine = None  # reinitialize the engine object
            

                amount += tempamount
                total_amount = amount + shipping_amount
            return render(request, 'cart.html', {'carts': carts, 'amount': amount, 'totalamount': total_amount, 'shipping_amount': shipping_amount, 'tempamount': tempamount, 'discount': discount, 'product_count': product_count, 'favorite_count': favorite_count})
        else:
            return render(request, 'emptycart.html', {'product_count': product_count, 'favorite_count': favorite_count})


# def check_cart_discount(request):
#     user = request.user
#     carts = Cart.objects.filter(user=user)
#     for cart in carts:
#         if cart.quantity > 3:
#             cart.discount = True
#             cart.save()

def increase_quantity(request, product_id):
    cart_item = get_object_or_404(
        Cart, product_id=product_id, user=request.user)
    product = cart_item.product
    cart_item.quantity += 1
    cart_item.save()
    return redirect('/cart')


def decrease_quantity(request, product_id):
    cart_item = get_object_or_404(
        Cart, product_id=product_id, user=request.user)
    product = cart_item.product
    cart_item.quantity -= 1
    if cart_item.quantity == 0:
        cart_item.delete()
        messages.warning(request, 'Product is removed from Cart')
    else:
        cart_item.save()
    return redirect('/cart')


def delete(request, id):
    cart = Cart.objects.get(id=id)
    cart.delete()
    return redirect('/cart')


@login_required(login_url='/login')
def checkout(request):
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    cart_products = Cart.objects.filter(user=request.user)
    product_count = 0
    for cart_item in cart_products:
        product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    user = request.user
    address = Customer.objects.filter(user=user)
    cart_items = Cart.objects.filter(user=user)
    discount = 0
    amount = 0
    shipping_amount = 10
    total_amount = 0
    cart_product = [p for p in Cart.objects.all() if p.user == request.user]
    if cart_product:
        for p in cart_product:
            tempamount = (p.quantity * p.product.productprice)
            if p.discount:
                discount += Decimal(tempamount) * Decimal('0.1')
                tempamount = tempamount - Decimal(tempamount) * Decimal('0.1')
            amount += tempamount
            total_amount = amount + shipping_amount

        return render(request, 'checkout.html', {'cart_items': cart_items, 'amount': amount, 'shipping_amount': shipping_amount, 'total_amount': total_amount, 'address': address, 'product_count': product_count, 'favorite_count': favorite_count})
    else:
        return render(request, 'emptycheckout.html', {'product_count': product_count, 'favorite_count': favorite_count})


def profile(request):
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    cart_products = Cart.objects.filter(user=request.user)
    product_count = 0
    for cart_item in cart_products:
        product_count += cart_item.quantity
    user = request.user
    customer = Customer.objects.filter(user=user)
    return render(request, 'profile.html', {'customer': customer, 'product_count': product_count, 'favorite_count': favorite_count})


def customer(request):
    if request.method == 'POST':
        user = request.user
        name = request.POST['name']
        email = request.POST['email']
        locality = request.POST['locality']
        city = request.POST['city']
        state = request.POST['state']
        zipcode = request.POST['zipcode']

        # Perform validation on all fields
        if not name:
            messages.warning(request, 'Name is required')
            return redirect('profile')
        elif len(name) > 20:
            messages.warning(request, 'Name should not exceed 20 characters')
            return redirect('profile')

        if not email:
            messages.warning(request, 'Email is required')
            return redirect('profile')
        # You can perform further email validation if needed

        if not locality:
            messages.warning(request, 'Locality is required')
            return redirect('profile')

        if not city:
            messages.warning(request, 'City is required')
            return redirect('profile')

        if not state:
            messages.warning(request, 'State is required')
            return redirect('profile')

        if not zipcode:
            messages.warning(request, 'Zipcode is required')
            return redirect('profile')
        # You can perform further validation on the zipcode if needed

        customer = Customer(user=user, name=name, email=email,
                            locality=locality, city=city, state=state, zipcode=zipcode)
        customer.save()
        messages.success(request, 'Customer details saved successfully')
    return redirect('profile')


def delete_customer(request, id):
    user = request.user
    customer = Customer.objects.get(user=user, id=id)
    customer.delete()
    return redirect('/profile')


def update_customer(request, id):
    customer = Customer.objects.get(id=id)
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    if request.method == 'POST':
        customer.name = request.POST.get('updatename')
        customer.email = request.POST.get('updateemail')
        customer.locality = request.POST.get('updatelocality')
        customer.city = request.POST.get('updatecity')
        customer.state = request.POST.get('updatestate')
        customer.zipcode = request.POST.get('updatezipcode')
        customer.save()
        return redirect('/profile')
        messages.success(request, 'Your Account has been Updated')
    else:
        return render(request, 'updatecustomer.html', {'customer': customer, 'product_count': product_count, 'favorite_count': favorite_count})


def send_order_confirmation(request, email):
    subject = 'Order Confirmation'
    user = request.user
    custid = request.GET.get('custid')
    orderplaced = OrderPlaced.objects.filter(user=user)
    customers = Customer.objects.filter(user=user, id=custid)
    email_from = settings.EMAIL_HOST_USER

    for customer in customers:
        message = f'Thank you {customer.name} for your order.\n\nYour ordered products are:\n\n'
        for item in orderplaced:
            message += f'{item.product.productname} - Quantity: {item.quantity}\n'
        message += f'\n\nShipping Address:\n{customer.locality}\n{customer.city}\n'
        recipient_list = [customer.user.email]
        send_mail(subject, message, email_from, recipient_list)


def paymentdone(request):
    user = request.user
    custid = request.GET.get('custid')
    customer = Customer.objects.get(id=custid)
    cart = Cart.objects.filter(user=user)
    amount_str = request.GET.get('amount')
    stripe_token = request.GET.get('stripeToken')

    amount = int(float(amount_str) * 100)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        # Create a new charge object using the Stripe API
        charge = stripe.Charge.create(
            amount=amount,
            currency="usd",
            source=stripe_token,  # This is the token created by Stripe.js
            description="Order payment for customer {}".format(
                customer.user.username)
        )

        # If the payment is successful, create a new order and send the order confirmation email
        for c in cart:
            OrderPlaced(user=user, customer=customer,
                        product=c.product, quantity=c.quantity).save()
            c.delete()
            send_order_confirmation(request, request.user.email)
        messages.success(
            request, 'Congratulations! Your Order has been received. Check Your email')
        engine = pyttsx3.init()
        engine.say('Congratulations! Your Order has been received. Check Your email')
        t = threading.Thread(target=engine.runAndWait)
        t.start()
        engine.endLoop()
        engine = None  # reinitialize the engine object
        return redirect('/orders')
    except stripe.error.CardError as e:
        # The card has been declined
        body = e.json_body
        err = body.get('error', {})
        messages.error(request, f"{err.get('message')}")
        return redirect('checkout')
    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        messages.error(request, "Rate limit error")
        return redirect('checkout')
    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        messages.error(request, "Invalid request error")
        return redirect('checkout')
    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        messages.error(request, "Authentication error")
        return redirect('checkout')
    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        messages.error(request, "API connection error")
        return redirect('checkout')
    except stripe.error.StripeError as e:
        # Something else happened, completely unrelated to Stripe
        messages.error(request, "Payment error")
        return redirect('checkout')


def order(request):
    orders = OrderPlaced.objects.filter(user=request.user)
    product_count = 0
    favorite_count = 0

    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity

        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()

        for order in orders:
            if order.status == 'Delivered':
                time.sleep(30)
                order.delete()
                messages.success(
                    request, f'Congratulations! Your Order "{order.product}" has been delivered')
                engine = pyttsx3.init()
                engine.say(f'Congratulations! Your Order "{order.product}" has been delivered. Thanks {request.user.username}, for using our services')
                t = threading.Thread(target=engine.runAndWait)
                t.start()
                engine.endLoop()
                engine = None  # reinitialize the engine object

    if not orders.exists():
        return render(request, 'emptyorders.html', {'favorite_count': favorite_count, 'product_count': product_count})

    return render(request, 'orders.html', {'orders': orders, 'favorite_count': favorite_count, 'product_count': product_count})

# def send_contact_message(request, email):
#     subject = 'Thanks For Contacting Us'
#     user = request.user
#     contacts = Contact.objects.filter(email=user.email)
#     email_from = settings.EMAIL_HOST_USER

#     for contact in contacts:
#         message = f'Thank you {contact.name} for contacting us.\n Email:{contact.email}.\n Subject:{contact.subject}.\n Message:{contact.message}.'
#         recipient_list = [contact.email]
#         send_mail(subject, message, recipient_list, email_from)

def contact(request):
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']
        contact = Contact(name=name, email=email,
                          subject=subject, message=message)
        contact.save()
        send_mail(
        'New message from your site',
        f'Name: {name}\nEmail: {email}\nMessage: {message}',
        email,
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
        messages.success(request, 'Your message has been sent')
        engine = pyttsx3.init()
        engine.say(f"Thanks {request.user.username}, for contacting us")
        t = threading.Thread(target=engine.runAndWait)
        t.start()
        engine.endLoop()
        engine = None  # reinitialize the engine object
        return redirect('/')
    else:
        return render(request, 'contact.html', {'product_count': product_count, 'favorite_count': favorite_count})


def loginuser(request):
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    if request.method == 'POST':
        loginusername = request.POST['loginusername']
        loginpassword = request.POST['loginpassword']
        loginn = authenticate(username=loginusername, password=loginpassword)
        if loginn is not None:
            login(request, loginn)
            messages.success(request, 'SuccessFully Login')
            engine = pyttsx3.init()
            engine.say(f"Welcome, {loginusername}")
            t = threading.Thread(target=engine.runAndWait)
            t.start()
            engine.endLoop()
            engine = None  # reinitialize the engine object
            return redirect('/')
        else:
            messages.warning(request, 'invalid Credentials')
            return redirect('login')
    else:
        return render(request, 'login.html', {'product_count': product_count, 'favorite_count': favorite_count})    

def logoutuser(request):
    username = request.user.username
    logout(request)
    messages.success(request, 'Successfully logged out')

    engine = pyttsx3.init()
    engine.say(f"You logged out successfully. Bye Bye, {username}. See You Later")
    t = threading.Thread(target=engine.runAndWait)
    t.start()
    engine.endLoop()
    engine = None  # reinitialize the engine object

    return redirect('/')


User = get_user_model()


def generate_activation_token():
    return secrets.token_hex(32)


def generate_login_token(email, token):
    # Concatenate the email and activation token
    data = email + token
    # Generate a unique key for the user based on the data and a secret key
    key = settings.SECRET_KEY.encode('utf-8')
    hashed_data = hmac.new(key, data.encode(
        'utf-8'), hashlib.sha256).hexdigest()
    # Return the login token, which includes the email, activation token, and hashed key
    return f"{email}:{token}:{hashed_data}"


def send_confirmation_email(request, email, token):
    subject = 'Welcome to our site'
    # Generates a unique login token for the user
    login_token = generate_login_token(email, token)
    login_url = request.build_absolute_uri(reverse('login_with_token', args=[
                                           login_token]))  # Builds the login URL with the token included
    message = f'Thank you for registering on our site. Click the following link to activate your account and automatically log in:\n\n{login_url}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


def register(request):
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()
    if request.method == 'POST':
        registerfname = request.POST['registerfname']
        registerlname = request.POST['registerlname']
        registerusername = request.POST['registerusername']
        registeremail = request.POST['registeremail']
        registerpassword = request.POST['registerpassword']
        confirmpassword = request.POST['confirmpassword']
        if registerpassword == confirmpassword:
            if User.objects.filter(email=registeremail).exists():
                messages.warning(
                    request, 'This email address is already in use.')
                return redirect('register')
            else:
                token = generate_activation_token()
                register = User.objects.create_user(
                    registerusername, registeremail, registerpassword)
                register.first_name = registerfname
                register.last_name = registerlname
                register.activation_token = token
                register.is_verified = False
                register.save()
                send_confirmation_email(request, registeremail, token)
                messages.success(
                    request, 'Registration successful. Please check your email to activate your account.')
                engine = pyttsx3.init()
                engine.say(f"Thanks For registering us, {registerusername}")
                t = threading.Thread(target=engine.runAndWait)
                t.start()
                engine.endLoop()
                engine = None  # reinitialize the engine object
                return redirect('/login')
        else:
            messages.warning(request, 'Passwords do not match.')
            return redirect('register')
    else:
        return render(request, 'register.html', {'product_count': product_count, 'favorite_count': favorite_count})


def login_with_token(request, token):
    # Split the token into its components
    try:
        email, activation_token, hashed_key = token.split(':')
    except ValueError:
        return redirect('/login')
    # Check that the hashed key matches the expected value
    expected_key = hmac.new(settings.SECRET_KEY.encode('utf-8'),
                            (email + activation_token).encode('utf-8'),
                            hashlib.sha256).hexdigest()
    if hashed_key != expected_key:
        return redirect('/login')
    # Authenticate and log in the user
    user = authenticate(request, email=email)
    if user is not None and user.activation_token == activation_token:
        user.is_active = True
        user.activation_token = ''
        user.save()
        login(request, user)
        return redirect('/')
    else:
        return redirect('/login')


@login_required(login_url='/login')
def add_to_favorite(request, id):
    product = Product.objects.get(id=id)

    favorite = Favorite.objects.filter(
        product=product, user=request.user).first()

    if favorite:
        messages.warning(request, f'{product} is already exists in Favorites')
        return redirect('/favorites')
    favorite = Favorite(user=request.user, product=product)
    favorite.save()
    messages.success(request, 'This product has been added to your Favorites')
    return redirect('/favorites')
    if request.user.is_not_authenticated:
        return redirect('/login')
        messages.warning(request, 'Please Login First')


def delete_favorite(request, id):
    favorite = Favorite.objects.get(id=id)
    favorite.delete()
    return redirect('/favorites')


@login_required(login_url='/login')
def show_favorite(request):
    product_count = 0
    if request.user.is_authenticated:
        cart_products = Cart.objects.filter(user=request.user)
        for cart_item in cart_products:
            product_count += cart_item.quantity
    favorite_count = 0
    if request.user.is_authenticated:
        favorite_products = Favorite.objects.filter(user=request.user)
        favorite_count = favorite_products.count()

        user = request.user
        favorites = Favorite.objects.filter(user=user)
        if favorite_count > 0:
            return render(request, 'favorite.html', {'favorites': favorites, 'product_count': product_count, 'favorite_count': favorite_count})
        else:
            return render(request, 'emptyfavorite.html', {'product_count': product_count, 'favorite_count': favorite_count})

def home_search_view(request):
    queryy = request.GET.get('qu')
    results = []
    if queryy:
        results = Product.objects.filter(
            productname__icontains=queryy) | Product.objects.filter(productprice__icontains=queryy)
    return render(request, 'search.html', {'queryy': queryy, 'results': results})
