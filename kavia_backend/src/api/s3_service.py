import os
import json
import boto3
from typing import List, Optional, Dict, Any
from botocore.exceptions import BotoCoreError, ClientError

class S3MetricsService:
    """
    Service to fetch metrics JSON data objects from AWS S3 or use local mock data if S3 fails
    or if 'USE_MOCK_DATA' env variable is set to 'true', '1', or 'yes' (case-insensitive).
    """

    MOCK_DATA_FILE = os.path.join(os.path.dirname(__file__), "mock_metrics.json")

    def __init__(self):
        # Allow toggle of mock mode by environment variable
        env_mock = os.getenv("USE_MOCK_DATA", "false").lower()
        self.use_mock = env_mock in ("true", "1", "yes")

        # Configuration: S3 credentials and region loaded from environment
        self.s3_bucket = os.getenv("S3_METRICS_BUCKET", "metrics-data")
        self.s3_prefix = os.getenv("S3_METRICS_PREFIX", "")
        self.s3 = None
        self.s3_available = False

        if not self.use_mock:
            try:
                session = boto3.session.Session(
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                    region_name=os.getenv("AWS_REGION", "us-east-1")
                )
                self.s3 = session.client("s3")
                # Attempt a lightweight call to check that S3 credentials are valid
                # This prevents S3 failures at request time.
                self.s3.list_buckets()
                self.s3_available = True
            except Exception:
                # Fallback to mock if S3 isn't usable
                self.use_mock = True
                self.s3_available = False

    # PUBLIC_INTERFACE
    def list_metric_objects(self) -> List[str]:
        """List all .json object keys in the metrics S3 bucket, unless using mock data."""
        if self.use_mock:
            return [f"mock:{item['id']}" for item in self._get_mock_data()]
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.s3_bucket,
                Prefix=self.s3_prefix
            )
            keys = []
            for page in page_iterator:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith(".json"):
                        keys.append(key)
            return keys
        except (BotoCoreError, ClientError):
            # If S3 fails, fallback to mock
            self.use_mock = True
            return [f"mock:{item['id']}" for item in self._get_mock_data()]

    # PUBLIC_INTERFACE
    def get_metric_object(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single metric JSON object from S3 by key or from mock data if using mock."""
        if self.use_mock:
            id_ = self.extract_id_from_key(key)
            for item in self._get_mock_data():
                if str(item.get("id")) == str(id_):
                    return item
            return None
        try:
            response = self.s3.get_object(Bucket=self.s3_bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            data = json.loads(content)
            return data
        except Exception:
            # Fallback to mock if S3 retrieval error
            self.use_mock = True
            id_ = self.extract_id_from_key(key)
            for item in self._get_mock_data():
                if str(item.get("id")) == str(id_):
                    return item
            return None

    # PUBLIC_INTERFACE
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """
        Retrieve and parse all metrics JSON objects, from S3 or mock data.
        """
        if self.use_mock:
            return self._get_mock_data()
        try:
            metrics = []
            keys = self.list_metric_objects()
            for key in keys:
                metric = self.get_metric_object(key)
                if metric is not None:
                    # Attach 'id' from key if not present
                    if "id" not in metric or not metric.get("id"):
                        metric["id"] = self.extract_id_from_key(key)
                    metrics.append(metric)
            return metrics
        except Exception:
            # Any failure falls back to mock mode
            self.use_mock = True
            return self._get_mock_data()

    # PUBLIC_INTERFACE
    def get_metric_by_id(self, id_: str) -> Optional[Dict[str, Any]]:
        """Get a metric entry whose 'id' matches the given id, using S3 or mock data."""
        if self.use_mock:
            for item in self._get_mock_data():
                if str(item.get("id")) == str(id_):
                    return item
            return None
        try:
            keys = self.list_metric_objects()
            for key in keys:
                metric = self.get_metric_object(key)
                if not metric:
                    continue
                if "id" in metric and str(metric["id"]) == str(id_):
                    return metric
                if self.extract_id_from_key(key) == str(id_):
                    metric["id"] = str(id_)
                    return metric
            return None
        except Exception:
            # Fallback to mock data
            self.use_mock = True
            for item in self._get_mock_data():
                if str(item.get("id")) == str(id_):
                    return item
            return None

    def extract_id_from_key(self, key: str) -> str:
        # Accepts s3 key or "mock:<id>"
        if key.startswith("mock:"):
            return key.split("mock:", 1)[-1]
        base = os.path.basename(key)
        if base.endswith(".json"):
            return base[:-5]
        return base

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Return mock metrics loaded from local mock_metrics.json file."""
        try:
            with open(self.MOCK_DATA_FILE, "r") as f:
                data = json.load(f)
            return data
        except Exception:
            # Fallback to builtin minimal if file is missing/corrupt
            return [
                {
                    "id": "mock-default",
                    "app_name": "MockApp",
                    "elapsed_time": 0.0,
                    "total_cost": 0.0,
                    "date": "2024-01-01",
                    "project_link": "https://example.com",
                    "cga_version": "mock",
                    "model": "mock",
                    "streaming": False
                }
            ]
