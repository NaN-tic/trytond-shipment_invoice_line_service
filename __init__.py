# This file is part shipment_invoice_line_service module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import sale

def register():
    Pool.register(
        sale.SaleLine,
        module='shipment_invoice_line_service', type_='model')

