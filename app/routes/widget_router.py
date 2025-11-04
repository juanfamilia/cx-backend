from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.widget_model import Widget, WidgetBase
from app.core.db import get_session

router = APIRouter()

# Endpoint de test (puedes quitarlo después)
@router.get("/widgets/test")
def test_widget():
    return {"message": "Endpoint widgets funcionando"}

# Endpoint para crear un widget
@router.post("/widgets/", response_model=Widget)
def create_widget(widget: WidgetBase, session: Session = Depends(get_session)):
    db_widget = Widget.from_orm(widget)
    session.add(db_widget)
    session.commit()
    session.refresh(db_widget)
    return db_widget

# Endpoint para listar todos los widgets
@router.get("/widgets/", response_model=list[Widget])
def list_widgets(session: Session = Depends(get_session)):
    widgets = session.exec(select(Widget)).all()
    return widgets

# Endpoint para consultar un widget por ID
@router.get("/widgets/{widget_id}", response_model=Widget)
def get_widget(widget_id: int, session: Session = Depends(get_session)):
    widget = session.get(Widget, widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget
