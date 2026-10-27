"""
housing_api.py

A  mock backend for a campus housing portal: browse residence
halls and room types with live availability, select/cancel a housing
assignment, and read housing announcements.

Run with:
    pip install fastapi uvicorn
    python housing_api.py

API is available at http://localhost:8006

Endpoints:
    GET  /buildings
    GET  /room-types
    GET  /room-types/{room_type_id}
    GET  /my-housing
    POST /housing/select   body: {"room_type_id": int}
    POST /housing/cancel
    GET  /announcements
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Mock Housing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# In-memory "database"
# ---------------------------------------------------------------------

BUILDINGS = [
    {"id": 1, "name": "Harborview Hall", "class_years": "First-year", "amenities": "dining hall, laundry, study lounge"},
    {"id": 2, "name": "Elm Residence", "class_years": "Sophomore+", "amenities": "kitchenette, laundry"},
    {"id": 3, "name": "Ridgeline Suites", "class_years": "Junior/Senior", "amenities": "kitchen, private bath, laundry"},
]

ROOM_TYPES = [
    {"id": 1, "building_id": 1, "name": "Double", "price_per_term": 3200, "capacity": 2, "total_spaces": 120},
    {"id": 2, "building_id": 1, "name": "Triple", "price_per_term": 2800, "capacity": 3, "total_spaces": 45},
    {"id": 3, "building_id": 2, "name": "Single", "price_per_term": 4100, "capacity": 1, "total_spaces": 40},
    {"id": 4, "building_id": 2, "name": "Double", "price_per_term": 3400, "capacity": 2, "total_spaces": 80},
    {"id": 5, "building_id": 3, "name": "4-Person Suite", "price_per_term": 3900, "capacity": 4, "total_spaces": 32},
]

SELECTIONS = [
    {"id": 1, "room_type_id": 1, "student": "Dolly Parton"},
    {"id": 2, "room_type_id": 1, "student": "Elvis Presley"},
    {"id": 3, "room_type_id": 3, "student": "Johnny Cash"},
]
_next_selection_id = 4

ANNOUNCEMENTS = [
    {
        "id": 1,
        "title": "Housing selection opens Monday",
        "posted": "2026-08-19T09:00:00",
        "body": "Returning student housing selection opens Monday at 8am. Popular room types in Ridgeline Suites have historically filled within the first day.",
    },
    {
        "id": 2,
        "title": "Elm Residence laundry room closed this week",
        "posted": "2026-08-21T09:00:00",
        "body": "The main-floor laundry room in Elm Residence is closed for repairs. Residents can use the basement laundry room in the meantime.",
    },
]

# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

class SelectRequest(BaseModel):
    room_type_id: int

def _get_building_or_404(building_id: int) -> dict:
    for b in BUILDINGS:
        if b["id"] == building_id:
            return b
    raise HTTPException(status_code=404, detail="Building not found")

def _get_room_type_or_404(room_type_id: int) -> dict:
    for rt in ROOM_TYPES:
        if rt["id"] == room_type_id:
            return rt
    raise HTTPException(status_code=404, detail="Room type not found")

def _taken_count(room_type_id: int) -> int:
    return sum(1 for s in SELECTIONS if s["room_type_id"] == room_type_id)

def _my_selection():
    for s in SELECTIONS:
        if s["student"] == "you":
            return s
    return None

def _summarize_room_type(rt: dict) -> dict:
    taken = _taken_count(rt["id"])
    building = _get_building_or_404(rt["building_id"])
    summary = dict(rt)
    summary["building_name"] = building["name"]
    summary["taken"] = taken
    summary["spaces_open"] = rt["total_spaces"] - taken
    return summary

@app.get("/buildings")
def list_buildings():
    return BUILDINGS

@app.get("/room-types")
def list_room_types():
    return [_summarize_room_type(rt) for rt in ROOM_TYPES]

@app.get("/room-types/{room_type_id}")
def get_room_type(room_type_id: int):
    return _summarize_room_type(_get_room_type_or_404(room_type_id))

@app.get("/my-housing")
def get_my_housing():
    selection = _my_selection()
    if not selection:
        return None
    rt = _get_room_type_or_404(selection["room_type_id"])
    return {**selection, **_summarize_room_type(rt)}

@app.get("/announcements")
def list_announcements():
    return ANNOUNCEMENTS

@app.post("/housing/select")
def select_housing(req: SelectRequest):
    global _next_selection_id
    room_type = _get_room_type_or_404(req.room_type_id)
    if _my_selection():
        raise HTTPException(
            status_code=400,
            detail="You already have a housing selection. Cancel it before choosing a new one.",
        )
    if _taken_count(room_type["id"]) >= room_type["total_spaces"]:
        raise HTTPException(status_code=400, detail=f'{room_type["name"]} is full')

    new_selection = {"id": _next_selection_id, "room_type_id": room_type["id"], "student": "you"}
    SELECTIONS.append(new_selection)
    _next_selection_id += 1
    return new_selection

@app.post("/housing/cancel")
def cancel_housing():
    selection = _my_selection()
    if not selection:
        raise HTTPException(status_code=404, detail="You don't have a housing selection to cancel")
    SELECTIONS.remove(selection)
    return {"cancelled": selection["id"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)