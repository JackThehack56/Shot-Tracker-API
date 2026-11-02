from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.models import Shot, Hole, Round
from src.schemas import ShotData, RoundResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import RoundRow, create_db_and_tables, get_async_session
from sqlalchemy import select
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def patch_to_db(round: Round, session: AsyncSession) -> None:
    if not round and not session: return
    global round_id
    result = await session.execute(select(RoundRow).where(RoundRow.id == round_id))
    db_round = result.scalars().first()
    if db_round:
        db_round.data = round.to_dict()
        db_round.is_finished = round.is_finished
        await session.commit()
    else: # If it's not it in the db create it
        round_row = RoundRow(
            id=round_id,
            is_finished=round.is_finished,
            data=round.to_dict()
        )

        session.add(round_row)
        await session.commit()
        await session.refresh(round_row)
        round_id = round_row.id
        print(str(round_id))


def parse_data(data: ShotData) -> Shot:
    return Shot(
        data.hole,
        data.stroke, 
        data.club, 
        data.category, 
        data.start, 
        data.finish,
        data.sg
    )


round: Round = None
round_id: uuid.UUID = None

@app.get("/test")
async def test(
    session: AsyncSession = Depends(get_async_session)
):
    global round
    if not round: return {"detail": "There's no round"}
    un_finished_holes = []
    for hole in round.holes:
        if not hole.is_finished:
            un_finished_holes.append(hole.hole)

    result = await session.execute(select(RoundRow).where(RoundRow.id == round_id))
    db_round = result.scalars().first()

    db_data = {
        "course": db_round.data["course"],
        "is_finished": db_round.is_finished,
        "hole_count": len(db_round.data["holes"])
    } if db_round else None

    return {
        "local": {
            "course": round.course,
            "is_finished": round.is_finished,
            "un_finished_holes": un_finished_holes,
            "hole_count": len(round.holes)
        },
        "database": db_data 
    }

@app.post("/receive") 
async def receive_data(
    data: ShotData,
    session: AsyncSession = Depends(get_async_session)
) -> RoundResponse:
    global round, round_id

    if round and round.is_finished:
        round.is_finished = True
        await patch_to_db(round, session)
        round, round_id = None, None
        return {
            "success": True,
            "message": "Succefully stored in db!\nThis round is now un-editable from here\nVisit the activity page to fix any mistakes"
        }

    if not round and not data.course or round and not round.course:
        raise HTTPException(status_code=400, detail="You must provide a course name!")

    shot = parse_data(data)

    if not round and not round_id:
        round = Round(data.course, Hole(1, shot))
        round_row = RoundRow(
            is_finished=round.is_finished,
            data=round.to_dict()
        )

        session.add(round_row)
        await session.commit()
        await session.refresh(round_row)
        round_id = round_row.id

        print(str(round_id))
    elif round.get_last_shot().hole == shot.hole:
        round.holes[-1].add_shot(shot)
        round._is_finished()
        await patch_to_db(round, session)
    else:
        round.add_hole(Hole(shot.hole, shot))
        await patch_to_db(round, session)

    if round and round.is_finished:
        return {
            "success": True, 
            "message": f"Click submit again to confirm this:\n{round.to_string()}"
        }

    return {
        "success": True,
        "message": round.to_string() 
    }


@app.get("/round")
async def get_current_round(
    session: AsyncSession = Depends(get_async_session)
) -> RoundResponse:
    global round, round_id
    success = True
    message = None
    # TODO Clean this code up!
    result = await session.execute(select(RoundRow).where(RoundRow.is_finished == False).where())
    current_round = result.scalars().first()

    if current_round:
        round = Round.from_dict(data=current_round.data)
        round_id = current_round.id
    elif round and round.is_finished and not current_round:
        finished_round = await session.execute(select(RoundRow).where(RoundRow.id == round_id).where(RoundRow.is_finished == True))
        finished_round = finished_round.scalars().first()
        if not finished_round:
            round, round_id = None, None
            return { 
                "success": False,
                "message": "No un-finished round found in db."
            }
            # If there is a running round and a duplicate is missing
            # in the db than it assumes that there is no round 
            # to be found in the db
        round = Round.from_dict(data=finished_round.data)
        round_id = finished_round.id
        message = f"Click submit again to confirm this:\n{round.to_string()}"
    elif round and not current_round: # If it's not it in the db create it
        round_row = RoundRow(
            id=round_id,
            is_finished=round.is_finished,
            data=round.to_dict()
        )

        session.add(round_row)
        await session.commit()
        await session.refresh(round_row)
        round_id = round_row.id
        print(str(round_id))   
    else:
        success = False
        message = "No un-finished round found in db."

    return {
        "success": success,
        "message": round.to_string() if not message else message
    }


@app.delete("/delete/shot")
async def delete_last_shot(
    session: AsyncSession = Depends(get_async_session)
) -> RoundResponse:
    global round, round_id
    if not round: return {"success":False,"message":"No shots to delete!"}

    if len(round.holes) > 0 and len(round.holes[-1].shots) > 0: 
        round.holes[-1].delete_last_shot()
        round._is_finished()
        await patch_to_db(round, session)
    elif len(round.holes) > 0:
        round.holes = round.holes[:-1]
        round._is_finished()
        await patch_to_db(round, session)
    

    return {
        "success": True,
        "message": round.to_string()
    }

@app.delete("/delete/round")
async def delete_round(
    session: AsyncSession = Depends(get_async_session)
) -> RoundResponse:
    global round, round_id
    if not round: return {"success":False,"message":"No round to delete!"}

    result = await session.execute(select(RoundRow).where(RoundRow.id == round_id))
    db_round = result.scalars().first()
    if db_round:
        await session.delete(db_round)
        await session.commit()

    round = None
    round_id = None
    return {
        "success": True,
        "message": "Round deleted successfully!"
    }