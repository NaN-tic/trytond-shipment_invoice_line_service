======================================
Scenario Shipment Invoice Line Service
======================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import Model, Wizard, Report
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Activate Modules::

    >>> config = activate_modules('shipment_invoice_line_service')

Create company::

    >>> _ = create_company()
    >>> company = get_company()
    >>> tax_identifier = company.party.identifiers.new()
    >>> tax_identifier.type = 'eu_vat'
    >>> tax_identifier.code = 'BE0897290877'
    >>> company.party.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> cash = accounts['cash']

    >>> Journal = Model.get('account.journal')
    >>> PaymentMethod = Model.get('account.invoice.payment.method')
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.save()
    >>> payment_method = PaymentMethod()
    >>> payment_method.name = 'Cash'
    >>> payment_method.journal = cash_journal
    >>> payment_method.credit_account = cash
    >>> payment_method.debit_account = cash
    >>> payment_method.save()

Create tax::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create account categories::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.account_revenue = revenue
    >>> account_category.save()

    >>> account_category_tax, = account_category.duplicate()
    >>> account_category_tax.customer_taxes.append(tax)
    >>> account_category_tax.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')

    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.salable = True
    >>> template.account_category = account_category_tax
    >>> template.save()
    >>> product, = template.products
    >>> product.list_price = Decimal('10')
    >>> product.save()

    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.account_category = account_category_tax
    >>> template.save()
    >>> service, = template.products
    >>> service.list_price = Decimal('30')
    >>> service.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line = inventory.lines.new(product=product)
    >>> inventory_line.quantity = 100.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory.click('confirm')
    >>> inventory.state
    'done'

Sale create invoice lines when shipments done (when invoice_method is shipment)::

    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.shipment_method = 'order'
    >>> sale.invoice_method = 'shipment'
    >>> line = sale.lines.new()
    >>> line.product = product
    >>> line.quantity = 10.0
    >>> line.unit_price = Decimal('10')
    >>> line = sale.lines.new()
    >>> line.product = service
    >>> line.quantity = 10.0
    >>> line.unit_price = Decimal('10')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> len(sale.invoices) == 0
    True
    >>> len(sale.shipments) != 0
    True
    >>> shipment, = sale.shipments
    >>> shipment.click('assign_try')
    >>> shipment.click('pick')
    >>> shipment.click('pack')
    >>> shipment.click('do')
    >>> sale.reload()
    >>> invoice, = sale.invoices
    >>> line1, line2 = invoice.lines
    >>> (line1.product.type, line2.product.type) == ('goods', 'service')
    True

Sale create invoice lines when sale is confirmed (when invoice_method is order)::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.shipment_method = 'invoice'
    >>> sale.invoice_method = 'order'
    >>> line = sale.lines.new()
    >>> line.product = product
    >>> line.quantity = 10.0
    >>> line.unit_price = Decimal('10')
    >>> line = sale.lines.new()
    >>> line.product = service
    >>> line.quantity = 10.0
    >>> line.unit_price = Decimal('10')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> len(sale.invoices) == 1
    True
    >>> invoice, = sale.invoices
    >>> line1, line2 = invoice.lines
    >>> (line1.product.type, line2.product.type) == ('goods', 'service')
    True

Sale create invoice lines when shipments return received (when invoice_method is shipment)::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.shipment_method = 'order'
    >>> sale.invoice_method = 'shipment'
    >>> line = sale.lines.new()
    >>> line.product = product
    >>> line.quantity = -10.0
    >>> line.unit_price = Decimal('10')
    >>> line = sale.lines.new()
    >>> line.product = service
    >>> line.quantity = -10.0
    >>> line.unit_price = Decimal('10')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> len(sale.invoices) == 0
    True
    >>> len(sale.shipment_returns) != 0
    True
    >>> shipment, = sale.shipment_returns
    >>> shipment.click('receive')
    >>> shipment.click('do')
    >>> sale.reload()
    >>> invoice, = sale.invoices
    >>> line1, line2 = invoice.lines
    >>> (line1.product.type, line2.product.type) == ('goods', 'service')
    True
