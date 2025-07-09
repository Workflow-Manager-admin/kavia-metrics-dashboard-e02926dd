# Kavia Metrics Backend - S3 Access & Environment Configuration

This backend fetches metric JSON data from AWS S3.

## Required Environment Variables

These must be set for S3 connectivity:

- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret access key
- `AWS_SESSION_TOKEN` (optional, for temporary credentials)
- `AWS_REGION` - AWS region (default: `us-east-1`)
- `S3_METRICS_BUCKET` - S3 bucket name (default: `metrics-data`)
- `S3_METRICS_PREFIX` - S3 prefix/path for JSON objects (default: empty string)

## Endpoints

- `GET /metrics`: List all metric JSON entries.
- `GET /metrics/{id}`: Retrieve a single metric entry by ID (from JSON or object key).

## Notes

- IDs are taken from either `"id"` field in metric JSON, or from the filename (key with `.json` removed).
- Errors in S3/data fetch are returned as HTTP 500 with details.
