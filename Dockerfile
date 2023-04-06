FROM python:3.8
ARG TOKEN
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y libgl1
RUN pip install -U pip

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt --extra-index-url https://$TOKEN@pkgs.dev.azure.com/LiquidStudiosBrazil/139e3811-b61c-447b-9ab0-4c6d8a4d9008/_packaging/aiv/pypi/simple

ENTRYPOINT ["tail", "-f", "/dev/null"]
