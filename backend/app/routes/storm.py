"""Storm cell tracking routes."""

from fastapi import APIRouter

from ..services.storm import StormCellListResponse, StormTrackListResponse, get_storm_cells, get_storm_tracks

router = APIRouter(prefix="/api/storm", tags=["Storm Tracking"])


@router.get(
    "/cells",
    response_model=StormCellListResponse,
    summary="Detected storm cells",
    description="Return currently detected convective storm cells with intensity, "
    "movement and tracking data. Currently returns clearly-labelled demo data.",
)
def storm_cells() -> StormCellListResponse:
    return get_storm_cells()


@router.get(
    "/tracks",
    response_model=StormTrackListResponse,
    summary="Storm cell movement tracks",
    description="Return historical and projected positions of tracked storm cells. "
    "Currently returns clearly-labelled demo data.",
)
def storm_tracks() -> StormTrackListResponse:
    return get_storm_tracks()
