# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Customer, Product, Sale, SaleItem, Supplier
from .models import Purchase


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('name', 'phone_number')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }


class ProductForm(forms.ModelForm):
    new_supplier = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New supplier name (if not listed)'}))

    class Meta:
        model = Product
        fields = ('name', 'description', 'category', 'selling_price', 'purchase_price', 'stock_quantity', 'low_stock_threshold', 'purchase_type', 'supplier')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Product Description'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Selling Price', 'step': '0.01'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Purchase Price', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stock Quantity'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Low Stock Threshold'}),
            'purchase_type': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # show suppliers in select
        try:
            self.fields['supplier'].queryset = Supplier.objects.all()
        except Exception:
            # If the Supplier table doesn't exist yet (migrations pending), avoid crashing the form.
            # Fall back to an empty queryset; user should run `makemigrations`/`migrate`.
            from django.db.models.query import QuerySet
            self.fields['supplier'].queryset = Supplier.objects.none()

    def clean(self):
        cleaned = super().clean()
        ptype = cleaned.get('purchase_type')
        supplier = cleaned.get('supplier')
        new_supplier = cleaned.get('new_supplier')
        if ptype == 'credit' and not (supplier or new_supplier):
            raise forms.ValidationError('For credit products, select or enter a supplier.')
        return cleaned

    def save(self, commit=True):
        new_supplier = self.cleaned_data.get('new_supplier')
        if new_supplier:
            supplier_obj, created = Supplier.objects.get_or_create(name=new_supplier)
            self.instance.supplier = supplier_obj
        return super().save(commit=commit)


class SaleItemForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(stock_quantity__gt=0), 
                                      widget=forms.Select(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'}))


class SaleForm(forms.ModelForm):
    customer_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Name (leave blank for walk-in)'}))
    customer_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (optional)'}))
    
    class Meta:
        model = Sale
        fields = ('discount_percentage',)
        widgets = {
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Discount %', 'step': '0.01'}),
        }


class SearchProductForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name, category, or stock level'}))
    category_filter = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by category'}))
    min_stock = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum stock'}))


class ReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    report_type = forms.ChoiceField(choices=[('sales', 'Sales Report'), ('inventory', 'Inventory Report')], 
                                     widget=forms.Select(attrs={'class': 'form-control'}))


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ('supplier', 'purchase_type', 'credit_by', 'total_amount')
        widgets = {
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'purchase_type': forms.Select(attrs={'class': 'form-control'}),
            'credit_by': forms.Select(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def clean(self):
        cleaned = super().clean()
        ptype = cleaned.get('purchase_type')
        credit_by = cleaned.get('credit_by')
        if ptype == 'credit' and not credit_by:
            raise forms.ValidationError('For credit purchases you must specify who is responsible (credit_by).')
        return cleaned
