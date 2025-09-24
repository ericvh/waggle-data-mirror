# Use waggle base image for compatibility with the SAGE/Waggle platform
FROM waggle/plugin-base:1.1.1-base

# Set plugin metadata as labels
LABEL sage.plugin.name="rabbitmq-influxdb-bridge"
LABEL sage.plugin.description="RabbitMQ to InfluxDB data bridge with configurable topic subscriptions"
LABEL sage.plugin.version="1.0.0"
LABEL sage.plugin.homepage="https://github.com/waggle-sensor/plugin-rabbitmq-influxdb-bridge"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY config.yaml .

# Create directory for configuration files
RUN mkdir -p /etc/waggle/

# Copy default configuration to expected location
COPY config.yaml /etc/waggle/config.yaml

# Set environment variables for waggle integration
ENV WAGGLE_PLUGIN_NAME="rabbitmq-influxdb-bridge"
ENV WAGGLE_PLUGIN_VERSION="1.0.0"

# Make the main script executable
RUN chmod +x main.py

# Health check to ensure the plugin is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Default command to run the plugin
CMD ["python3", "main.py", "--config", "/etc/waggle/config.yaml"] 