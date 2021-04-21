FROM python:3.8 
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY /maps_dashboard/* /maps_dashboard/
CMD ["gunicorn","-b","0.0.0.0:80","-k","uvicorn.workers.UvicornWorker","--forwarded-allow-ips","*","--proxy-allow-from","*","maps_dashboard.app:app"]
