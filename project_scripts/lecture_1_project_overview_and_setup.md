
Hello everyone, and welcome to this new series where we'll be diving deep into a complete Point of Sale and Inventory Management System built with Django!

**What We're Building**

This is a feature-rich application designed to handle the typical needs of a retail business. Here’s a quick look at what it can do:

*   **User Management:** The system supports three distinct user roles: Admin, Manager, and Cashier, each with different levels of access and capabilities.
*   **Product Management:** You can easily add, update, and delete products, manage their stock levels, and set thresholds for low-stock alerts.
*   **Sales Transactions:** A cashier can process sales, add products to a cart, and generate receipts.
*   **Customer Management:** Keep track of your customers and their purchase history.
*   **Inventory and Sales Reporting:** The system provides valuable insights with reports on sales, inventory status, and more.

In this first video, we're going to get the project up and running on our local machines.

**1. Project Structure**

First, let's quickly go over the main files and directories:

*   `PosIms/`: This is the main project directory.
*   `core/`: This is the main Django app that contains most of our project's logic.
    *   `models.py`: Defines our database structure. We'll have tables for Users, Products, Sales, and Customers.
    *   `views.py`: Contains the logic for handling requests and rendering our web pages.
    *   `urls.py`: Defines the URL patterns for our application.
    *   `templates/`: This folder holds all the HTML files that create the user interface.
*   `posIms/`: This is the project's configuration directory.
    *   `settings.py`: Contains all the project settings, like database configuration and installed apps.
    *   `urls.py`: The main URL configuration for the entire project.
*   `manage.py`: A command-line utility that lets you interact with this Django project.
*   `requirements.txt`: This file lists all the Python packages our project depends on.
*   `populate_demo_data.py`: A handy script to fill our database with some initial sample data so we can start using the app right away.

**2. Setting Up the Project**

Alright, let's get this set up. Open your terminal and follow along.

First, it's always a good practice to create a virtual environment to keep our project dependencies isolated.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate
```

Now that our environment is active, let's install all the necessary packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

This will install Django, Django REST Framework, and other packages this project needs.

**3. Initializing the Database**

With the dependencies installed, the next step is to set up our database. Django uses an SQLite database by default, which is perfect for local development.

We need to run migrations to create the database tables based on our models.

```bash
python manage.py migrate
```

**4. Populating with Demo Data**

To make it easier to explore the application, I've created a script that populates the database with sample users, products, and customers.

Let's run it:

```bash
python populate_demo_data.py
```

This script will create an admin, a manager, and a cashier user for you. The login credentials will be printed in the terminal.

**5. Running the Development Server**

We're all set! Now, let's start the Django development server.

```bash
python manage.py runserver
```

You can now open your web browser and navigate to `http://127.0.0.1:8000/`.

You should see the login page for our Point of Sale system. You can log in with the user credentials provided by the population script (e.g., username: `admin`, password: `password`).

**What's Next?**

That's it for our first lecture! We've successfully set up the project and have it running locally.

In the next video, we'll take a closer look at the heart of our application: the Django models. We'll explore how the data is structured and how the different pieces of our application are related.

Thanks for watching, and I'll see you in the next one!
