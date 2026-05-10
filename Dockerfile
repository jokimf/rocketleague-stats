FROM python:alpine
ADD src /src
ADD rrrocket /rrrocket
RUN chmod -R u+x /rrrocket
COPY requirements.txt /
RUN pip install -r requirements.txt
EXPOSE 7823
CMD ["uvicorn", "app:app", "--app-dir", "src", "--port", "7823", "--host", "0.0.0.0" ]