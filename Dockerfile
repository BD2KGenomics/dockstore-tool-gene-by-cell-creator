#############################################################
# Dockerfile to build a sample tool container for BAMStats
#############################################################

# Set the base image to Ubuntu
FROM ubuntu:16.04

RUN apt-get update && apt-get install -y python

# File Author / Maintainer
MAINTAINER Trevor Pesout <tpesout@ucsc.edu>

# Setup packages
USER root

# copy over the script
COPY src/create_gene_by_cell.py /bin/
COPY src/test.sh /bin/
RUN chmod a+x /bin/create_gene_by_cell.py
RUN chmod a+x /bin/test.sh

# init data directory
RUN mkdir /data
WORKDIR /data

CMD ["/bin/bash"]
#ENTRYPOINT ["/bin/create_gene_by_cell.py"]
