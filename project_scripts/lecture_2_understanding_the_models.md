
Hello everyone, and welcome back to our series on the Django Point of Sale and Inventory Management System.

In the last video, we got the project set up and running. Today, we're going to dive into the foundation of our application: the Django models.

**What are Models?**

In Django, a model is the single, definitive source of information about your data. It contains the essential fields and behaviors of the data you’re storing. Each model maps to a single database table.

Our models are defined in the `core/models.py` file. Let's open it up and take a look.

**(Show the `core/models.py` file on screen)**

**1. The `User` Model**

```python
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
```

We start with a custom `User` model. We're extending Django's built-in `AbstractUser` model. This is a common practice when you want to add extra fields to the standard user model.

The key addition here is the `role` field. This allows us to assign different roles to our users, which we'll use to control their permissions throughout the application.

**2. The `Product` Model**

```python
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    # ... and other fields
```

This is one of the most important models. It represents an item that can be sold. Let's break down its fields:

*   `name`, `description`, `category`: Basic information about the product.
*   `selling_price`: The price at which we sell the product. We use `DecimalField` for currency to avoid floating-point rounding issues.
*   `stock_quantity`: How many of this item we currently have in stock.
*   `low_stock_threshold`: When the `stock_quantity` falls below this number, we can trigger a low stock alert.

**3. The `Customer` Model**

```python
class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
```

This model is for storing information about our customers. It's a straightforward model with fields for name, email, phone number, and address. We also have a "Walk-in Customer" for sales where we don't need to record customer details.

**4. The `Sale` and `SaleItem` Models**

This is where things get interesting. How do we represent a sales transaction? We need to know who bought what, when, and for how much. We do this with two related models: `Sale` and `SaleItem`.

```python
class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # ... other fields

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
```

*   A `Sale` represents a single transaction. It has a link to a `Customer` (if applicable), the date of the sale, and the total amount.
*   A `SaleItem` represents a single line item within that sale.
    *   It has a `ForeignKey` to the `Sale` it belongs to. The `related_name='items'` is important; it lets us get all the items for a sale by calling `sale.items.all()`.
    *   It has a `ForeignKey` to the `Product` that was sold.
    *   `quantity` stores how many of that product were sold.
    *   `price_at_sale` is crucial. We store the price of the product *at the time of the sale*. Product prices can change, so we need to record the historical price for accurate sales records.

This `Sale` and `SaleItem` structure is a very common and powerful pattern for representing order-like data.

**Model Relationships**

The `ForeignKey` fields create relationships between our models:

*   A `Sale` can have many `SaleItem`s (One-to-Many).
*   A `Product` can be in many `SaleItem`s (One-to-Many).
*   A `Customer` can have many `Sale`s (One-to-Many).

These relationships are what make our database powerful. They allow us to ask complex questions like "What were the total sales for this customer last month?" or "Which products are selling the most?".

**What's Next?**

That's a tour of our core models. Understanding this data structure is key to understanding how the entire application works.

In the next lecture, we'll look at the "V" in MTV (Model-Template-View): the **Views**. We'll see how Django's views read data from these models and prepare it to be displayed on our web pages.

Thanks for watching, and I'll see you in the next one!
