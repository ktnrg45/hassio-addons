ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh /

RUN apk add iperf3 \
	&& chmod a+x /run.sh

CMD [ "/run.sh" ]