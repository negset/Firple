FROM fedora:39

RUN dnf update -y \
  && dnf install -y \
  fontforge \
  fonttools \
  ttfautohint \
  findutils \
  wget \
  unzip \
  make \
  && dnf clean all

WORKDIR /opt
CMD ["tail","-f","/dev/null"]
