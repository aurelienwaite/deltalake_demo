FROM python:3.11-bullseye

COPY requirements.txt /opt/aurelien/requirements.txt
WORKDIR /opt/aurelien
RUN pip install -r requirements.txt

COPY agg_pw.py /opt/aurelien/agg_pw.py

CMD ["pathway", "spawn", "--processes", "1", "--threads", "4", "python", "./agg_pw.py"]