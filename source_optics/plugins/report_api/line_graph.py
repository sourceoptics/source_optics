class Plugin(object):

    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):
        return dict(ok=1)


INFO = """

        stats_set = Statistic.objects.filter(
            interval=interval,
            repo=kwargs['repo'],
            author=author,
            start_date__range=(start, end)
        ).order_by('start_date')
        
"""
