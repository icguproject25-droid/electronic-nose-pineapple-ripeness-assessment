# Arduino Mega E-Nose Data Acquisition

This folder contains the Arduino Mega programs used for gas sensing data acquisition in our pineapple electronic nose project.

## Overview

The purpose of these Arduino sketches is to collect raw gas sensor data and environmental data for pineapple ripeness analysis.  
The system uses multiple gas sensors together with a BME280 sensor, and outputs the measurements through the serial monitor in CSV-style format for later preprocessing, feature extraction, and machine learning model training.

## Hardware

The data acquisition system is based on:

- Arduino Mega 2560
- MQ2 gas sensor
- MQ3 gas sensor
- MQ9 gas sensor
- MQ135 gas sensor
- TGS2602 gas sensor
- TGS2620 gas sensor
- BME280 environmental sensor

## Sensor Pin Mapping

The analog input pins are assigned as follows:

- MQ2 -> A0
- MQ3 -> A1
- MQ9 -> A2
- MQ135 -> A3
- TGS2602 -> A4
- TGS2620 -> A5

The BME280 is connected through I2C.

## Files

### `air_TGS2620.ino`
This sketch is used to measure the air background condition inside the container.

Main functions:
- Preheats all sensors for 5 minutes
- Waits 30 seconds before recording
- Collects air baseline data
- Records gas sensor values and environmental values
- Outputs formatted serial data for later analysis

This program is mainly used to establish the background reference of the sensing environment.

### `pineapple_TGS2620.ino`
This sketch is used to measure pineapple gas signals inside the container.

Main functions:
- Preheats all sensors for 5 minutes
- Waits 30 seconds before recording
- Reads raw values from all gas sensors
- Reads temperature, humidity, and pressure from BME280
- Performs basic validation for abnormal values
- Computes baseline from the first 30 valid samples
- Outputs time-series sensor data through serial output

This program is mainly used to capture volatile gas patterns released by pineapple samples.

## Data Output

The serial output is designed for data logging and later model development.  
The recorded fields include:

- Timestamp
- Raw sensor readings
- Temperature
- Humidity
- Pressure
- Log-transformed sensor values
- Delta log values
- Moving-average log values

The output can be saved as CSV-like text and used in the data preprocessing and machine learning pipeline.

## Workflow

The general workflow is:

1. Upload the selected Arduino sketch to Arduino Mega
2. Place the sensors and sample container in the experiment setup
3. Open the serial monitor or serial logger
4. Wait for the preheating stage to finish
5. Start recording
6. Save the serial output for later processing

## Notes

- `air_TGS2620.ino` is used for air/background measurement
- `pineapple_TGS2620.ino` is used for pineapple sample measurement
- The sampling interval is 1 second
- The maximum number of samples is 900
- The first 30 valid samples are used to compute the baseline
- The BME280 address is checked at both `0x76` and `0x77`

## Project Context

These Arduino programs are part of our electronic nose based pineapple ripeness detection system.  
The collected sensor data is later used for:

- data cleaning
- baseline correction
- feature engineering
- model training
- ripeness classification
- deployment to Raspberry Pi and web-based interfaces

## Author

This folder is part of our graduation project on non-destructive pineapple ripeness detection using an electronic nose system.
