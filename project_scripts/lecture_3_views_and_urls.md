
Hello everyone, and welcome back!

In our last session, we explored the models that form the backbone of our Point of Sale system. Today, we're moving on to the "V" in Django's MTV pattern: **Views**. We'll also look at how URLs map to these views.

**What are Views?**

A view function, or "view," is a Python function that takes a web request and returns a web response. This response can be the HTML contents of a web page, a redirect, a 404 error, an XML document, or an image... or anything, really.

Our views are located in `core/views.py`. They contain the business logic of our application.

**(Show the `core/views.py` file)**

Let's examine a few key views to understand how they work.

**1. `login_view` - Handling User Authentication**

```python
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                # ... other roles
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})
```

This view handles the login process.

*   If the request is a `GET` request, it simply displays the login form.
*   If it's a `POST` request (meaning the user submitted the form), it uses Django's built-in `AuthenticationForm` to validate the credentials.
*   The `authenticate` function checks if the username and password are valid.
*   If they are, the `login` function creates a session for the user.
*   Finally, it redirects the user to the appropriate dashboard based on their `role`.

**2. `product_list` - Displaying a List of Objects**

```python
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})
```

This is a much simpler view.

*   The `@login_required` decorator is a piece of Django middleware that ensures only logged-in users can access this page. If a non-logged-in user tries to access it, they'll be redirected to the login page.
*   `Product.objects.all()` is the Django ORM in action. This line retrieves all the records from the `Product` table in our database.
*   The `render` function takes the request, the name of a template (`product_list.html`), and a "context" dictionary. The `products` queryset is passed to the template, where we can loop through it to display each product.

**3. `product_create` - Creating New Objects with Forms**

```python
@login_required
@role_required('admin', 'manager')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form})
```

This view handles the creation of new products.

*   We have another decorator here: `@role_required('admin', 'manager')`. This is a custom decorator (which we'll look at later) that restricts access to this page to only users with the 'admin' or 'manager' role.
*   This view uses a `ProductForm`, which is a Django ModelForm. This form is automatically generated from our `Product` model.
*   If the request is a `POST`, we validate the submitted data.
*   If the form is valid, `form.save()` creates a new `Product` instance in the database with the data from the form. It's that simple!
*   We then redirect the user back to the product list.

**4. URLs - Mapping URLs to Views**

So, how does Django know which view to call for a given URL? That's handled in the `urls.py` files.

First, let's look at the main `posIms/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]
```

This is the root URL configuration. It does two things:
1.  It includes the URLs for the Django admin site at the `/admin/` path.
2.  For any other path (represented by the empty string `''`), it includes the URLs defined in our `core` app's `urls.py` file.

Now, let's look at `core/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    # ... many other paths
]
```

This is where the magic happens. Each `path()` function defines a URL pattern:

*   The first argument is the URL pattern itself (e.g., `products/`).
*   The second argument is the view function that should be called when that URL is requested (e.g., `views.product_list`).
*   The `name` argument gives the URL a unique name. This is a best practice because it allows us to refer to this URL from other parts of our code (like in redirects or templates) without having to hardcode the URL path.

So, when a user goes to `/products/`, Django finds the matching pattern in `core/urls.py` and calls the `product_list` view.

**What's Next?**

We've now seen how models store our data, and how views and URLs work together to process requests and send back responses.

In the next lecture, we'll complete the MTV picture by looking at **Templates**. We'll see how the data prepared by our views is rendered into the HTML that the user sees in their browser.

Thanks for watching!
