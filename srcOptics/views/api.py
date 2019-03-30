from django.http import *
from django.core import serializers

from ..models import *

"""
Returns a list of Repository objects by search query
that matches repo names or tag objects
"""
def search(request, query):
    repos = None
    if not query:
        repos = Repository.objects.all()
    else:
        repos = Repository.objects.filter(name__icontains=query)
        tag_query = Tag.objects.filter(name__icontains=query)
        for tag in tag_query:
            repos |= tag.repos.all()
    data = serializers.serialize('json',repos)
    return HttpResponse(data, content_type='application/json')
