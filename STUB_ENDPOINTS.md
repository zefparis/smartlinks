# Stub Endpoints Documentation

This document describes the stub endpoints that have been implemented to support the frontend while the actual backend implementation is in progress.

## Analytics Endpoints

### `GET /api/analytics/clicks/history`

**Description**: Returns click history data with optional filters.

**Query Parameters**:
- `days`: Number of days of history to return (default: 30)
- `segment_id`: Optional segment ID to filter by
- `device`: Optional device type to filter by

**Example Response**:
```json
{
  "history": [
    {
      "date": "2025-08-18",
      "clicks": 42,
      "conversions": 10,
      "revenue": 15.75,
      "conversion_rate": 23.81
    }
  ],
  "total_clicks": 42,
  "total_conversions": 10,
  "total_revenue": 15.75
}
```

### `GET /api/analytics/devices`

**Description**: Returns device statistics.

**Query Parameters**:
- `segment_id`: Optional segment ID to filter by
- `start_date`: Optional start date (YYYY-MM-DD)
- `end_date`: Optional end date (YYYY-MM-DD)

**Example Response**:
```json
{
  "devices": [
    {
      "device": "mobile",
      "clicks": 25,
      "conversions": 5,
      "conversion_rate": 20.0
    }
  ],
  "total_clicks": 25,
  "total_conversions": 5,
  "overall_conversion_rate": 20.0
}
```

## Services Endpoints

### `GET /api/services/status`

**Description**: Returns the status of all services.

**Example Response**:
```json
{
  "router": {
    "status": "running",
    "uptime": 3600,
    "last_check": "2025-08-18T16:00:00Z"
  },
  "autopilot": {
    "status": "idle",
    "last_run": "2025-08-18T15:30:00Z"
  },
  "probes": {
    "status": "active",
    "last_run": "2025-08-18T15:45:00Z"
  }
}
```

### `POST /api/services/autopilot/start`

**Description**: Starts the autopilot service.

**Example Response**:
```json
{
  "status": "success",
  "message": "Autopilot started successfully"
}
```

### `POST /api/services/router/start`

**Description**: Starts the router service.

**Example Response**:
```json
{
  "status": "success",
  "message": "Router started successfully"
}
```

### `POST /api/services/probes/start`

**Description**: Starts the probes service.

**Example Response**:
```json
{
  "status": "success",
  "message": "Probes started successfully"
}
```

## Implementation Notes

- All endpoints return HTTP 200 OK with a JSON response.
- Error responses include a descriptive message and an appropriate HTTP status code.
- The response formats match the expected frontend interfaces.
- Timestamps are in ISO 8601 format (e.g., "2025-08-18T16:00:00Z").
