"""Desglose solicitado: IVA suma e ISR retenido resta, ambos sobre subtotal."""
from decimal import Decimal, ROUND_HALF_UP


def amounts(subtotal,vat_bp=0,isr_bp=0):
    if type(subtotal) is not int or subtotal<0:
        raise ValueError('El subtotal debe ser centavos enteros no negativos.')
    vat=int((Decimal(subtotal)*Decimal(vat_bp)/10000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    isr=int((Decimal(subtotal)*Decimal(isr_bp)/10000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    return {'subtotal_cents':subtotal,'vat_bp':vat_bp,'isr_bp':isr_bp,'vat_cents':vat,'isr_cents':isr,'total_cents':subtotal+vat-isr}


def percent(basis_points):
    return f'{basis_points/100:g}%'
