FROM fedora:latest
ENV LOOPY_PATH="/home/loopy"
ENV LOOPY_CONFIG_PATH="/home/loopy/config.yaml"
ENV PATH="$PATH:${LOOPY_PATH}:${LOOPY_PATH}/bin"

RUN dnf -y install sudo git wget make python-devel openssl-devel net-tools bind-utils bash-completion python3.10
RUN ln -s /usr/bin/python3 /usr/bin/python
WORKDIR /home

RUN git clone https://github.com/Jooho/loopy.git && \
    cd loopy && \
    make init

# For local test
#COPY loopy /home/loopy
#RUN cd /home/loopy && \
#    make init

CMD /bin/bash
