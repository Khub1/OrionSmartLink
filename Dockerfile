# Use a slim Python 3.9 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install tzdata and ODBC driver dependencies
RUN apt-get update && \
    apt-get install -y \
    tzdata \
    gnupg2 \
    curl \
    unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set timezone to America/Argentina/Buenos_Aires
ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    # Verify timezone
    date

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Ensure Python output is not buffered
ENV PYTHONUNBUFFERED=1

# Expose port 8000
EXPOSE 8000

# Run Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]