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
        return '{:,.2f}'.format(v)
    except:
        pass    
        
    return value

def crypto(value)
    try:
        v = float(value)
        return '{:,.8f}'.format(v)
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