import os
from fastapi import FastAPI, HTTPException
import httpx
import json
import datetime

from database import AltData, AltHealthData



from sqlmodel import Session, SQLModel, create_engine, func, select, update
app = FastAPI()

if os.environ.get("API_TESTING") == "1":
    engine = create_engine("sqlite:///test_database.db")
else:
    engine = create_engine("sqlite:///database.db")
    SQLModel.metadata.create_all(engine)

async def fetch_altitude_data() -> dict[str, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://nestio.space/api/satellite/data")
        resp.raise_for_status()
        alt_data = json.loads(resp.content)
        return alt_data


@app.get("/stats")
async def stats():
    row = None
    try:
        new_data = await fetch_altitude_data()
        row = AltData(altitude=float(new_data["altitude"]), last_updated=datetime.datetime.fromisoformat(new_data["last_updated"]))
    except httpx.HTTPStatusError:
        pass
    with Session(engine) as session:
        if row:
            session.add(row)
            session.commit()
        statement = select(
            func.avg(AltData.altitude).label("avg_altitude"),
            func.min(AltData.altitude).label("min_altitude"),
            func.max(AltData.altitude).label("max_altitude")
        ).where(AltData.last_updated>=datetime.datetime.now() - datetime.timedelta(minutes=5))

        stats_data = session.exec(statement).first()
        if not stats_data:
            # we likely got new data, so unless the satellite API returns data which is more than 5 minutes old, we are guaranteed something.
            # that, or the requests over the last five minutes have been receiving API errors
            raise HTTPException(status_code=500, detail="No current data.")
        stats_data = {"avg_altitude": stats_data[0], "min_altitude": stats_data[1], "max_altitude": stats_data[2]}
        return stats_data


def health_logic():
    with Session(engine) as session:
        statement = select(
            func.avg(AltData.altitude).label("avg_altitude"),
        ).where(AltData.last_updated>=datetime.datetime.now() - datetime.timedelta(minutes=1))
        stats_data = session.exec(statement).first()
        if not stats_data:
            raise HTTPException(status_code=500, detail="No current data")
        avg_alt = stats_data
        if avg_alt < 160:
            decay_row = AltHealthData(orbital_decay_timestamp=datetime.datetime.now())
            session.add(decay_row)
            session.commit()
            return  "WARNING: RAPID ORBITAL DECAY IMMINENT"
        else:
            target_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
            recent_decay = session.exec(select(AltHealthData).where(AltHealthData.orbital_decay_timestamp>=target_time)).first()
            if recent_decay:
                session.exec(update(AltHealthData).where(AltHealthData.orbital_decay_timestamp >= target_time, AltHealthData.orbit_sustained_timestamp == None).values(orbit_sustained_timestamp=datetime.datetime.now()))
                session.commit()
                return "Sustained Low Earth Orbit Resumed"
            else:
                return "Altitude is A-OK"


@app.get("/health")
async def health():
    return health_logic()

