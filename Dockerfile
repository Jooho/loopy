FROM fedora:latest
ENV LOOPY_ROOT_PATH="/home/loopy"
ENV PYTHONPATH="${LOOPY_ROOT_PATH}/src"
ENV LOOPY_CONFIG_FILE="config.yaml"
ENV PATH="$PATH:${LOOPY_ROOT_PATH}:${LOOPY_ROOT_PATH}/bin"

RUN dnf -y install sudo git wget make python-devel openssl-devel net-tools bind-utils bash-completion python3.11 which procps gettext
RUN ls -l /usr/bin/python || ln -s /usr/bin/python3 /usr/bin/python


WORKDIR /home

#RUN git clone https://github.com/Jooho/loopy.git && \
#    cd loopy && \
#    make init

# For local test
COPY ./ /home/loopy
RUN cd /home/loopy && \
    make init

#RUN groupadd -g 1000 loopy && \
#    useradd -u 1000 -g 1000 loopy && \
#    echo "loopy:1000:708061870" > /etc/subgid && \
#    echo "loopy:1000:708061870" > /etc/subuid

# Change ownership of necessary directories
#RUN chown -R 1000:1000 /home/loopy && \
#    chmod -R 775 /home/loopy

#USER 1000

CMD ["/bin/bash"]
