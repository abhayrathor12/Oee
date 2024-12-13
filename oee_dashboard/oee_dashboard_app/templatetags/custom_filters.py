from django import template

register = template.Library()


@register.filter
def replace_underscores(value):
    return value.replace("_", " ")


@register.filter
def get_attribute(obj, field_name):
    return getattr(obj, field_name, None)


@register.filter
def get_dict_value(dictionary, key):
    """Custom filter to access dictionary values by key."""
    return dictionary.get(key, None)


@register.filter
def group_fields(data, n):
    """
    Group dictionary or list into chunks of n
    Usage: {{ fields|group_fields:2 }}
    """
    if isinstance(data, dict):
        # For dictionaries, convert to list of tuples first
        items = list(data.items())
        return [dict(items[i : i + n]) for i in range(0, len(items), n)]
    elif isinstance(data, list):
        # For lists, use standard list grouping
        return [data[i : i + n] for i in range(0, len(data), n)]
    return data
