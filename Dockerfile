FROM registry.drycc.cc/drycc/base:bullseye

ENV DRYCC_UID=1001 \
  DRYCC_GID=1001 \
  DRYCC_HOME_DIR=/data \
  PYTHON_VERSION="3.10.6" \
  PROMETHEUS_VERSION="2.40.3" \
  PUSHGATEWAY_VERSION="1.5.1" \
  NODE_EXPORTER_VERSION="1.4.0" \
  KUBE_STATE_METRICS="2.7.0" \
  CONFIGMAP_RELOAD="0.8.0"


COPY . /

RUN groupadd drycc --gid ${DRYCC_GID} \
  && useradd drycc -u ${DRYCC_UID} -g ${DRYCC_GID} -s /bin/bash -m -d ${DRYCC_HOME_DIR} \
  && install-stack python $PYTHON_VERSION \
  && install-stack prometheus $PROMETHEUS_VERSION \
  && install-stack pushgateway $PUSHGATEWAY_VERSION \
  && install-stack node_exporter $NODE_EXPORTER_VERSION \
  && install-stack kube-state-metrics $KUBE_STATE_METRICS \
  && install-stack configmap-reload $CONFIGMAP_RELOAD \
  && . init-stack \
  && set -eux; pip3 install --disable-pip-version-check -r requirements.txt 2>/dev/null; set +eux \
  && chmod +x /usr/local/bin/start-proxy.py /usr/local/bin/start-backend.sh \
  && rm -rf \
      /usr/share/doc \
      /usr/share/man \
      /usr/share/info \
      /usr/share/locale \
      /var/lib/apt/lists/* \
      /var/log/* \
      /var/cache/debconf/* \
      /etc/systemd \
      /lib/lsb \
      /lib/udev \
      /usr/lib/`echo $(uname -m)`-linux-gnu/gconv/IBM* \
      /usr/lib/`echo $(uname -m)`-linux-gnu/gconv/EBC* \
      /var/cache/apk/* /root/.gem/ruby/*/cache/*.gem \
  && bash -c "mkdir -p /usr/share/man/man{1..8}"

VOLUME ${DRYCC_HOME_DIR}

USER ${DRYCC_UID}

# Expose the gateway port
EXPOSE 8000
