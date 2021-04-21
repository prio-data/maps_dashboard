
from contextlib import closing
import textwrap

from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import contextily

from . import plotting,orm

@plotting.plotbytes
def hist(data,variable=None,keepna=False,floor=0):
    """
    Plotting function.
    """
    if not variable:
        variable = data.columns[0]

    with closing(orm.get_session()) as sess:
        vdict = orm.getdict(variable,sess)
        description = orm.getdescr(variable,sess)

    data = data[variable].value_counts().reset_index()
    data = data[data[variable]>floor]
    data[variable] = (data[variable] / data[variable].sum())

    vdict = {k:v for k,v in vdict.items() if v in data["index"].values}
    data["index"] = data["index"].apply(plotting.wrap)
    vdict = {k:plotting.wrap(v) for k,v in vdict.items()}

    if not keepna:
        vdict = {k:v for k,v in vdict.items() if k>=0}


    fig,ax = plt.subplots()
    sns.barplot(
            x = data["index"],
            y = data[variable],
            ax = ax,
            order = vdict.values()
        )
    
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    plt.title("\n".join(textwrap.wrap(description,60)))
    plt.xlabel("")
    plt.ylabel("")
    plt.subplots_adjust(top=0.85,bottom=0.15)
    fig.set_size_inches(plotting.calcwidth(data[variable]),6)

@plotting.plotbytes
def count(data,v1,v2,keepna,floor,pst=False,incat=False):

    data = data.groupby(v1)[v2].value_counts()
    data = data[data > floor]

    if pst:
        if incat:
            data = data.groupby(level=0).apply(lambda x: (x / x.sum()))
        else:
            tot_n = data.sum()
            data = data.groupby(level=0).apply(lambda x: (x / tot_n))

    data.name = "count" 
    data = data.reset_index()

    with closing(orm.get_session()) as sess:
        dicts = {}
        for v in v1,v2:
            data[v] = orm.withmeta(data[v],sess)
            dicts[v] = orm.getdict(v,sess)

        v1d,v2d = (orm.getdescr(v,sess) for v in (v1,v2))

    if not keepna:
        rmna = lambda d: {k:v for k,v in d.items() if k >= 0}
        dicts = {k:rmna(v) for k,v in dicts.items()}

    dicts[v1] = {k:v for k,v in dicts[v1].items() if v in data[v1].values}

    fig,ax = plt.subplots()
    sns.barplot(
            data = data, 
            x = v1, y = "count", hue = v2, ci = "sd",
            order = dicts[v1].values(),
            hue_order = dicts[v2].values(),
            ax = ax
        )
    ax.set_xticklabels(plotting.wrapped(dicts[v1].values()))

    if pst:
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    plt.title(plotting.nlwrap(v1d,50))

    legend = plt.legend(title=plotting.nlwrap(v2d,20),frameon = False,loc=2,bbox_to_anchor=(1.,1))
    ttl = legend.get_title()
    ttl.set_multialignment("center")

    for txt in legend.get_texts():
        txt.set_text(plotting.nlwrap(txt.get_text(),15))

    width = plotting.calcwidth(data[v1])
    fig.set_size_inches(width,6)
    plt.subplots_adjust(right=0.7,bottom=0.15)
    plt.xlabel("")
    plt.ylabel("")

@plotting.plotbytes
def mean(data,v1,v2,keepna,floor:int=0):
    if not keepna:
        for v in v1,v2:
            data = data[data[v] > 0]

    with closing(orm.get_session()) as sess:
        data[v1] = orm.withmeta(data[v1],sess)
        vdict = orm.getdict(v1,sess)
        v1d,v2d = (orm.getdescr(v,sess) for v in (v1,v2))

    minval,maxval = data[v2].min(),data[v2].max()

    if not keepna:
        vdict = {k:v for k,v in vdict.items() if k > 0}

    fig,ax = plt.subplots(figsize=(3,3))

    sns.barplot(
            data = data,
            x=v1,y=v2,
            ax = ax,
            order = vdict.values(),
        )

    ax.set_xticklabels(plotting.wrapped(vdict.values()))
    fig.set_size_inches(plotting.calcwidth(data[v1]),6)
    fig.subplots_adjust(left=0.20)
    fig.text(0.06,0.5,plotting.nlwrap(v2d+" (mean)",25),rotation="vertical",va="center",ha="center")
    plt.title(v1d)
    plt.ylim(minval,maxval)
    plt.xlabel("")
    plt.ylabel("")

@plotting.plotbytes
def map(geodata,scalemin,scalemax):
    geodata = geodata.to_crs(epsg=3857)
    fig,ax = plt.subplots()
    geodata.plot(column = "var",ax=ax,alpha=0.8,
            legend=True,vmin=scalemin,vmax=scalemax)
    contextily.add_basemap(ax,
            source=contextily.providers.Stamen.TonerLite)
    fig.set_size_inches((6.5,8))
