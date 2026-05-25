# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User, Customer, Product, Sale, SaleItem, Return, Supplier
from .models import PurchaseItem
from .forms import (UserRegistrationForm, CustomerForm, ProductForm, 
                    SaleItemForm, SaleForm, SearchProductForm, ReportForm, PurchaseForm, SupplierForm)
from .models import Purchase


# ============ AUTHENTICATION VIEWS ============

def login_view(request):
    """Handle user login with role-based access."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


def register_view(request):
    """Admin-only user registration."""
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


# ============ DASHBOARD VIEWS ============

@login_required
def dashboard(request):
    """Role-based dashboard with key metrics."""
    context = {}
    
    import json
    from datetime import timedelta
    today = timezone.now().date()
    
    # Chart data: Last 7 days revenue
    dates = [(today - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
    revenue_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        r = Sale.objects.filter(timestamp__date=d).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        revenue_data.append(float(r))
        
    context['chart_dates'] = json.dumps(dates)
    context['chart_revenue'] = json.dumps(revenue_data)
    
    if request.user.role == 'admin':
        context['total_users'] = User.objects.count()
        context['total_sales'] = Sale.objects.count()
        return render(request, 'admin_dashboard.html', context)
    
    elif request.user.role == 'manager':
        context['today_sales'] = Sale.objects.filter(timestamp__date=today).count()
        context['today_revenue'] = revenue_data[-1]  # Today's revenue is the last item
        context['low_stock_products'] = Product.objects.filter(stock_quantity__lte=F('low_stock_threshold')).count()
        context['total_customers'] = Customer.objects.count()
        context['total_products'] = Product.objects.filter(is_active=True).count()
        return render(request, 'manager_dashboard.html', context)
    
    else:  # cashier
        context['pending_sales'] = 0  # Can track temporary sales
        return render(request, 'cashier_dashboard.html', context)


# ============ PRODUCT MANAGEMENT VIEWS ============

@login_required
def product_list(request):
    """List all products with search and filter functionality."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')
    
    form = SearchProductForm(request.GET or None)
    products = Product.objects.filter(is_active=True)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category_filter')
        min_stock = form.cleaned_data.get('min_stock')
        
        if search:
            products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if category:
            products = products.filter(category__icontains=category)
        if min_stock is not None:
            products = products.filter(stock_quantity__gte=min_stock)
    
    # Highlight low stock items
    for product in products:
        product.is_low_stock = product.stock_quantity <= product.low_stock_threshold
    
    context = {'products': products, 'form': form}
    return render(request, 'product_list.html', context)


@login_required
def product_create(request):
    """Add a new product."""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully.')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    return render(request, 'product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
def product_update(request, pk):
    """Update product details."""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'product_form.html', {'form': form, 'title': 'Update Product'})


@login_required
def product_delete(request, pk):
    """Delete a product."""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, 'Product removed from portal (soft-deleted).')
        return redirect('product_list')
    
    return render(request, 'product_confirm_delete.html', {'product': product})


# ============ CUSTOMER MANAGEMENT VIEWS ============

