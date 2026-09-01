"""Storm cell tracking service."""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_storm_cells, demo_storm_tracks
from ..schemas.storm import StormCell, StormTrack


class StormCellListResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    count: int
    cells: list[StormCell]


class StormTrackListResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    count: int
    tracks: list[StormTrack]


def get_storm_cells() -> StormCellListResponse:
    cells = demo_storm_cells()
    return StormCellListResponse(count=len(cells), cells=cells)


def get_storm_tracks() -> StormTrackListResponse:
    tracks = demo_storm_tracks()
    return StormTrackListResponse(count=len(tracks), tracks=tracks)
