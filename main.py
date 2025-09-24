#!/usr/bin/env python3
"""
Waggle Plugin: RabbitMQ to InfluxDB Bridge

This plugin subscribes to configurable RabbitMQ topics and rebroadcasts
the messages to a remote InfluxDB database.
"""

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import pika
import yaml
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class RabbitMQToInfluxBridge:
    """Main bridge class for RabbitMQ to InfluxDB data forwarding."""
    
    def __init__(self, config_path: str):
        """Initialize the bridge with configuration."""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.running = True
        
        # RabbitMQ connection
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        
        # InfluxDB client
        self.influx_client = None
        self.write_api = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Error: Configuration file {config_path} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format
        )
        
        logger = logging.getLogger('rabbitmq-influx-bridge')
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _connect_rabbitmq(self) -> bool:
        """Establish connection to RabbitMQ."""
        try:
            rabbitmq_config = self.config['rabbitmq']
            
            # Create connection parameters
            credentials = pika.PlainCredentials(
                rabbitmq_config.get('username', 'guest'),
                rabbitmq_config.get('password', 'guest')
            )
            
            parameters = pika.ConnectionParameters(
                host=rabbitmq_config.get('host', 'localhost'),
                port=rabbitmq_config.get('port', 5672),
                virtual_host=rabbitmq_config.get('virtual_host', '/'),
                credentials=credentials,
                heartbeat=rabbitmq_config.get('heartbeat', 600),
                blocked_connection_timeout=rabbitmq_config.get('blocked_connection_timeout', 300)
            )
            
            self.rabbitmq_connection = pika.BlockingConnection(parameters)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            
            self.logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def _connect_influxdb(self) -> bool:
        """Establish connection to InfluxDB."""
        try:
            influx_config = self.config['influxdb']
            
            self.influx_client = InfluxDBClient(
                url=influx_config['url'],
                token=influx_config['token'],
                org=influx_config['org'],
                timeout=influx_config.get('timeout', 10000)
            )
            
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            
            # Test connection
            self.influx_client.ping()
            self.logger.info("Successfully connected to InfluxDB")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            return False
    
    def _setup_subscriptions(self):
        """Setup RabbitMQ topic subscriptions."""
        topics = self.config.get('topics', [])
        
        for topic_config in topics:
            exchange = topic_config.get('exchange', '')
            routing_key = topic_config.get('routing_key', '#')
            queue_name = topic_config.get('queue_name')
            
            # Declare exchange if specified
            if exchange:
                self.rabbitmq_channel.exchange_declare(
                    exchange=exchange,
                    exchange_type=topic_config.get('exchange_type', 'topic'),
                    durable=topic_config.get('durable', True)
                )
            
            # Declare queue
            if not queue_name:
                # Auto-generate queue name if not specified
                queue_result = self.rabbitmq_channel.queue_declare(queue='', exclusive=True)
                queue_name = queue_result.method.queue
            else:
                self.rabbitmq_channel.queue_declare(
                    queue=queue_name,
                    durable=topic_config.get('durable', True)
                )
            
            # Bind queue to exchange
            if exchange:
                self.rabbitmq_channel.queue_bind(
                    exchange=exchange,
                    queue=queue_name,
                    routing_key=routing_key
                )
            
            # Setup consumer
            self.rabbitmq_channel.basic_consume(
                queue=queue_name,
                on_message_callback=lambda ch, method, properties, body, topic=topic_config: 
                    self._message_callback(ch, method, properties, body, topic),
                auto_ack=False
            )
            
            self.logger.info(f"Subscribed to topic: exchange={exchange}, routing_key={routing_key}, queue={queue_name}")
    
    def _message_callback(self, channel, method, properties, body, topic_config):
        """Handle incoming RabbitMQ messages."""
        try:
            # Parse message
            try:
                message_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                # If not JSON, treat as string
                message_data = {'raw_message': body.decode('utf-8')}
            
            # Transform to InfluxDB point
            point = self._transform_to_influx_point(message_data, topic_config, method)
            
            if point:
                # Write to InfluxDB
                bucket = topic_config.get('influx_bucket') or self.config['influxdb']['bucket']
                self.write_api.write(bucket=bucket, record=point)
                
                self.logger.debug(f"Successfully forwarded message to InfluxDB: {method.routing_key}")
            
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            # Reject message and requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _transform_to_influx_point(self, message_data: Dict, topic_config: Dict, method) -> Optional[Point]:
        """Transform RabbitMQ message to InfluxDB Point."""
        try:
            # Get measurement name
            measurement = topic_config.get('measurement') or method.routing_key.replace('.', '_')
            
            # Create point
            point = Point(measurement)
            
            # Add timestamp
            if 'timestamp' in message_data:
                # Try to parse timestamp from message
                try:
                    if isinstance(message_data['timestamp'], (int, float)):
                        point = point.time(int(message_data['timestamp'] * 1000000000))  # Convert to nanoseconds
                    else:
                        # Try to parse as ISO string
                        dt = datetime.fromisoformat(message_data['timestamp'].replace('Z', '+00:00'))
                        point = point.time(dt)
                except:
                    # Use current time if parsing fails
                    point = point.time(datetime.utcnow())
            else:
                # Use current time
                point = point.time(datetime.utcnow())
            
            # Add tags from topic config
            tags = topic_config.get('tags', {})
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)
            
            # Add routing key as tag
            point = point.tag('routing_key', method.routing_key)
            point = point.tag('exchange', method.exchange)
            
            # Add fields from message data
            field_mapping = topic_config.get('field_mapping', {})
            
            for key, value in message_data.items():
                if key == 'timestamp':
                    continue  # Skip timestamp as it's handled above
                
                # Use field mapping if available
                field_name = field_mapping.get(key, key)
                
                # Add field based on type
                if isinstance(value, (int, float)):
                    point = point.field(field_name, value)
                elif isinstance(value, bool):
                    point = point.field(field_name, value)
                else:
                    point = point.field(field_name, str(value))
            
            return point
            
        except Exception as e:
            self.logger.error(f"Error transforming message to InfluxDB point: {e}")
            return None
    
    def run(self):
        """Main run loop."""
        self.logger.info("Starting RabbitMQ to InfluxDB bridge...")
        
        # Connect to services
        while self.running:
            if not self._connect_rabbitmq():
                self.logger.error("Failed to connect to RabbitMQ, retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            if not self._connect_influxdb():
                self.logger.error("Failed to connect to InfluxDB, retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            break
        
        if not self.running:
            return
        
        try:
            # Setup subscriptions
            self._setup_subscriptions()
            
            self.logger.info("Bridge is running. Press Ctrl+C to stop.")
            
            # Start consuming messages
            while self.running:
                try:
                    self.rabbitmq_connection.process_data_events(time_limit=1)
                except pika.exceptions.AMQPConnectionError:
                    self.logger.error("Lost connection to RabbitMQ, attempting to reconnect...")
                    self._connect_rabbitmq()
                    self._setup_subscriptions()
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup connections and resources."""
        self.logger.info("Cleaning up connections...")
        
        if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
            self.rabbitmq_connection.close()
        
        if self.influx_client:
            self.influx_client.close()
        
        self.logger.info("Cleanup complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='RabbitMQ to InfluxDB Bridge')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Create and run bridge
    bridge = RabbitMQToInfluxBridge(args.config)
    bridge.run()


if __name__ == '__main__':
    main() 