from django.template.defaultfilters import register
from django.contrib.auth.models import Group

@register.filter(name='lookup')
def lookup(dict, index):
    if index in dict:
        return dict[index]
    return ''

@register.filter(name='currency')
def currency(value):
    try:
        v = float(value)
        strValue = '{:,.2f}'.format(v)
        
        return strValue if strValue != "0.00" else crypto(value)
    except:
        pass    
        
    return value

@register.filter(name='crypto')
def crypto(value):
    try:
        v = float(value)
        strValue = '{:,.8f}'.format(v)
        return strValue if strValue != "0.00000000" else str(value)
    except:
        pass
        
    return value

@register.filter(name='has_group')
def has_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
        return group in user.groups.all()
    except:
        return False

@register.filter(name='zip')
def zip_lists(a, b):
  return zip(a, b)