# contributor note: the django UI will be eventually replaced by a new dynamic frontend speaking to the REST API, do not add features


from django import template

register = template.Library()

@register.simple_tag
def query_url(items, key, value):
    url = '?'
    for k, v in items:
        if k != key:
            url += k + '=' + v + '&'
    url += key + '=' + str(value)

    return url
