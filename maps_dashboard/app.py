import contextlib
import logging
import json
import importlib

from fastapi import FastAPI,Response
from sqlalchemy.exc import ProgrammingError
import pandas as pd
import geopandas as gpd
import jinja2
from shapely import wkt

from . import orm, plots, util

logger = logging.getLogger(__name__)
app = FastAPI() 

tpl_env = jinja2.Environment(
    loader = jinja2.PackageLoader("maps_dashboard","."),
    autoescape = jinja2.select_autoescape(["html"])
)

@app.get("/hist/{vname:str}")
def resolve_hist(vname:str, fmt:str="png", floor:int=0):
    with contextlib.closing(orm.connect()) as con:
        try:
            df = orm.getvar(vname,con)
        except ProgrammingError: 
            return Response(status_code=404)

    with contextlib.closing(orm.get_session()) as sess:
        df[vname] = orm.withmeta(df[vname],sess)

    try:
        plotbytes, mimetype = plots.hist(df,floor=floor,format=fmt)
    except NotImplementedError:
        return Response(status_code=400)
    return Response(plotbytes, media_type=mimetype)

@app.get("/comp/{v1}/{v2}/{plottype}")
def resolve_comp(v1:str,v2:str,plottype:str="count",incat:bool=False,keepna=False,floor:int=0,fmt:str="png"):
    FUNCTIONS ={
            "count": plots.count,
            "mean": plots.mean,
            "pst": lambda *args,**kwargs: plots.count(*args,**kwargs,pst=True),
            "grppst": lambda *args,**kwargs: plots.count(*args,**kwargs,pst=True,incat=True)
        }

    with contextlib.closing(orm.connect()) as con:
        try:
            df = orm.getvar(v1,con).join(orm.getvar(v2,con))
        except ProgrammingError: 
            return Response(status_code=404)

    plotbytes,mimetype = FUNCTIONS[plottype](df,v1,v2,keepna=keepna,floor=floor,format=fmt)

    return Response(plotbytes, media_type=mimetype)

@app.get("/map/{variable}/{plottype}/{arg}")
def resolve_map(variable:str, plottype:str, arg:int, fmt:str="png"):
    with contextlib.closing(orm.connect()) as con:
        san = util.sanitizeVarname(variable)
        data = pd.read_sql(
                f"SELECT {san} "
                f"AS var, pdet FROM data WHERE {san} > -1",
                con)
        scalemin,scalemax = data["var"].min(),data["var"].max()

        geodata = pd.read_sql("SELECT * FROM geodata",con)
        geodata["geometry"] = geodata["geostring"].apply(wkt.loads)
        geodata = gpd.GeoDataFrame(geodata,geometry="geometry")
        geodata = geodata.set_crs("epsg:4326")

    base = data.copy()
    try:
        if plottype == "eq":
            data["isval"] = data["var"] == arg 
        elif plottype == "gt":
            data["isval"] = data["var"] > arg 
        else:
            raise KeyError

        data = (data[["pdet","isval"]]
                .groupby("pdet")
                .agg(["sum","count"])
            )

        data.columns = data.columns.droplevel(0)
        data = data.reset_index()
        data["var"] = (data["sum"] / data["count"])*100
        scalemin,scalemax = 0,100
    except KeyError:
        data = base.groupby("pdet").mean() 

    geodata = geodata.merge(data,on="pdet")

    picbytes,mimetype = plots.map(geodata,scalemin,scalemax,format=fmt)
    return Response(picbytes,media_type=mimetype)

@app.get("/")
def resolve_dash():
    with contextlib.closing(orm.get_session()) as sess:
        variables = sess.query(orm.Variable).filter(orm.Variable.description!="NaN")

    plottypes = [
            {"name":"Histogram",
                "path":"hist/%s?floor=%s","needs":["v1","param"]},

            {"name":"Comparison means",
                "path":"comp/%s/%s/mean","needs":["v1","v2"]},

            {"name":"Comparison percentages",
                "path":"comp/%s/%s/pst?floor=%s","needs":["v1","v2","param"]},

            {"name":"Group comp. percentages",
                "path":"comp/%s/%s/grppst?floor=%s","needs":["v1","v2","param"]},

            {"name":"Comparison counts",
                "path":"comp/%s/%s/count?floor=%s","needs":["v1","v2","param"]},

            {"name":"Map mean",
                "path":"map/%s/mean/0","needs":["v1"]},

            {"name":"Map percent equals",
                "path":"map/%s/eq/%s","needs":["v1","param"]}
        ]

    descriptions = json.loads(importlib.resources.read_text("maps_dashboard","dash_descriptions_esp.json"))
    for plottype in plottypes:
        plottype["description"] = descriptions[plottype["name"]]

    formats = [
            {"name":"png","ext":"png"},
            {"name":"postscript","ext":"ps"},
            {"name":"pdf","ext":"pdf"},
            {"name":"svg","ext":"svg"},
        ]

    html = tpl_env.get_template("dash.html").render(
                variables = variables,
                plottypes = plottypes,
                formats = formats,
                json = json
            )

    return Response(html, media_type="text/html")
