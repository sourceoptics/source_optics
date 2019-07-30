# contributor note: the django UI will be eventually replaced by a new dynamic frontend speaking to the REST API, do not add features

import plotly.offline as opy
from plotly import tools
from .. import v1_graph


class RepositoryGraph:
    def __init__(self, **kwargs):
        self.repos = kwargs['repos']
        self.start = kwargs['q']['start']
        self.end = kwargs['q']['end']
        self.attribute = kwargs['q']['attribute']
        self.interval = kwargs['q']['interval']
        self.page = int(kwargs['q']['page'])
        self.range = 5



    def attributes_by_repo(self):

        p_start = (self.page-1) * self.range
        if len(self.repos) < self.range * self.page:
            diff = len(self.repos) - p_start
            p_end  = p_start + diff
            #p_end = p_start + (self.range * self.page) - len(self.repos) + 1
        else:
            p_end = p_start + self.range

        print(p_start)
        print(p_end)

        if len(self.repos) == 0:
            return None

        print(self.repos)

        figure = tools.make_subplots(
            rows=self.range,
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.1,
            subplot_titles=tuple([_.name for _ in self.repos[p_start:p_end]]),
        )


        # Iterate over repo queryset, generating attribute graph for each
        print(p_start, p_end)
        for i in range(p_start, p_end):
            figure = v1_graph.generate_graph_data(
                figure=figure,
                repo=self.repos[i],
                name=self.repos[i].name,
                start=self.start,
                end=self.end,
                attribute=self.attribute,
                interval=self.interval,
                row=i-p_start+1,
                col=1
            )
        figure['layout'].update(height=1000)

        data = opy.plot(figure, auto_open=False, output_type='div')

        return data
