# Waggle Plugin: RabbitMQ to InfluxDB Bridge

A robust waggle plugin that subscribes to configurable RabbitMQ topics and forwards the messages to a remote InfluxDB database. This plugin provides reliable message routing with automatic reconnection, flexible data transformation, and comprehensive error handling.

## Features

- 🚀 **Configurable Topic Subscriptions**: Subscribe to multiple RabbitMQ exchanges and queues
- 🔄 **Automatic Reconnection**: Robust connection handling with automatic retry logic
- 🏷️ **Flexible Data Mapping**: Transform RabbitMQ messages to InfluxDB points with custom field mappings
- 📊 **Multi-Bucket Support**: Route different topics to different InfluxDB buckets
- 🛡️ **Error Handling**: Graceful error handling with message acknowledgment/rejection
- 📝 **Comprehensive Logging**: Detailed logging with configurable levels
- ⚙️ **YAML Configuration**: Easy-to-read YAML configuration files

## Installation

1. **Clone or download the plugin files:**
   ```bash
   # Ensure you have the following files:
   # - main.py
   # - requirements.txt
   # - config.yaml (example configuration)
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the plugin:**
   ```bash
   # Copy and modify the example configuration
   cp config.yaml my_config.yaml
   # Edit my_config.yaml with your specific settings
   ```

## Configuration

The plugin uses a YAML configuration file that defines:

### Basic Structure

```yaml
logging:
  level: INFO

rabbitmq:
  host: localhost
  port: 5672
  username: guest
  password: guest
  # ... other RabbitMQ settings

influxdb:
  url: http://localhost:8086
  token: your-token-here
  org: your-org
  bucket: default-bucket

topics:
  - exchange: sensor.data
    routing_key: "sensor.*.temperature"
    # ... topic-specific settings
```

### Configuration Sections

#### RabbitMQ Settings
- `host`: RabbitMQ server hostname
- `port`: RabbitMQ server port (default: 5672)
- `username`: Authentication username
- `password`: Authentication password
- `virtual_host`: Virtual host (default: /)
- `heartbeat`: Connection heartbeat interval
- `blocked_connection_timeout`: Timeout for blocked connections

#### InfluxDB Settings
- `url`: InfluxDB server URL
- `token`: InfluxDB authentication token
- `org`: InfluxDB organization name
- `bucket`: Default bucket for data storage
- `timeout`: Connection timeout in milliseconds

#### Topic Configuration
Each topic entry can include:
- `exchange`: RabbitMQ exchange name (optional)
- `exchange_type`: Exchange type (topic, direct, fanout, headers)
- `routing_key`: Message routing pattern (supports wildcards)
- `queue_name`: Queue name (auto-generated if not specified)
- `durable`: Whether queue/exchange should survive server restarts
- `measurement`: InfluxDB measurement name
- `influx_bucket`: Override default InfluxDB bucket
- `tags`: Static tags to add to all points from this topic
- `field_mapping`: Map message fields to InfluxDB field names

## Usage

### Basic Usage

```bash
# Run with default config.yaml
python main.py

# Run with custom configuration file
python main.py --config /path/to/my_config.yaml
```

### Message Format

The plugin supports JSON messages and will attempt to parse them automatically. For non-JSON messages, the content is stored as a `raw_message` field.

#### Example JSON Message
```json
{
  "timestamp": "2023-09-24T12:00:00Z",
  "sensor_id": "temp_001",
  "temperature": 23.5,
  "humidity": 65.2,
  "location": "building_a"
}
```

This would be transformed to an InfluxDB point with:
- **Measurement**: Defined in topic config or derived from routing key
- **Timestamp**: Parsed from message or current time
- **Tags**: From topic config + routing_key, exchange
- **Fields**: temperature, humidity, sensor_id, location

### Data Transformation

#### Field Mapping
Map message fields to different InfluxDB field names:

```yaml
topics:
  - exchange: sensors
    routing_key: "temp.*"
    field_mapping:
      temp_c: temperature_celsius
      temp_f: temperature_fahrenheit
      rh: relative_humidity
```

#### Tags
Add static tags to categorize data:

```yaml
topics:
  - exchange: sensors
    routing_key: "building1.*"
    tags:
      building: building_1
      floor: ground
      department: facilities
```

## Advanced Usage Examples

### Example 1: Weather Station Data
```yaml
topics:
  - exchange: weather
    routing_key: "station.*.measurements"
    queue_name: weather_data_queue
    measurement: weather_readings
    influx_bucket: weather-data
    tags:
      source: weather_station
    field_mapping:
      temp: temperature
      press: pressure
      wind_spd: wind_speed
```

### Example 2: IoT Sensor Network
```yaml
topics:
  - exchange: iot.sensors
    routing_key: "device.*.#"
    measurement: iot_data
    tags:
      network: primary
    field_mapping:
      val: sensor_value
      bat: battery_level
