FROM python:alpine
ADD src /src
COPY requirements.txt /
RUN pip install -r requirements.txt
EXPOSE 7823
CMD ["uvicorn", "app:app", "--reload", "--app-dir", "src", "--port", "7823", "--host", "0.0.0.0" ]