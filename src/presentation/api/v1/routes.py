from fastapi import APIRouter, HTTPException
from datetime import datetime
from src.application.use_cases.process_egg_counts import ProcessEggCountsUseCase
from src.presentation.api.v1.models.egg_count import EggCountRequest, EggCountResponse
from src.config.settings import AVIARY_CONFIGS
from src.infrastructure.orion.client import OrionClient
from src.infrastructure.database.sql_server_repository import SqlServerRepository

router = APIRouter()

@router.post("/egg_counts", response_model=EggCountResponse)
async def process_egg_counts(request: EggCountRequest):
    aviary_id = request.aviary_id
    #date = request.date
    try:
        # Parse validated date string to date object
        date_obj = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        # Shouldn't reach here due to Pydantic validation, but included for safety
        raise HTTPException(status_code=400, detail="Invalid date format")

    if aviary_id not in AVIARY_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Invalid aviary_id: {aviary_id}")
    config = AVIARY_CONFIGS[aviary_id]
    orion_client = OrionClient(
        ip=config.ip,
        port=config.port,
        devcmd=config.devcmd,
        num_rows=config.num_rows,
        target_cmd=config.target_cmd,
        response_size=config.response_size
    )
    db_repo = SqlServerRepository()
    use_case = ProcessEggCountsUseCase(
        orion_repo=orion_client,
        db_repo=db_repo,
        fila_mapping=config.fila_mapping
    )
    try:
        result = use_case.execute(aviary_id, date_obj)
        if not result:
            raise ValueError("Failed to process egg counts")
        return EggCountResponse(
            status="success",
            message="Egg counts updated successfully",
            data={
                "aviary_id": result.aviary_id,
                "date": result.date.strftime("%Y-%m-%d"),
                "egg_counts": result.counts
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing egg counts: {str(e)}")
