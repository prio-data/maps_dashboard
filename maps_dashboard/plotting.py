
import math
import textwrap
import io
from matplotlib import pyplot as plt

from pandas import Series

MIMETYPES = {
        "png": "image/png",
        "jpg": "image/jpg",
        "pdf": "application/pdf",
        "ps": "application/postscript",
        "svg": "image/svg+xml"
    }

def plotbytes(fn):
    def inner(*args,**kwargs):
        format = kwargs.get("format")
        format = format if format else "png"
        kwargs = {k:v for k,v in kwargs.items() if k != "format"}

        try:
            mimetype = MIMETYPES[format]
        except KeyError as ke:
            raise NotImplementedError from ke

        bio = io.BytesIO()
        plt.clf()
        fn(*args,**kwargs)
        plt.savefig(bio,format = format)
        return bio.getvalue(),mimetype
    return inner

calcwidth = lambda series: max(6,2.2 * len(series.unique()))
wrap = lambda label: "\n".join(textwrap.wrap(label,16))
nlines = lambda string: len(string.split("\n"))
wrapped = lambda labels: [wrap(lbl) for lbl in labels]

nlwrap = lambda txt,lnsize: "\n".join(textwrap.wrap(txt,lnsize))

def maximizeText(string,width=200,height=100,minsize=8,maxsize=16):
    """
    Try to keep text inside a "box" with a fixed width.
    Returns the text with linebreaks, as well as a recommended font size.
    """
    fontsize = minsize
    calcwidth = lambda string,fontsize: max([len(ln)*fontsize for ln in string.split("\n")])
    linewidth = lambda fontsize: math.floor(width / fontsize)

    cwidth = calcwidth(string,minsize) 
    if cwidth < width:
        while cwidth < width:
            fontsize += 0.1
            cwidth = calcwidth(string,fontsize)
            if fontsize > maxsize:
                fontsize = maxsize
                break
    else:
        string = [string]
        while cwidth > width:
            string = " ".join(string)
            cwidth = calcwidth(string,fontsize)
            string = textwrap.wrap(string,linewidth(fontsize))
            if fontsize < minsize:
                fontsize = minsize
                break
            else:
                fontsize -= 0.1
    return linewidth(fontsize),math.floor(fontsize)
