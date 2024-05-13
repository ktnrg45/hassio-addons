ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh /
COPY run.py /
RUN apk add --no-cache python3 py3-pip \
	&& python3 -m venv /venv \
	&& /venv/bin/python3 -m pip install boto3 requests

CMD [ "/run.sh" ]