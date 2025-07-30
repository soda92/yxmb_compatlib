def format_value(value, decimal_places):
    if not value:
        return ''
    try:
        num = float(value)
    except (ValueError, TypeError):
        return ''
    if decimal_places == 0:
        return str(int(round(num)))
    else:
        return str(round(num, decimal_places))
