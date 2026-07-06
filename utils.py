import re
from typing import Dict, Any, Tuple

NA_VALUE = "N/A"


def is_na(value: str) -> bool:
    return isinstance(value, str) and value.strip().upper() == NA_VALUE


def validate_input(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate user input for security and data integrity
    Returns (is_valid, error_message)
    """

    # Check required fields
    if not data.get('brand', '').strip():
        return False, "Brand is required"

    if not data.get('item_type', '').strip():
        return False, "Item type is required"

    # Validate brand (alphanumeric + spaces + common punctuation)
    brand = data.get('brand', '').strip()
    if not is_na(brand) and (len(brand) > 50 or not re.match(r"^[a-zA-Z0-9\s\-'&.]+$", brand)):
        return False, "Brand contains invalid characters or is too long"

    # Validate item type
    item_type = data.get('item_type', '').strip()
    if not is_na(item_type) and (len(item_type) > 50 or not re.match(r"^[a-zA-Z0-9\s\-]+$", item_type)):
        return False, "Item type contains invalid characters or is too long"

    # Validate size (optional)
    size = data.get('size', '').strip()
    if size and not is_na(size) and (len(size) > 10 or not re.match(r"^[a-zA-Z0-9\s\-]+$", size)):
        return False, "Size contains invalid characters or is too long"

    # Validate color (optional)
    color = data.get('color', '').strip()
    if color and not is_na(color) and (len(color) > 30 or not re.match(r"^[a-zA-Z0-9\s\-]+$", color)):
        return False, "Color contains invalid characters or is too long"

    # Validate material (optional)
    material = data.get('material', '').strip()
    if material and not is_na(material) and (len(material) > 50 or not re.match(r"^[a-zA-Z0-9\s\-,]+$", material)):
        return False, "Material contains invalid characters or is too long"

    # Validate condition
    condition = data.get('condition', '').strip().lower()
    if condition not in ['new', 'used', '', 'n/a']:
        return False, "Condition must be 'new', 'used', or 'N/A'"
    
    # Validate user price (optional)
    user_price = data.get('user_price')
    if user_price:
        try:
            price = float(user_price)
            if price < 0 or price > 100000:  # Reasonable price range
                return False, "Price must be between $0 and $100,000"
        except (ValueError, TypeError):
            return False, "Price must be a valid number"
    
    return True, ""

def sanitize_input(text: str) -> str:
    """
    Sanitize text input by removing potentially dangerous characters
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Strip and limit length
    text = text.strip()[:200]  # Max 200 characters
    
    return text

def format_price(price: float) -> str:
    """
    Format price for display
    """
    try:
        return f"${price:.2f}"
    except (ValueError, TypeError):
        return "N/A"

def extract_price_from_text(text: str) -> float:
    """
    Try to extract price from API response text
    """
    if not text:
        return None
    
    # Look for price patterns like $12.34, $1,234.56, etc.
    price_patterns = [
        r'\$([\\d,]+\\.\\d{2})',  # $12.34, $1,234.56
        r'\$([\\d,]+)',          # $123
        r'([\\d,]+\\.\\d{2})\\s*(?:USD|dollars?)',  # 12.34 USD
        r'([\\d,]+)\\s*(?:USD|dollars?)',         # 123 USD
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                # Remove commas and convert to float
                price_str = matches[0].replace(',', '')
                return float(price_str)
            except ValueError:
                continue
    
    return None