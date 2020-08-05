ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh /
COPY run.py /
RUN apk add --no-cache python3 py3-pip \
	&& pip3 install boto3 \
	&& chmod a+x /run.sh

CMD [ "/run.sh" ]