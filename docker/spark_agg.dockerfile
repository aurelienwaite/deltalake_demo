FROM spark:python3-java17

USER root
RUN pip install pyarrow==18.1.0 pandas
USER spark