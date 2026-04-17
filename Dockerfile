FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# Seed demo data on first run
RUN python -m promptqa.seed

EXPOSE 8000

CMD ["promptqa", "serve", "--host", "0.0.0.0"]
