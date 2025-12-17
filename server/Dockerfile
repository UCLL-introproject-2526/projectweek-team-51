FROM python:3.11-slim

WORKDIR /app

# Ensure logs flush immediately and no .pyc files are written
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# Copy server code
COPY server.py /app/server.py

# The server listens on this TCP port (see SERVER_PORT in server.py)
EXPOSE 9001

# Run the server
CMD ["python", "server.py"]
