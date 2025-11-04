from fastapi import APIRouter

router = APIRouter()

# Ejemplo de endpoint
@router.get("/widgets/test")
def test_widget():
    return {"message": "Endpoint widgets funcionando"}
