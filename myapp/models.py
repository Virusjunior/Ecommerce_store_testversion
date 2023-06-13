from django.db import models
from ckeditor.fields import RichTextField
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.core.validators import MinValueValidator, MaxValueValidator

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zipcode = models.IntegerField()

    def __str__(self):
        return f'{self.name} from user "{self.user}"'
    

class Contact(models.Model):
    name = models.CharField(max_length=20)
    email = models.EmailField()
    subject = models.CharField(max_length=20)
    message = models.TextField(max_length=1000)

    def __str__(self):
        return self.name

def __str__(self):
    return str(self.id)

CATEGORY_CHOICES = [
    ('tp', 'trendyproducts'),
    ('md', 'mendress'),
    ('wd', 'womendress'),
    ('bd', 'babydress'),
    ('a', 'accerssories'),
    ('b', 'bags'),
    ('s', 'shoes'),
]
COLOR_CHOICES = [
    ('black', 'Black'),
    ('white', 'White'),
    ('red', 'Red'),
    ('blue', 'Blue'),
    ('green', 'Green'),
]


class Product(models.Model):
    # category = models.ForeignKey(Category, related_name='products',on_delete=models.CASCADE)
    productimage = models.ImageField(blank=False, default='', upload_to='')
    productcreated_at = models.DateTimeField(default=datetime.now, blank=True)
    productname = models.CharField(max_length=40, default='')
    productprice = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    productprevprice = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    productinfo = RichTextField()
    productdescription = RichTextField()
    productaddinfo = RichTextField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, blank=True, null=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_count = models.IntegerField(default=0)
    color = models.CharField(choices=COLOR_CHOICES, max_length=20, default='', blank=True)

    def __str__(self):
        return self.productname

# def __str__(self):
#     return str(self.id)

class ProductsImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='')
    def __str__(self):
        return f'This image is for {self.product.productname}'
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE, default='', blank=True,null=True)
    stars = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    # id = models.AutoField(primary_key=True)
    review = models.TextField()
    created_at = models.DateTimeField(default=datetime.now, blank= True)
    name = models.CharField(max_length=40)
    email = models.EmailField()
    def __str__(self):
        return f'{self.name} review for {self.product}'
    @property
    def staricon(self):
        stars_icon = '<i class="fas fa-star"></i>'
        return format_html(''.join([stars_icon for _ in range(self.stars)]))

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # color = models.CharField(max_length=20) # add color field
    quantity = models.PositiveIntegerField(default=1)
    discount = models.BooleanField(default=False)
    added_on = models.DateTimeField(default=datetime.now, blank= True)

    
    def __str__(self):
        return f'{self.user} cart for {self.product}'
    
    @property
    def totalcost(self):
        if self.discount:
            return Decimal(self.product.productprice) * self.quantity * Decimal(0.9)
        else:
            return Decimal(self.product.productprice) * self.quantity

    @property
    def discounted_price(self):
        if self.discount:
            return self.product.productprice * self.quantity-1
        else:
            return self.product.productprice


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    def __str__(self):
        return f'{self.user} favorites {self.product}'
    

status = (
    ('Accepted','Accepted'),
    ('Packed', 'Packed'),
    ('On The Way', 'On The Way'),
    ('Delivered', 'Delivered'),
    ('Cancel', 'Cancel'),
)

class OrderPlaced(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered_date = models.DateTimeField(default=datetime.now, blank= True)
    status = models.CharField(choices=status, max_length=30, default='Pending')

    def __str__(self):
        return self.product.productname
    
    
    