@echo off
echo Installing new dependencies for SmartLinks Autopilot RCP enhancements...

echo Installing aiohttp...
pip install aiohttp>=3.8.0

echo Installing OR-Tools...
pip install ortools>=9.5.0

echo Installing OpenTelemetry core...
pip install opentelemetry-api>=1.20.0
pip install opentelemetry-sdk>=1.20.0

echo Installing OpenTelemetry instrumentation...
pip install opentelemetry-instrumentation-fastapi>=0.41b0
pip install opentelemetry-instrumentation-sqlalchemy>=0.41b0

echo Installing OpenTelemetry exporters...
pip install opentelemetry-exporter-prometheus>=0.57b0
pip install opentelemetry-exporter-otlp-proto-grpc>=1.20.0

echo Done! All new dependencies installed.
pause
