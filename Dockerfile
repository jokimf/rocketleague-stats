FROM python:alpine3.19
ADD src /src

COPY requirements.txt /
RUN pip install -r requirements.txt

EXPOSE 7823
#CMD [ "flask", "--app", "./src/web.py", "run", "--port", "7823" ]

ENV FLASK_APP .\src\web.py
ENV FLASK_RUNPORT 7823
CMD [ "flask", "--app", "./src/web.py", "run", "--port", "7823" ]