FROM python:3.8-slim

WORKDIR /app
COPY . /app
RUN pip --no-cache-dir install -r requirements.txt
# Make port 80 available to the world outside this container
EXPOSE 5001

# Define environment variable
ENV OPENAI_API_KEY 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
CMD ["python3", "server.py"]
