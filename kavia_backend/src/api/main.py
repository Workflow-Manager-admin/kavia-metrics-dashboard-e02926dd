from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel, Field

from .s3_service import S3MetricsService

tags_metadata = [
    {
        "name": "metrics",
        "description": "Operations to retrieve application metrics from S3."
    }
]

app = FastAPI(
    title="Kavia Metrics API",
    description="Backend API for the Kavia Metrics Dashboard. Provides metrics from S3.",
    version="1.0.0",
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MetricModel(BaseModel):
    """Pydantic model to describe a metric entry."""
    id: str = Field(..., description="Unique identifier for the metric entry")
    app_name: str = Field(None, description="Application name")
    elapsed_time: float = Field(None, description="Elapsed time in seconds")
    total_cost: float = Field(None, description="Total cost")
    date: str = Field(None, description="Date of metric collection")
    project_link: str = Field(None, description="Link to project")
    cga_version: str = Field(None, description="CGA version used")
    model: str = Field(None, description="Model identifier")
    streaming: bool = Field(None, description="Streaming enabled/disabled")
    # Any additional fields will be preserved
    class Config:
        extra = "allow"

s3_service = S3MetricsService()

@app.get("/", tags=["metrics"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get(
    "/metrics",
    response_model=List[MetricModel],
    summary="Fetch all metric entries from S3",
    description="Returns a list of all metrics JSON entries in the S3 bucket.",
    tags=["metrics"],
    responses={
        200: {"description": "Successful Response"},
        500: {"description": "S3 error or Data fetch issue"},
    }
)
def get_all_metrics():
    """
    Returns a list of all parsed metrics from S3 as JSON.
    """
    try:
        entries = s3_service.get_all_metrics()
        return entries
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch metrics: {str(e)}"}
        )

# PUBLIC_INTERFACE
@app.get(
    "/metrics/{id}",
    response_model=MetricModel,
    summary="Fetch specific metric entry by id",
    description="Returns a single metric entry by unique identifier (from field or S3 object key) from the S3 bucket.",
    tags=["metrics"],
    responses={
        200: {"description": "Metric found"},
        404: {"description": "No entry found for the specified id"},
        500: {"description": "S3 error or Data fetch issue"},
    }
)
def get_metric_by_id(id: str = Path(..., description="The unique metric id (from object key or entry id field)")):
    """
    Returns one metric entry matching its identifier.
    """
    try:
        metric = s3_service.get_metric_by_id(id)
        if metric is None:
            raise HTTPException(status_code=404, detail=f"Metric entry with id '{id}' not found")
        return metric
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch metric '{id}': {str(e)}"}
        )
