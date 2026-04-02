from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.utils.deps import check_company_payment_status, get_auth_user


class PromptCreate(BaseModel):
    name: str
    category: str
    template: str
    is_active: bool = True
    description: str | None = None
    variables: list[str] = []


class PromptUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    template: str | None = None
    is_active: bool | None = None
    description: str | None = None
    variables: list[str] | None = None


class PromptPublic(BaseModel):
    id: int
    company_id: int
    name: str
    category: str
    template: str
    is_active: bool
    variables: list[str] = []
    description: str | None = None
    version: int = 1
    created_at: str
    updated_at: str


class PromptsResponse(BaseModel):
    data: list[PromptPublic]
    total: int


_PROMPTS_BY_COMPANY: dict[int, list[PromptPublic]] = {}
_PROMPT_ID_SEQ: int = 1


router = APIRouter(
    prefix="/prompts",
    tags=["Prompts"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id() -> int:
    global _PROMPT_ID_SEQ
    next_id = _PROMPT_ID_SEQ
    _PROMPT_ID_SEQ += 1
    return next_id


@router.get("/", response_model=PromptsResponse)
async def get_prompts(
    request: Request,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    is_active: bool | None = None,
):
    company_id = request.state.user.company_id
    prompts = list(_PROMPTS_BY_COMPANY.get(company_id, []))
    if is_active is not None:
        prompts = [p for p in prompts if p.is_active == is_active]
    total = len(prompts)
    return PromptsResponse(data=prompts[skip : skip + limit], total=total)


@router.get("/active", response_model=PromptPublic)
async def get_active_prompt(request: Request):
    company_id = request.state.user.company_id
    prompts = _PROMPTS_BY_COMPANY.get(company_id, [])
    active = next((p for p in prompts if p.is_active), None)
    if not active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active prompt found",
        )
    return active


@router.get("/{prompt_id}", response_model=PromptPublic)
async def get_prompt(request: Request, prompt_id: int):
    company_id = request.state.user.company_id
    prompts = _PROMPTS_BY_COMPANY.get(company_id, [])
    prompt = next((p for p in prompts if p.id == prompt_id), None)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )
    return prompt


@router.post("/", response_model=PromptPublic)
async def create_prompt(request: Request, payload: PromptCreate):
    company_id = request.state.user.company_id
    now = _now_iso()
    prompt = PromptPublic(
        id=_next_id(),
        company_id=company_id,
        name=payload.name,
        category=payload.category,
        template=payload.template,
        is_active=payload.is_active,
        variables=payload.variables or [],
        description=payload.description,
        version=1,
        created_at=now,
        updated_at=now,
    )
    prompts = _PROMPTS_BY_COMPANY.get(company_id, [])
    prompts.append(prompt)
    _PROMPTS_BY_COMPANY[company_id] = prompts
    return prompt


@router.put("/{prompt_id}", response_model=PromptPublic)
async def update_prompt(request: Request, prompt_id: int, payload: PromptUpdate):
    company_id = request.state.user.company_id
    prompts = _PROMPTS_BY_COMPANY.get(company_id, [])
    for idx, prompt in enumerate(prompts):
        if prompt.id == prompt_id:
            patch = payload.model_dump(exclude_unset=True)
            patch["version"] = prompt.version + 1
            patch["updated_at"] = _now_iso()
            updated = prompt.model_copy(update=patch)
            prompts[idx] = updated
            _PROMPTS_BY_COMPANY[company_id] = prompts
            return updated
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Prompt not found",
    )


@router.delete("/{prompt_id}")
async def delete_prompt(request: Request, prompt_id: int):
    company_id = request.state.user.company_id
    prompts = _PROMPTS_BY_COMPANY.get(company_id, [])
    before = len(prompts)
    prompts = [p for p in prompts if p.id != prompt_id]
    _PROMPTS_BY_COMPANY[company_id] = prompts
    if len(prompts) == before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )
    return {"message": "Prompt deleted"}
