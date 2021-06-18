FROM retroarcher/retroarcher-baseimage:python3

LABEL maintainer="RetroArcher"

ARG BRANCH
ARG COMMIT

ENV RETROARCHER_DOCKER=True
ENV TZ=UTC

WORKDIR /app

RUN \
  groupadd -g 1000 retroarcher && \
  useradd -u 1000 -g 1000 retroarcher && \
  echo ${BRANCH} > /app/branch.txt && \
  echo ${COMMIT} > /app/version.txt

COPY . /app

CMD [ "python", "RetroArcher.py", "--datadir", "/config" ]
ENTRYPOINT [ "./start.sh" ]

VOLUME /config
EXPOSE 9696
HEALTHCHECK --start-period=90s CMD curl -ILfSs http://localhost:9696/status > /dev/null || curl -ILfkSs https://localhost:9696/status > /dev/null || exit 1
