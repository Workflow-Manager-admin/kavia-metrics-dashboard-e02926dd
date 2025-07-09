# Kavia Metrics Backend - S3 Access & Environment Configuration with Mock Data Support

This backend fetches metric JSON data from AWS S3 or (for local development and testing) from a local mock data file.

## Required Environment Variables

These must be set for S3 connectivity (unless using mock mode):

- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret access key
- `AWS_SESSION_TOKEN` (optional, for temporary credentials)
- `AWS_REGION` - AWS region (default: `us-east-1`)
- `S3_METRICS_BUCKET` - S3 bucket name (default: `metrics-data`)
- `S3_METRICS_PREFIX` - S3 prefix/path for JSON objects (default: empty string)

### Mock Data Mode (Local Development)

You can force the API to use mock data, bypassing all S3 logic, by setting:

- `USE_MOCK_DATA=true` (or `True`, `1`, `yes`)

If S3 connection fails for any reason (missing credentials, network, invalid configuration), the API **will automatically fallback to mock data** to enable dashboard/frontend development to continue.

**Mock data is loaded from `src/api/mock_metrics.json` and provides sample metric entries.**

## Endpoints

- `GET /metrics`: List all metric JSON entries (or mock data).
- `GET /metrics/{id}`: Retrieve a single metric entry by ID (from JSON/object key or mock data).

## Notes

- IDs are taken from either `"id"` field in metric JSON, or from the filename (key with `.json` removed).
- Errors in S3/data fetch are returned as HTTP 500 with details.
- If mock data mode is active, the API will always use local mock data and never attempt S3.
- To restore real S3 operation, unset or set `USE_MOCK_DATA` to `false`.

### Local Development Quickstart

1. `export USE_MOCK_DATA=true`
2. Run the FastAPI app as usual (e.g., `uvicorn src.api.main:app --reload`)
3. Access `/metrics` and `/metrics/{id}` for immediate frontend dashboard development—no AWS/S3 setup required.

