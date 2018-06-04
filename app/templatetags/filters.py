from django.template.defaultfilters import register

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
        
    return ''