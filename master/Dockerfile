FROM postgres:12
COPY ./replicant/requirenments.txt /python-requirements/requirements.txt
RUN set -ex; \
    apt-get -o Acquire::ForceIPv4=true update ; \
    savedAptMark="$(apt-mark showmanual)" ; \
    apt-get update ; \
    apt-get install -y python3 python3-pip; \
    pip3 install --no-cache-dir -r ./python-requirements/requirements.txt

ENV APP_DIR /opt/replicant
WORKDIR $APP_DIR

COPY replicant $APP_DIR/replicant
COPY master/setup-master.sh /docker-entrypoint-initdb.d/setup-master.sh
RUN chmod +x /docker-entrypoint-initdb.d/setup-master.sh
CMD ["python3", "-m", "replicant.main"]
