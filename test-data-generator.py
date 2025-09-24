#!/usr/bin/env python3
"""
Test Data Generator for RabbitMQ to InfluxDB Bridge Plugin

This script generates sample sensor data and publishes it to RabbitMQ
for testing the bridge plugin functionality.
"""

import json
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any

import pika


def generate_sensor_data() -> Dict[str, Any]:
    """Generate realistic sensor data."""
    now = datetime.now(timezone.utc)
    
    return {
        "timestamp": now.isoformat(),
        "sensor_id": f"sensor_{random.randint(1, 10):03d}",
        "node_id": f"node_{random.randint(1, 5):03d}",
        "temperature": round(random.uniform(15.0, 35.0), 2),
        "humidity": round(random.uniform(30.0, 90.0), 2),
        "pressure": round(random.uniform(980.0, 1020.0), 2),
        "light_level": random.randint(0, 1000),
        "battery_voltage": round(random.uniform(3.0, 4.2), 2),
        "signal_strength": random.randint(-80, -20),
        "status": random.choice(["active", "inactive", "warning"])
    }


def generate_weather_data() -> Dict[str, Any]:
    """Generate weather station data."""
    now = datetime.now(timezone.utc)
    
    return {
        "timestamp": now.isoformat(),
        "station_id": f"weather_{random.randint(1, 3):03d}",
        "wind_speed": round(random.uniform(0.0, 25.0), 1),
        "wind_direction": random.randint(0, 359),
        "rainfall": round(random.uniform(0.0, 5.0), 2),
        "solar_radiation": random.randint(0, 1200),
        "uv_index": random.randint(0, 11),
        "visibility": round(random.uniform(5.0, 20.0), 1)
    }


def generate_alert_data() -> Dict[str, Any]:
    """Generate alert/event data."""
    now = datetime.now(timezone.utc)
    
    alert_types = ["temperature_high", "humidity_low", "battery_low", "connection_lost"]
    severities = ["info", "warning", "critical"]
    
    return {
        "timestamp": now.isoformat(),
        "alert_id": f"alert_{random.randint(1000, 9999)}",
        "alert_type": random.choice(alert_types),
        "severity": random.choice(severities),
        "source": f"sensor_{random.randint(1, 10):03d}",
        "message": f"Alert triggered: {random.choice(alert_types)}",
        "value": round(random.uniform(0.0, 100.0), 2),
        "threshold": round(random.uniform(50.0, 80.0), 2)
    }


class DataPublisher:
    """Publishes test data to RabbitMQ."""
    
    def __init__(self, host='rabbitmq', port=5672, username='waggle', password='waggle'):
        self.connection = None
        self.channel = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare exchanges
                self.channel.exchange_declare(
                    exchange='sensor.data',
                    exchange_type='topic',
                    durable=True
                )
                
                self.channel.exchange_declare(
                    exchange='weather.updates',
                    exchange_type='topic',
                    durable=True
                )
                
                self.channel.exchange_declare(
                    exchange='alerts',
                    exchange_type='topic',
                    durable=True
                )
                
                print(f"Connected to RabbitMQ at {self.host}:{self.port}")
                return True
                
            except Exception as e:
                retry_count += 1
                print(f"Connection attempt {retry_count} failed: {e}")
                if retry_count < max_retries:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("Max retries reached. Exiting.")
                    return False
    
    def publish_sensor_data(self):
        """Publish sensor data."""
        data = generate_sensor_data()
        routing_key = f"sensor.{data['sensor_id']}.measurements"
        
        self.channel.basic_publish(
            exchange='sensor.data',
            routing_key=routing_key,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                timestamp=int(time.time())
            )
        )
        
        print(f"Published sensor data: {routing_key}")
    
    def publish_weather_data(self):
        """Publish weather data."""
        data = generate_weather_data()
        routing_key = f"station.{data['station_id']}.measurements"
        
        self.channel.basic_publish(
            exchange='weather.updates',
            routing_key=routing_key,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                timestamp=int(time.time())
            )
        )
        
        print(f"Published weather data: {routing_key}")
    
    def publish_alert_data(self):
        """Publish alert data."""
        data = generate_alert_data()
        routing_key = f"alert.{data['severity']}.{data['alert_type']}"
        
        self.channel.basic_publish(
            exchange='alerts',
            routing_key=routing_key,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                timestamp=int(time.time())
            )
        )
        
        print(f"Published alert: {routing_key}")
    
    def close(self):
        """Close connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


def main():
    """Main function to run the data generator."""
    print("Starting test data generator...")
    
    publisher = DataPublisher()
    
    if not publisher.connect():
        return
    
    try:
        message_count = 0
        
        while True:
            # Publish different types of data with varying frequencies
            
            # Sensor data (most frequent)
            if message_count % 2 == 0:
                publisher.publish_sensor_data()
            
            # Weather data (less frequent)
            if message_count % 5 == 0:
                publisher.publish_weather_data()
            
            # Alert data (least frequent)
            if message_count % 10 == 0:
                publisher.publish_alert_data()
            
            message_count += 1
            
            # Sleep between messages
            time.sleep(random.uniform(1.0, 3.0))
            
    except KeyboardInterrupt:
        print("\nStopping data generator...")
    
    except Exception as e:
        print(f"Error in data generator: {e}")
    
    finally:
        publisher.close()
        print("Data generator stopped.")


if __name__ == '__main__':
    main() 