FROM python:3.11

# Set working directory
WORKDIR /code

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
