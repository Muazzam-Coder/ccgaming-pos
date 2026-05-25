from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField
from core.models import Supplier, Product, Purchase, PurchaseItem, SaleItem

s = Supplier.objects.get(pk=1)
print("SUPPLIER:", s.id, s.name)
print("\nProducts with FK -> this supplier:")
for p in Product.objects.filter(supplier=s):
    print("P:", p.id, p.name, "stock=", p.stock_quantity, "purchase_price=", p.purchase_price)

print("\nPurchases whose supplier text contains supplier name:")
for p in Purchase.objects.filter(supplier__icontains=s.name):
    print("Purchase:", p.id, p.timestamp, "supplier_text=", p.supplier, "total_amount=", p.total_amount)

pis = PurchaseItem.objects.filter(Q(purchase__supplier__icontains=s.name) | Q(product__supplier=s)).select_related('purchase','product')
print("\nMatching PurchaseItem lines:", pis.count())
for pi in pis:
    print("PI:", pi.purchase_id, pi.product.id, pi.product.name, "qty=", pi.quantity, "price=", pi.price_at_purchase)

sis = SaleItem.objects.filter(product__supplier=s).select_related('sale','product')
print("\nSaleItem lines for products with FK to this supplier:", sis.count())
for si in sis:
    print("SI:", si.sale_id, si.product.id, si.product.name, "qty=", si.quantity, "price=", si.price_at_sale)

# Totals
pi_total = pis.aggregate(total=Sum(ExpressionWrapper(F('quantity') * F('price_at_purchase'), output_field=DecimalField())))['total'] or 0
si_total = sis.aggregate(total=Sum(ExpressionWrapper(F('quantity') * F('price_at_sale'), output_field=DecimalField())))['total'] or 0
print("\nTotals => PurchaseItem subtotal:", pi_total, "  SaleItem revenue:", si_total)