@login_required
def customer_list(request):
    """List all customers."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')
    
    customers = Customer.objects.all().order_by('-created_at')
    context = {'customers': customers}
    return render(request, 'customer_list.html', context)


@login_required
def customer_create(request):
    """Add a new customer."""
    if request.user.role not in ['admin', 'manager', 'cashier']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully.')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_update(request, pk):
    """Update customer information."""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customer_form.html', {'form': form, 'title': 'Update Customer'})


@login_required
def customer_delete(request, pk):
    """Delete a customer."""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('customer_list')
    
    return render(request, 'customer_confirm_delete.html', {'customer': customer})


# ============ SALES VIEWS ============

@login_required
def sales_transaction(request):
    """Process a new sales transaction."""
    # Allow both cashiers and admins to perform sales transactions
    if request.user.role not in ['cashier', 'admin']:
        messages.error(request, 'Access denied. Cashiers or Admin only.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            # Validate stock before creating sale
            products = request.POST.getlist('product_id')
            quantities = request.POST.getlist('quantity')
            
            # Check if all products have enough stock
            stock_issues = []
            for product_id, quantity in zip(products, quantities):
                if product_id and quantity:
                    product = get_object_or_404(Product, pk=product_id)
                    quantity = int(quantity)
                    
                    if product.stock_quantity < quantity:
                        stock_issues.append(
                            f'{product.name}: Only {product.stock_quantity} in stock, '
                            f'trying to sell {quantity}'
                        )
            
            if stock_issues:
                messages.error(request, 'Insufficient stock: ' + ' | '.join(stock_issues))
                form = SaleForm()
                products_list = Product.objects.filter(is_active=True)
                return render(request, 'sales_transaction.html', {
                    'form': form,
                    'products': products_list
                })
            
            # Get or create customer
            customer_name = form.cleaned_data.get('customer_name')
            customer_phone = form.cleaned_data.get('customer_phone')
            
            if customer_name:
                customer, _ = Customer.objects.get_or_create(
                    name=customer_name,
                    defaults={'phone_number': customer_phone or ''}
                )
            else:
                # Default random/walk-in customer
                customer, _ = Customer.objects.get_or_create(
                    name='Walk-in Customer',
                    defaults={'phone_number': '0000000000'}
                )
            
            # Create sale
            discount_percentage = form.cleaned_data.get('discount_percentage', 0)
            total_amount = request.POST.get('total_amount')
            
            if total_amount:
                sale = Sale.objects.create(
                    customer=customer,
                    cashier=request.user,
                    total_amount=total_amount,
                    discount_percentage=discount_percentage
                )
                
                # Process sale items and update inventory
                discount_amounts = request.POST.getlist('discount_amount')
                for product_id, quantity, discount_amount in zip(products, quantities, discount_amounts):
                    if product_id and quantity:
                        product = get_object_or_404(Product, pk=product_id)
                        quantity = int(quantity)
                        discount_amt = float(discount_amount) if discount_amount else 0
                        
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            price_at_sale=product.selling_price,
                            discount_amount=discount_amt
                        )
                        
                        # Update inventory
                        product.stock_quantity -= quantity
                        product.save()
                
                messages.success(request, f'Sale #{sale.id} processed successfully.')
                return redirect('sales_receipt', pk=sale.id)
    else:
        form = SaleForm()
    
    products = Product.objects.filter(stock_quantity__gt=0)
    context = {'form': form, 'products': products}
    return render(request, 'sales_transaction.html', context)


@login_required
def sales_receipt(request, pk):
    """Display receipt for a completed sale."""
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.user.role == 'cashier' and sale.cashier != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Calculate subtotal and discount amount from sale items
    sale_items = SaleItem.objects.filter(sale=sale)
    subtotal = sum(item.quantity * item.price_at_sale for item in sale_items)
    
    # Calculate discount amount
    discount_amount = subtotal * (sale.discount_percentage / 100) if sale.discount_percentage > 0 else 0
    
    context = {
        'sale': sale,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'items': sale_items
    }
    return render(request, 'sales_receipt.html', context)


@require_POST
@login_required
def email_receipt(request, pk):
    """Simulate emailing the receipt to the customer."""
    sale = get_object_or_404(Sale, pk=pk)
    email = request.POST.get('customer_email')
    
    if email:
        # In a production 2026 app, this would use django.core.mail.send_mail
        # or an API like SendGrid/Postmark configured in settings.py
        messages.success(request, f"Digital receipt for Sale #{sale.id} has been emailed to {email}")
    else:
        messages.error(request, "Please provide a valid email address.")
        
    return redirect('sales_receipt', pk=sale.id)


@login_required
def sales_history(request):
    """View sales history."""
    if request.user.role == 'cashier':
        sales = Sale.objects.filter(cashier=request.user).order_by('-timestamp')
    else:
        sales = Sale.objects.all().order_by('-timestamp')
    
    context = {'sales': sales}
    return render(request, 'sales_history.html', context)


# ============ PRODUCT RETURN VIEWS ============

@login_required
def product_returns(request):
    """View and manage product returns."""
    if request.user.role == 'cashier':
        returns = Return.objects.filter(returned_by=request.user).order_by('-created_at')
    else:
        returns = Return.objects.all().order_by('-created_at')
    
    context = {'returns': returns}
    return render(request, 'product_returns.html', context)


@login_required
def process_return(request, pk):
    """Process a product return."""
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.user.role == 'cashier' and sale.cashier != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    sale_items = sale.items.all()
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        reason = request.POST.get('reason', '')
        
        # Get the sale item to find the price
        sale_item = get_object_or_404(SaleItem, sale=sale, product_id=product_id)
        return_amount = (sale_item.price_at_sale * quantity) - sale_item.discount_amount
        
        # Create return record
        Return.objects.create(
            sale=sale,
            product_id=product_id,
            quantity=quantity,
            reason=reason,
            return_amount=return_amount,
            returned_by=request.user
        )
        
        # Update inventory - add back to stock
        product = Product.objects.get(pk=product_id)
        product.stock_quantity += quantity
        product.save()
        
        messages.success(request, f'Return processed successfully. ${return_amount} refunded.')
        return redirect('sales_receipt', pk=sale.id)
    
    context = {'sale': sale, 'sale_items': sale_items}
    return render(request, 'process_return.html', context)


# ============ INVENTORY VIEWS ============

@login_required
def inventory_status(request):
    """View inventory status and low-stock alerts."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')
    
    products = Product.objects.filter(is_active=True)
    low_stock_products = products.filter(stock_quantity__lte=F('low_stock_threshold'))

    total_stock_value = products.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('stock_quantity') * F('selling_price'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    
    context = {
        'products': products,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_products.count(),
        'total_stock_value': total_stock_value,
    }
    return render(request, 'inventory_status.html', context)


@login_required
def purchase_list(request):
    """List purchases and provide filter by type (cash/credit)."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')

    ptype = request.GET.get('type')  # 'cash' or 'credit' or None
    purchases = Purchase.objects.all().order_by('-timestamp')
    if ptype in ('cash', 'credit'):
        purchases = purchases.filter(purchase_type=ptype)

    # Ensure each purchase has a computed_total attribute (fallback to Purchase.total_amount)
    from .models import PurchaseItem
    for p in purchases:
        # compute sum of purchase items for this purchase
        agg = PurchaseItem.objects.filter(purchase=p).aggregate(total=Sum(ExpressionWrapper(F('quantity') * F('price_at_purchase'), output_field=DecimalField())))
        p.computed_total = agg['total'] or p.total_amount or 0

    context = {'purchases': purchases, 'filter_type': ptype}
    return render(request, 'purchase_list.html', context)


@login_required
def purchase_create(request):
    """Create a purchase record."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')

    products = Product.objects.filter(is_active=True)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('price')

        if form.is_valid():
            if not product_ids:
                messages.error(request, 'Please add at least one product line to the purchase.')
                return render(request, 'purchase_form.html', {'form': form, 'products': products})

            purchase = form.save(commit=False)
            purchase.created_by = request.user

            # compute total from line items
            total_amount = 0
            line_items = []
            for pid, qty, pr in zip(product_ids, quantities, prices):
                try:
                    prod = Product.objects.get(pk=int(pid))
                except (Product.DoesNotExist, ValueError):
                    continue
                try:
                    q = int(qty)
                except ValueError:
                    q = 0
                try:
                    pprice = float(pr)
                except ValueError:
                    pprice = float(prod.purchase_price or 0)

                if q <= 0:
                    continue
                line_total = q * pprice
                total_amount += line_total
                line_items.append((prod, q, pprice))

            purchase.total_amount = total_amount
            purchase.save()

            # create PurchaseItem records and update product stock
            for prod, q, pprice in line_items:
                from .models import PurchaseItem
                PurchaseItem.objects.create(purchase=purchase, product=prod, quantity=q, price_at_purchase=pprice)
                prod.stock_quantity = (prod.stock_quantity or 0) + q
                # update last purchase price
                prod.purchase_price = pprice
                prod.save()

            messages.success(request, 'Purchase recorded successfully.')
            return redirect('purchase_list')
    else:
        form = PurchaseForm()

    return render(request, 'purchase_form.html', {'form': form, 'products': products})


@login_required
def purchase_report(request):
    """Simple purchase report view — filter by purchase type and date range."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')

    start = request.GET.get('start')
    end = request.GET.get('end')
    ptype = request.GET.get('type')

    purchases = Purchase.objects.all().order_by('-timestamp')
    # Suppliers list (for filtering & summary)
    try:
        suppliers = Supplier.objects.all()
    except Exception:
        suppliers = Supplier.objects.none()

    supplier_id = request.GET.get('supplier_id')
    if supplier_id and supplier_id.isdigit():
        try:
            sel_sup = suppliers.get(pk=int(supplier_id))
            # Filter purchases whose supplier text contains the supplier name (case-insensitive)
            purchases = purchases.filter(supplier__icontains=sel_sup.name)
        except Supplier.DoesNotExist:
            sel_sup = None
    else:
        sel_sup = None
    if ptype in ('cash', 'credit'):
        purchases = purchases.filter(purchase_type=ptype)
    if start:
        purchases = purchases.filter(timestamp__date__gte=start)
    if end:
        purchases = purchases.filter(timestamp__date__lte=end)

    # Prefer to compute total from PurchaseItem lines for accuracy (fallback to Purchase.total_amount)
    try:
        total = PurchaseItem.objects.filter(purchase__in=purchases).aggregate(total=Sum(ExpressionWrapper(F('quantity') * F('price_at_purchase'), output_field=DecimalField())))['total'] or 0
    except Exception:
        total = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    # Build supplier summary (total purchases + total sales for products from that supplier)
    supplier_summary = []
    sale_items = SaleItem.objects.all()
    for sup in suppliers:
        # use icontains to match variations in stored supplier text
        sup_purchases_total = purchases.filter(supplier__icontains=sup.name).aggregate(total=Sum('total_amount'))['total'] or 0
        sup_sales_total = sale_items.filter(product__supplier=sup).aggregate(
            total=Sum(ExpressionWrapper(F('quantity') * F('price_at_sale'), output_field=DecimalField()))
        )['total'] or 0
        supplier_summary.append({
            'supplier': sup,
            'purchases_total': sup_purchases_total,
            'sales_total': sup_sales_total,
        })

    # Export disabled: CSV export removed per project settings

    context = {'purchases': purchases, 'total': total, 'filter_type': ptype, 'start': start, 'end': end, 'suppliers': suppliers, 'selected_supplier': sel_sup, 'supplier_summary': supplier_summary}
    return render(request, 'purchase_report.html', context)


@login_required
def supplier_history(request, pk):
    """Show a supplier's complete history: purchases (from Purchase.supplier text) and sales (SaleItems for products linked to Supplier)."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')

    sup = get_object_or_404(Supplier, pk=pk)

    # Purchases where Purchase.supplier text contains supplier name (case-insensitive)
    purchases = Purchase.objects.filter(supplier__icontains=sup.name).order_by('-timestamp')

    # Sale items for products that have this supplier FK
    sale_items = SaleItem.objects.filter(product__supplier=sup).select_related('sale', 'product').order_by('-sale__timestamp')

    # purchases_total: prefer sum of PurchaseItem lines for purchases that reference this supplier text
    from .models import PurchaseItem
    purchases_total = PurchaseItem.objects.filter(purchase__supplier__icontains=sup.name).aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_at_purchase'), output_field=DecimalField()))
    )['total']
    if not purchases_total:
        # fallback to older Purchase.total_amount field if PurchaseItem rows are missing
        purchases_total = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    sales_total = sale_items.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_at_sale'), output_field=DecimalField()))
    )['total'] or 0

    # Build per-product summary for products that belong to this supplier
    products_for_supplier = Product.objects.filter(supplier=sup)
    product_summary = []
    for p in products_for_supplier:
        total_sold = SaleItem.objects.filter(product=p).aggregate(qty=Sum('quantity'))['qty'] or 0
        current_stock = p.stock_quantity or 0
        # total acquired from this supplier = sum of PurchaseItem.quantity for purchases linked to this supplier text
        acquired_agg = PurchaseItem.objects.filter(product=p, purchase__supplier__icontains=sup.name).aggregate(total=Sum('quantity'))
        acquired_total = acquired_agg['total']
        if acquired_total and acquired_total > 0:
            total_acquired = acquired_total
            purchase_subtotal = PurchaseItem.objects.filter(product=p, purchase__supplier__icontains=sup.name).aggregate(
                subtotal=Sum(ExpressionWrapper(F('quantity') * F('price_at_purchase'), output_field=DecimalField()))
            )['subtotal'] or 0
        else:
            # If there are no PurchaseItem rows (older data), infer acquired qty from current stock + total sold
            total_sold = SaleItem.objects.filter(product=p).aggregate(qty=Sum('quantity'))['qty'] or 0
            current_stock = p.stock_quantity or 0
            total_acquired = current_stock + total_sold
            purchase_subtotal = float(total_acquired) * float(p.purchase_price or 0)
        sales_revenue = float(total_sold) * float(p.selling_price or 0)
        product_summary.append({
            'product': p,
            'purchase_price': p.purchase_price,
            'selling_price': p.selling_price,
            'acquired_qty': total_acquired,
            'sold_qty': total_sold,
            'purchase_subtotal': purchase_subtotal,
            'sales_revenue': sales_revenue,
        })

    # Build combined history (purchase lines + sales lines)
    combined_history = []
    # include PurchaseItem lines
    purchase_items = []
    try:
        # include PurchaseItem rows where the purchase supplier text contains the supplier name
        # or where the Product.supplier FK points to this supplier — covers both legacy and newer records
        purchase_items = PurchaseItem.objects.filter(
            Q(purchase__supplier__icontains=sup.name) | Q(product__supplier=sup)
        ).select_related('purchase', 'product')
    except Exception:
        purchase_items = []

    purchase_ids_with_items = set([pi.purchase_id for pi in purchase_items])

    for pi in purchase_items:
        combined_history.append({
            'type': 'Purchase',
            'ref_id': pi.purchase.id,
            'date': pi.purchase.timestamp,
            'item': pi.product.name,
            'quantity': pi.quantity,
            'amount': float(pi.quantity) * float(pi.price_at_purchase or 0),
        })

    # purchases without PurchaseItem lines — fall back to Purchase.total_amount
    purchases_without_items = purchases.exclude(pk__in=purchase_ids_with_items)
    for p in purchases_without_items:
        combined_history.append({
            'type': 'Purchase',
            'ref_id': p.id,
            'date': p.timestamp,
            'item': p.supplier or '',
            'quantity': '',
            'amount': float(p.total_amount or 0),
        })

    # add sale lines
    for si in sale_items:
        combined_history.append({
            'type': 'Sale',
            'ref_id': si.sale.id,
            'date': si.sale.timestamp,
            'item': si.product.name,
            'quantity': si.quantity,
            'amount': float(si.quantity) * float(si.price_at_sale or 0),
        })

    # sort by date desc
    combined_history.sort(key=lambda x: x['date'] or datetime.min, reverse=True)

    # Export disabled: CSV export removed per project settings

    context = {
        'supplier': sup,
        'purchases': purchases,
        'sale_items': sale_items,
        'purchases_total': purchases_total,
        'sales_total': sales_total,
        'product_summary': product_summary,
        'combined_history': combined_history,
    }
    return render(request, 'supplier_history.html', context)


