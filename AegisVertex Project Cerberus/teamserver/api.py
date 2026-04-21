from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from typing import List

import models, db, auth, schemas, config
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.post('/auth/register', response_model=schemas.UserRead, tags=["Auth"])
async def register_operator(user_in: schemas.UserCreate, db_session: AsyncSession = Depends(db.get_db)):
    result = await db_session.execute(select(models.User).where(models.User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = auth.get_password_hash(user_in.password)
    new_user = models.User(username=user_in.username, hashed_password=hashed_pw)

    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)
    return new_user


@router.post('/auth/login', tags=["Auth"])
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db_session: AsyncSession = Depends(db.get_db)
):
    user = await auth.authenticate_user(db_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )
    refresh_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=config.settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        token_type="refresh"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": config.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post('/teams/', response_model=schemas.TeamRead, tags=["Ops"])
async def create_team(
        team_in: schemas.TeamCreate,
        current_user=Depends(auth.get_current_user),
        db_session: AsyncSession = Depends(db.get_db)
):
    new_team = models.Team(name=team_in.name, description=team_in.description)
    db_session.add(new_team)
    await db_session.commit()
    await db_session.refresh(new_team)
    return new_team


@router.get('/beacons/', response_model=List[schemas.BeaconRead], tags=["Ops"])
async def list_beacons(
        current_user=Depends(auth.get_current_user),
        db_session: AsyncSession = Depends(db.get_db)
):
    result = await db_session.execute(select(models.Beacon))
    return result.scalars().all()


@router.post('/beacons/', response_model=schemas.BeaconRead, tags=["Ops"])
async def register_beacon_manually(
        beacon_in: schemas.BeaconCreate,
        current_user=Depends(auth.get_current_user),
        db_session: AsyncSession = Depends(db.get_db)
):
    new_beacon = models.Beacon(team_id=beacon_in.team_id, name=beacon_in.name)
    db_session.add(new_beacon)
    await db_session.commit()
    await db_session.refresh(new_beacon)
    return new_beacon