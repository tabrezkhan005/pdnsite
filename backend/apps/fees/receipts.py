from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import Receipt


def generate_receipt_pdf(payment):
    """
    Generates a PDF receipt for a successful payment and saves it to a new Receipt model.
    """
    # Create receipt record first to get the number
    receipt = Receipt.objects.create(
        payment=payment,
        student=payment.student,
        amount_paise=payment.amount_paise
    )

    # Prepare context
    allocations = payment.allocations.select_related('invoice').all()
    context = {
        'receipt': receipt,
        'payment': payment,
        'student': payment.student,
        'guardian': getattr(payment.student, 'guardian', None),
        'allocations': allocations,
    }

    html_string = render_to_string('fees/receipt.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()

    filename = f"Receipt_{receipt.receipt_number.replace('/', '_')}.pdf"
    receipt.pdf_file.save(filename, ContentFile(pdf_bytes))
    return receipt
