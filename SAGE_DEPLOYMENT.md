# Sage Portal Deployment Guide

This guide provides step-by-step instructions for deploying the RabbitMQ to InfluxDB Bridge plugin through the Sage portal app interface.

## Prerequisites

- Access to Sage portal with plugin deployment permissions
- Valid RabbitMQ and InfluxDB server endpoints
- Authentication credentials for both services

## Files for Portal Integration

The following files are required for Sage portal integration:

### Core Files
- `sage.yaml` - Plugin manifest and configuration schema
- `Dockerfile` - Container build instructions
- `main.py` - Main plugin application
- `requirements.txt` - Python dependencies
- `config.yaml` - Default configuration template

### Deployment Files
- `deployment.yaml` - Kubernetes deployment specification
- `docker-compose.yaml` - Development environment setup

### Testing Files
- `test-data-generator.py` - Test data generator for validation

## Step-by-Step Deployment

### 1. Plugin Registration

1. **Access Sage Portal**: Log into the Sage portal with appropriate credentials

2. **Navigate to Plugin Registry**: Go to the Edge Code Repository (ECR) section

3. **Upload Plugin Manifest**: 
   - Upload the `sage.yaml` file
   - Verify that all metadata fields are correctly populated
   - Ensure configuration parameters are properly defined

4. **Review Plugin Details**:
   - Check plugin name: `rabbitmq-influxdb-bridge`
   - Verify version: `1.0.0`
   - Confirm resource requirements are acceptable

### 2. Configuration Setup

Configure the following parameters through the portal interface:

#### RabbitMQ Settings
- **Host**: Your RabbitMQ server hostname/IP
- **Port**: RabbitMQ AMQP port (default: 5672)
- **Username**: Authentication username
- **Password**: Authentication password (marked as sensitive)
- **Virtual Host**: RabbitMQ virtual host (default: /)

#### InfluxDB Settings
- **URL**: InfluxDB server URL (e.g., http://your-influx-server:8086)
- **Token**: InfluxDB authentication token (marked as sensitive)
- **Organization**: InfluxDB organization name
- **Bucket**: Default bucket for data storage

#### Plugin Settings
- **Logging Level**: DEBUG, INFO, WARNING, or ERROR
- **Topics Configuration**: Customize via the config.yaml file

### 3. Deployment Options

#### Option A: Kubernetes Deployment (Recommended)

1. **Upload Deployment Spec**: Use the provided `deployment.yaml`
2. **Configure Secrets**: Set up Kubernetes secrets for sensitive credentials
3. **Deploy to Cluster**: Deploy through the Sage portal's Kubernetes interface
4. **Monitor Status**: Check pod status and logs through the portal

#### Option B: Docker Compose Deployment

1. **Development/Testing**: Use `docker-compose.yaml` for standalone deployments
2. **Local Testing**: Suitable for development and testing environments

### 4. Topic Configuration

Customize the message routing by editing the topics section in your deployment:

```yaml
topics:
  - exchange: your.sensor.exchange
    routing_key: "sensor.*.measurements"
    queue_name: your_sensor_queue
    measurement: sensor_data
    influx_bucket: sensor-data
    tags:
      source: your_source
      location: your_location
    field_mapping:
      temp: temperature
      humid: humidity
```

### 5. Validation and Testing

#### Pre-deployment Testing
1. **Test Data Generator**: Use `test-data-generator.py` to validate the setup
2. **Local Environment**: Run the full stack with `docker-compose up`
3. **Verify Data Flow**: Check that data appears in InfluxDB

#### Post-deployment Validation
1. **Monitor Logs**: Check plugin logs for connection and processing status
2. **Verify Data**: Confirm data is being written to InfluxDB
3. **Check Performance**: Monitor resource usage and message throughput

### 6. Monitoring and Maintenance

#### Health Checks
- The plugin includes built-in health checks
- Monitor through Sage portal dashboards
- Set up alerts for connection failures

#### Log Analysis
```bash
# View plugin logs
kubectl logs -f deployment/rabbitmq-influxdb-bridge -n waggle-plugins

# Monitor message processing
kubectl logs deployment/rabbitmq-influxdb-bridge -n waggle-plugins | grep "Successfully forwarded"
```

#### Performance Monitoring
- CPU usage: Should remain under 50% under normal load
- Memory usage: Typically 128-256 MB depending on message volume
- Message throughput: Monitor processed messages per second

## Troubleshooting

### Common Issues

#### Connection Problems
- **RabbitMQ Connection Failed**: Verify host, port, and credentials
- **InfluxDB Authentication Error**: Check token and organization settings
- **Network Connectivity**: Ensure firewall rules allow connections

#### Data Flow Issues
- **No Data in InfluxDB**: Check exchange and routing key configuration
- **Message Processing Errors**: Review logs for JSON parsing issues
- **Queue Buildup**: Monitor queue lengths in RabbitMQ management interface

#### Resource Issues
- **High Memory Usage**: Increase memory limits in deployment spec
- **CPU Throttling**: Adjust CPU limits or optimize message processing
- **Disk Space**: Monitor InfluxDB storage usage

### Debug Mode

Enable debug logging for detailed troubleshooting:

```yaml
config:
  logging_level: "DEBUG"
```

This will provide detailed information about:
- Connection attempts and failures
- Message processing and transformation
- InfluxDB write operations
- Error conditions and retries

## Advanced Configuration

### Custom Field Mappings

Define how RabbitMQ message fields map to InfluxDB fields:

```yaml
field_mapping:
  source_field: target_field
  temperature_c: temperature_celsius
  rh_percent: relative_humidity
```

### Multiple InfluxDB Buckets

Route different message types to different buckets:

```yaml
topics:
  - exchange: sensor.data
    influx_bucket: sensor-measurements
  - exchange: alerts
    influx_bucket: system-alerts
```

### High Availability

For production deployments:
- Use multiple plugin replicas
- Configure persistent volumes for logs
- Set up monitoring and alerting
- Implement backup strategies for InfluxDB

## Support and Documentation

- **Plugin Repository**: [GitHub Link]
- **Sage Documentation**: [Sage Portal Docs]
- **Issue Tracking**: Use GitHub issues for bug reports
- **Community Support**: Waggle community forums

## Security Considerations

- Store sensitive credentials (passwords, tokens) in Kubernetes secrets
- Use TLS/SSL for RabbitMQ and InfluxDB connections where possible
- Regularly rotate authentication tokens
- Monitor for unauthorized access attempts 