```

### Example 3: Alert System
```yaml
topics:
  - exchange: alerts
    routing_key: "alert.critical.*"
    queue_name: critical_alerts
    measurement: system_alerts
    influx_bucket: alerts
    tags:
      severity: critical
      system: monitoring
```

## Monitoring and Logging

### Log Levels
- `DEBUG`: Detailed debugging information including message contents
- `INFO`: General operational information
- `WARNING`: Warning messages for non-critical issues
- `ERROR`: Error messages for failures

### Log Output Example
```
2023-09-24 12:00:00,123 - rabbitmq-influx-bridge - INFO - Starting RabbitMQ to InfluxDB bridge...
2023-09-24 12:00:01,456 - rabbitmq-influx-bridge - INFO - Successfully connected to RabbitMQ
2023-09-24 12:00:01,789 - rabbitmq-influx-bridge - INFO - Successfully connected to InfluxDB
2023-09-24 12:00:02,012 - rabbitmq-influx-bridge - INFO - Subscribed to topic: exchange=sensors, routing_key=temp.*, queue=temp_queue
```

## Error Handling

The plugin includes robust error handling:

- **Connection Failures**: Automatic reconnection with exponential backoff
- **Message Processing Errors**: Failed messages are rejected and requeued
- **InfluxDB Errors**: Connection issues trigger reconnection attempts
- **Configuration Errors**: Validation and clear error messages

## Graceful Shutdown

The plugin responds to SIGINT (Ctrl+C) and SIGTERM signals:

```bash
# Graceful shutdown
kill -TERM <pid>
# or
Ctrl+C
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify RabbitMQ/InfluxDB services are running
   - Check host/port settings in configuration
   - Verify network connectivity

2. **Authentication Errors**
   - Verify username/password for RabbitMQ
   - Check InfluxDB token and organization settings

3. **Queue/Exchange Not Found**
   - Ensure exchanges exist or set plugin to declare them
   - Check routing key patterns

4. **Data Not Appearing in InfluxDB**
   - Verify bucket names and permissions
   - Check InfluxDB logs for write errors
   - Enable DEBUG logging to see message transformation

### Debug Mode
```bash
# Enable debug logging
python main.py --config config.yaml
# Then edit config.yaml to set logging.level: DEBUG
```

## Requirements

- Python 3.7+
- RabbitMQ server
- InfluxDB 2.0+
- Network connectivity between plugin and both services

## Sage Portal Integration

### Plugin Registration Files

This plugin includes the necessary YAML files for integration with the Sage portal app interface:

#### `sage.yaml` - Plugin Manifest
The main plugin manifest file that defines metadata, configuration parameters, resource requirements, and deployment specifications for the Sage ecosystem.

Key sections:
- **Metadata**: Name, version, description, authors
- **Architecture**: Supported platforms (linux/amd64, linux/arm64)
- **Resources**: CPU/memory requirements and limits
- **Configuration**: User-configurable parameters with types and defaults
- **Science**: Description of scientific measurements and outputs

#### `Dockerfile` - Container Build
Containerization file that:
- Uses waggle base image for compatibility
- Sets appropriate labels for plugin identification
- Installs dependencies and copies application files
- Configures health checks and default command

#### `deployment.yaml` - Kubernetes Deployment
Complete Kubernetes deployment specification including:
- **Deployment**: Pod template with resource limits and health checks
- **ConfigMap**: Configuration management for runtime settings
- **Service**: Network access configuration
- **RBAC**: Service account and permissions for waggle integration

#### `docker-compose.yaml` - Development Environment
Full development stack including:
- RabbitMQ message broker with management UI
- InfluxDB time-series database
- The bridge plugin container
- Optional Grafana for visualization
- Test data generator for validation

### Usage in Sage Portal

1. **Plugin Registration**: Upload the `sage.yaml` manifest to register the plugin in the Sage Edge Code Repository (ECR)

2. **Container Build**: The Sage portal will use the `Dockerfile` to build the plugin container

3. **Deployment**: Use `deployment.yaml` for Kubernetes-based deployments or `docker-compose.yaml` for standalone deployments

4. **Configuration**: Parameters defined in `sage.yaml` config section will appear as configurable options in the portal interface

### Development and Testing

```bash
# Start development environment
docker-compose up -d

# Run with test data generator
docker-compose --profile testing up -d

# Include monitoring dashboard
docker-compose --profile monitoring up -d

# View plugin logs
docker-compose logs -f rabbitmq-influxdb-bridge

# Access services:
# - RabbitMQ Management: http://localhost:15672 (waggle/waggle)
# - InfluxDB: http://localhost:8086 (waggle/waggle-password)
# - Grafana: http://localhost:3000 (admin/waggle)
```

## License

This waggle plugin is provided as-is for waggle ecosystem integration.

## Contributing

To extend or modify the plugin:

1. Review the `RabbitMQToInfluxBridge` class structure
2. Add new features by extending existing methods
3. Test with your specific RabbitMQ and InfluxDB setup
4. Update configuration examples as needed 