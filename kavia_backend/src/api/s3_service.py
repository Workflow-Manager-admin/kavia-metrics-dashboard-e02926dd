import os
import boto3
from typing import List, Optional, Dict, Any
from botocore.exceptions import BotoCoreError, ClientError

class S3MetricsService:
    """
    Service to fetch metrics JSON data objects from an AWS S3 bucket.
    """

    def __init__(self):
        # Configuration: S3 credentials and region loaded from environment
        self.s3_bucket = os.getenv("S3_METRICS_BUCKET", "metrics-data")
        self.s3_prefix = os.getenv("S3_METRICS_PREFIX", "")
        session = boto3.session.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.s3 = session.client("s3")

    # PUBLIC_INTERFACE
    def list_metric_objects(self) -> List[str]:
        """List all .json object keys in the metrics S3 bucket."""
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
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"S3 listing error: {str(e)}") from e

    # PUBLIC_INTERFACE
    def get_metric_object(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single metric JSON object from S3 by key."""
        try:
            response = self.s3.get_object(Bucket=self.s3_bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            import json
            data = json.loads(content)
            return data
        except self.s3.exceptions.NoSuchKey:
            return None
        except (BotoCoreError, ClientError, Exception) as e:
            raise RuntimeError(f"S3 retrieval error for key '{key}': {str(e)}") from e

    # PUBLIC_INTERFACE
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """
        Retrieve and parse all metrics JSON objects.
        """
        metrics = []
        keys = self.list_metric_objects()
        for key in keys:
            metric = self.get_metric_object(key)
            if metric is not None:
                # Attach 'id' from key if not present by default
                if "id" not in metric or not metric.get("id"):
                    metric["id"] = self.extract_id_from_key(key)
                metrics.append(metric)
        return metrics

    # PUBLIC_INTERFACE
    def get_metric_by_id(self, id_: str) -> Optional[Dict[str, Any]]:
        """Get a metric entry whose 'id' matches the given id."""
        keys = self.list_metric_objects()
        for key in keys:
            metric = self.get_metric_object(key)
            if not metric:
                continue
            # Look for matching id
            if "id" in metric and str(metric["id"]) == str(id_):
                return metric
            # If 'id' is not in object, try by key/id mapping
            if self.extract_id_from_key(key) == str(id_):
                metric["id"] = str(id_)
                return metric
        return None

    def extract_id_from_key(self, key: str) -> str:
        # Extract id from object key (e.g., "metrics/123.json" -> "123")
        base = os.path.basename(key)
        if base.endswith(".json"):
            return base[:-5]
        return base
