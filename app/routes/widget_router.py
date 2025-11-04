from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.widget_model import Widget, WidgetBase
from app.core.db import get_db as get_session

router = APIRouter()

# Endpoint de test (puedes quitarlo después)
@router.get("/widgets/test")
async def test_widget():
    return {"message": "Endpoint widgets funcionando"}

# Endpoint para crear un widget
@router.post("/widgets/", response_model=Widget)
async def create_widget(widget: WidgetBase, session: AsyncSession = Depends(get_session)):
    db_widget = Widget.from_orm(widget)
    session.add(db_widget)
    await session.commit()
    await session.refresh(db_widget)
    return db_widget

# Endpoint para listar todos los widgets
@router.get("/widgets/", response_model=list[Widget])
async def list_widgets(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Widget))
    widgets = result.scalars().all()
    return widgets

# Endpoint para consultar un widget por ID
@router.get("/widgets/{widget_id}", response_model=Widget)
async def get_widget(widget_id: int, session: AsyncSession = Depends(get_session)):
    widget = await session.get(Widget, widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget
