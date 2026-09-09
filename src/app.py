from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.models import Shot, Hole, Round
from src.schemas import ShotData, RoundResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import RoundRow, create_db_and_tables, get_async_session
from sqlalchemy import select

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
    result = await session.execute(select(RoundRow).where(RoundRow.id == round_id))
    current_round = result.scalars().first()
    current_round.data = round.to_dict()
    current_round.is_finished = round.is_finished
    await session.commit()


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
round_id: str = None

@app.post("/receive") 
async def receive_data(
    data: ShotData,
    session: AsyncSession = Depends(get_async_session)
) -> RoundResponse:
    global round, round_id

    if not round and not data.course:
        raise HTTPException(status_code=400, detail="You must provide a course name!")

    print(data)
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

    elif len(round.holes) == shot.hole:
        round.holes[shot.hole-1].add_shot(shot)
        await patch_to_db(round, session)
    else:
        round.add_hole(Hole(shot.hole, shot))
        await patch_to_db(round, session)


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

    result = await session.execute(select(RoundRow).where(RoundRow.is_finished == False))
    current_round = result.scalars().first()

    if current_round:
        round = Round.from_dict(data=current_round.data)
        round_id = current_round.id
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
    if not round: return {"success":False,"message":"No shot to delete!"}

    round.holes[len(round.holes)-1].delete_last_shot()
    await patch_to_db(round=round, session=session)

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
    await session.delete(db_round)
    session.commit()

    round = None
    round_id = None
    return {
        "success": True,
        "message": "Round deleted successfully!"
    }