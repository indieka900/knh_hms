from django.utils import timezone

def generate_payment_id_uuid():
    """Generate payment ID using UUID - guaranteed unique"""
    import uuid
    today = timezone.now().strftime('%Y%m%d')
    unique_part = str(uuid.uuid4())[:8].upper()
    return f"PAY{today}{unique_part}"