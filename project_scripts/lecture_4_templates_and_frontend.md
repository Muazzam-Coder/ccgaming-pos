
Hello everyone, and welcome back to our Django POS series.

We've covered Models, Views, and URLs. Today, we're going to look at the final piece of the puzzle: **Templates**. This is the "T" in Django's MTV architecture, and it's all about the presentation layer of our application.

**What are Templates?**

A template is a text file that contains the structure of our output format (in our case, HTML). It has placeholders for where the dynamic data will go. The process of combining a template with data from a view to produce a final HTML page is called "rendering."

Our templates are located in the `core/templates/` directory.

**(Show the `core/templates/` directory structure)**

**1. Template Inheritance and `base.html`**

One of the most powerful features of Django's template engine is inheritance. Most websites have a common structure: a header, a footer, a sidebar, etc. Instead of repeating this code in every single HTML file, we can create a base template and have other templates "extend" it.

Let's look at `base.html`.

**(Show `base.html`)**

```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}My POS System{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/pos_modern.css' %}">
</head>
<body>
    <nav>
        <!-- Navigation bar here -->
    </nav>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <!-- Footer here -->
    </footer>
</body>
</html>
```

Notice the `{% block ... %}` and `{% endblock %}` tags. These define blocks that child templates can override.

*   `{% block title %}`: A child template can provide its own title.
*   `{% block content %}`: This is the main content area. Each page will fill this block with its specific content.

Also, notice this line: `<link rel="stylesheet" href="{% static 'css/pos_modern.css' %}">`. The `{% static ... %}` tag is how we link to our static files, like CSS and JavaScript. Django will automatically find the correct path to this file.

**2. Displaying Data with the Django Template Language**

Now, let's see how a child template uses this base. Let's look at `product_list.html`.

**(Show `product_list.html`)**

```html
{% extends 'base.html' %}

{% block title %}Product List{% endblock %}

{% block content %}
    <h1>Our Products</h1>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Price</th>
                <th>Stock</th>
            </tr>
        </thead>
        <tbody>
            {% for product in products %}
                <tr>
                    <td>{{ product.name }}</td>
                    <td>${{ product.selling_price|floatformat:2 }}</td>
                    <td>{{ product.stock_quantity }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
{% endblock %}
```

*   `{% extends 'base.html' %}`: This must be the very first line. It tells the template engine that this template inherits from `base.html`.
*   It then overrides the `title` and `content` blocks.
*   **Template Variables:** `{{ product.name }}`. The double curly braces are used to insert the value of a variable. In our `product_list` view, we passed a context dictionary `{'products': products}`. Here, we are accessing that `products` queryset.
*   **Template Tags:** `{% for product in products %}` and `{% endfor %}`. The curly-brace-percent syntax is for template tags. These provide logic, like loops and conditional statements. Here, we're looping through each `product` in the `products` queryset and creating a table row for it.
*   **Template Filters:** `{{ product.selling_price|floatformat:2 }}`. The pipe character applies a filter. The `floatformat` filter formats a number to a given number of decimal places, which is perfect for currency.

**3. The Cashier Dashboard - The Main Interface**

The most complex template is probably `cashier_dashboard.html`. This is the main screen that a cashier will use to make sales.

**(Show `cashier_dashboard.html`)**

This template brings everything together:
*   It has a list of products that can be added to a cart.
*   It uses JavaScript (which we'll touch on later) to handle the cart logic dynamically without needing to reload the page for every action.
*   It has a form to select a customer.
*   It calculates the total and subtotal of the sale in real-time.

This template is a good example of how you can build a rich, interactive user interface by combining Django templates with JavaScript.

**4. Static Files**

Our application's look and feel is controlled by CSS. The main stylesheet is `static/css/pos_modern.css`.

When we run `python manage.py collectstatic`, Django gathers all the static files from each app's `static` directory and puts them into a single `staticfiles` directory at the project root. This is the directory that is served in production.

**What's Next?**

We've now covered the full Model-View-Template cycle. You've seen how data flows from the database, through our models, is processed by our views, and is finally rendered into a user-facing webpage by our templates.

In the next and final lecture of this introductory series, we'll look at some of the more advanced features of the project, including the REST API and the reporting functionality.

Thanks for watching!
