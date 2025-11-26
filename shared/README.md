# Siete CX - Shared Library

## 📦 ¿Qué es Shared?

Librería transversal que contiene:
- **SQLModel schemas**: Definiciones de tablas DB compartidas entre servicios
- **Services**: Lógica de negocio reutilizable
- **Core**: Configuración, DB connection, security
- **Utils**: Helpers para validación, deps, etc.

## 🚀 Instalación (Desarrollo Local)

```bash
# Desde raíz del monorepo
pip install -e ./shared

# Verificar instalación
python -c "from shared.models.user_model import User; print('✅ Shared installed correctly')"
```

## 📖 Uso Básico

### Ejemplo 1: Importar Modelo de DB

```python
# En app/routes/ o analysis/services/
from shared.models.user_model import User, UserCreate

async def create_user(db: AsyncSession, user_data: UserCreate):
    user = User(**user_data.dict())
    db.add(user)
    await db.commit()
    return user
```

### Ejemplo 2: Usar Servicios Compartidos

```python
# En app/routes/evaluation_router.py
from shared.services.evaluation_services import get_evaluation

async def get_evaluation_route(evaluation_id: int, db: AsyncSession):
    evaluation = await get_evaluation(db, evaluation_id)
    return evaluation
```

## ⚠️ Errores Frecuentes

### Error 1: `ModuleNotFoundError: No module named 'shared'`

**Causa:** No instalaste shared o lo instalaste en virtualenv diferente

**Fix:**
```bash
# Asegúrate de estar en el virtualenv correcto
which python  # Debe ser /path/to/venv/bin/python

# Reinstalar shared
pip install -e ./shared
```

### Error 2: `ImportError: cannot import name 'User' from 'shared.models'`

**Causa:** Imports circulares o estructura incorrecta

**Fix:** Siempre importa desde el módulo específico:
```python
# ❌ Incorrecto
from shared.models import User

# ✅ Correcto
from shared.models.user_model import User
```

## 🔄 Actualizar Shared

Si modificas shared, **SIEMPRE**:
1. Verificar que no rompiste imports: `python -c "from shared.models import *"`
2. Actualizar `CHANGELOG.md` si hay cambios significativos
3. Considerar bump de versión en `pyproject.toml`

## 📞 Estructura

```
shared/
├── pyproject.toml          # Package definition
├── setup.py                # Setuptools config
├── README.md               # This file
├── core/
│   ├── config.py           # Settings (Pydantic)
│   ├── db.py               # Database session
│   └── security.py         # JWT, password hashing
├── models/
│   ├── user_model.py
│   ├── evaluation_model.py
│   └── ...                 # All SQLModel schemas
├── services/
│   ├── evaluation_services.py
│   ├── users_services.py
│   └── ...                 # Business logic
├── utils/
│   ├── deps.py             # FastAPI dependencies
│   └── helpers/
└── types/
    └── pagination.py       # Shared type definitions
```

## 🎯 Principios

1. **Shared contiene lógica reutilizable**: Si se usa en 2+ servicios, va en shared
2. **No dependencias pesadas**: Shared solo tiene FastAPI, SQLModel, Pydantic
3. **Imports internos**: Dentro de shared, usa `from shared.models.xxx`
4. **Versionado semántico**: Breaking changes = major bump
