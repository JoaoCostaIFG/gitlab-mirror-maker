FROM python:3.8-slim as builder

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY mirrormaker /mirrormaker

ENTRYPOINT ["python", "/mirrormaker/mirrormaker.py"]
