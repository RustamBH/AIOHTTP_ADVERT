import json
import pydantic

from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = web.Application()
PG_DSN = "postgresql+asyncpg://app:1234@127.0.0.1:5431/app"
engine = create_async_engine(PG_DSN, echo=True)
Base = declarative_base()


class ApiError(web.HTTPException):
    def __init__(self, error_message: str | dict):
        message = json.dumps({'status': 'error', 'description': error_message})
        super(ApiError, self).__init__(text=message, content_type='application/json')


class BadRequest(ApiError):
    status_code = 400


class NotFound(ApiError):
    status_code = 404


class Advertisement(Base):
    __tablename__ = "adverts"

    id = Column(Integer, primary_key=True)
    title = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    owner = Column(String(128), nullable=False)


class CreateAdvertModel(pydantic.BaseModel):
    title: str
    description: str
    owner: str

    @pydantic.validator("title")
    def is_empty_title(cls, value: str):
        if len(value) == 0:
            raise ValueError("title can not be empty")
        return value

    @pydantic.validator("description")
    def is_empty_description(cls, value: str):
        if len(value) < 8:
            raise ValueError("description is too short")
        return value

    @pydantic.validator("owner")
    def is_empty_owner(cls, value: str):
        if len(value) == 0:
            raise ValueError("owner can not be empty")
        return value


async def get_advert(advert_id: int, session) -> Advertisement:
    advert = await session.get(Advertisement, advert_id)
    if advert is None:
        raise NotFound(message="advert not found")
    return advert


class AdvertView(web.View):
    async def get(self):
        advert_id = int(self.request.match_info["advert_id"])
        async with app.async_session_maker() as session:
            advert = await get_advert(advert_id, session)
            return web.json_response(
                {
                    "title": advert.title,
                    "description": advert.description,
                    "owner": advert.owner,
                    "date": advert.creation_time.isoformat()
                }
            )

    async def post(self):
        advert_data = await self.request.json()
        advert_data = CreateAdvertModel(**advert_data).dict()
        async with app.async_session_maker() as session:
            try:
                new_advert = Advertisement(**advert_data)
                session.add(new_advert)
                await session.commit()
                # return web.json_response({"id": new_advert.id})
            except IntegrityError as er:
                raise BadRequest(message="advert already exists")
            return web.json_response({"id": new_advert.id})

    async def delete(self):
        advert_id = int(self.request.match_info["advert_id"])
        async with app.async_session_maker() as session:
            advert = await get_advert(advert_id, session)
            await session.delete(advert)
            await session.commit()
            return web.json_response({"status": "success"})


async def init_orm(app: web.Application):
    print("Приложение стартовало")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async_session_maker = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        app.async_session_maker = async_session_maker
        yield
    print("Приложение завершило работу")


app.cleanup_ctx.append(init_orm)
app.add_routes([web.get("/advert/{advert_id:\d+}", AdvertView)])
app.add_routes([web.delete("/advert/{advert_id:\d+}", AdvertView)])
app.add_routes([web.post("/advert/", AdvertView)])
web.run_app(app)