@login_required
def supplier_create(request):
    """Add a new supplier."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully.')
            return redirect('supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@login_required
def supplier_list(request):
    """Simple list of suppliers with links to their history."""
    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')

    try:
        suppliers = Supplier.objects.all().order_by('name')
    except Exception:
        suppliers = Supplier.objects.none()

    context = {'suppliers': suppliers}
    return render(request, 'supplier_list.html', context)


# ============ REPORT VIEWS ============

@login_required
def sales_report(request):
    """Generate sales reports for a given period with quantity details."""

    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')
    
    form = ReportForm(request.GET or None)
    sales = Sale.objects.all()
    sales_items = SaleItem.objects.all()
    report_data = None
    product_summary = None
    
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        # Combine dates with time for proper filtering
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        sales = sales.filter(timestamp__range=[start_datetime, end_datetime])
        sales_items = sales_items.filter(sale__timestamp__range=[start_datetime, end_datetime])
        
        # Product-level summary with quantities
        product_summary = {}
        for item in sales_items:
            if item.product.id not in product_summary:
                product_summary[item.product.id] = {
                    'product_name': item.product.name,
                    'total_quantity': 0,
                    'total_revenue': 0,
                    'num_items': 0
                }
            product_summary[item.product.id]['total_quantity'] += item.quantity
            product_summary[item.product.id]['total_revenue'] += (item.quantity * item.price_at_sale - item.discount_amount)
            product_summary[item.product.id]['num_items'] += 1
        
        report_data = {
            'total_sales': sales.count(),
            'total_revenue': sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'average_sale': sales.aggregate(avg=Sum('total_amount') / Count('id'))['avg'] or 0,
            'total_discount': sales.aggregate(Sum('discount_percentage'))['discount_percentage__sum'] or 0,
            'total_quantity_sold': sales_items.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'num_unique_items': sales_items.values('product').distinct().count(),
            'period': f"{start_date} to {end_date}"
        }
        
        # Export disabled: CSV export removed per project settings
    
    context = {
        'form': form,
        'sales': sales,
        'report_data': report_data,
        'product_summary': product_summary
    }
    return render(request, 'sales_report.html', context)


@login_required
def inventory_report(request):
    """Generate inventory reports."""

    if request.user.role == 'cashier':
        messages.error(request, 'Access denied. Manager or Admin only.')
        return redirect('dashboard')
    
    products = Product.objects.filter(is_active=True)

    # Filters: purchase_type (cash/credit) and supplier
    purchase_type = request.GET.get('purchase_type')
    supplier_id = request.GET.get('supplier_id')

    try:
        suppliers = Supplier.objects.all()
    except Exception:
        suppliers = Supplier.objects.none()

    if purchase_type in ['cash', 'credit']:
        products = products.filter(purchase_type=purchase_type)

    if supplier_id:
        try:
            products = products.filter(supplier_id=int(supplier_id))
        except ValueError:
            pass

    total_stock_value = sum(p.stock_quantity * p.selling_price for p in products)
    total_cost_value = sum(p.stock_quantity * p.purchase_price for p in products)

    report_data = {
        'total_products': products.count(),
        'total_stock_value': total_stock_value,
        'total_cost_value': total_cost_value,
        'low_stock_count': products.filter(stock_quantity__lte=F('low_stock_threshold')).count(),
        'out_of_stock_count': products.filter(stock_quantity=0).count(),
    }
    
    # Export disabled: CSV export removed per project settings
    
    context = {
        'products': products,
        'report_data': report_data,
        'suppliers': suppliers,
        'selected_purchase_type': purchase_type,
        'selected_supplier_id': int(supplier_id) if supplier_id and supplier_id.isdigit() else None,
    }
    return render(request, 'inventory_report.html', context)
