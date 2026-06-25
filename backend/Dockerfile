FROM python:3.13

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY app app
COPY alembic alembic
COPY alembic.ini .

EXPOSE 8000

RUN chmod +x app/entrypoint.sh

ENTRYPOINT [ "app/entrypoint.sh" ]
CMD [ "--host", "0.0.0.0", "--port", "8000" ]
