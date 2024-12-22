FROM python:3.13.1-bullseye

RUN pip install pyarrow==18.1.0 polars==1.17.1 deltalake==0.22.3