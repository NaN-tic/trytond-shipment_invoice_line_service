from trytond.pool import PoolMeta


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    def _get_invoice_line_quantity(self):
        quantity = super()._get_invoice_line_quantity()

        has_goods = any([l for l in self.sale.lines
            if l.product and l.product.type == 'goods'])
        if (has_goods
                and self.product and self.product.type == 'service'
                and self.sale.shipment_method == 'order'
                and self.sale.invoice_method == 'shipment'):
            shipments_done = [
                s for s in self.sale.shipments if s.state == 'done']
            if shipments_done:
                return quantity
            else:
                return 0
        return quantity
