# studentapp/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)     




# from django import template

# register = template.Library()

# @register.filter
# def get_score(table_data, args):
#     batch_id, comp_id = args
#     return table_data.get(batch_id, {}).get(comp_id, "")