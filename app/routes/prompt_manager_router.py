from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.prompt_manager_model import (
    PromptManagerCreate,
    PromptManagerUpdate,
    PromptManagerPublic,
    PromptManagersPublic,
)
from app.services.prompt_manager_services import (
    get_prompt_by_id,
    get_prompts_by_company,
    create_prompt,
    update_prompt,
    soft_delete_prompt,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/prompts",
    tags=["Prompt Manager"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_company_prompts(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=50),
) -> PromptManagersPublic:
    """Get all prompts for the authenticated user's company"""
    
    # Only admins and superadmins can manage prompts
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="view prompts")
    
    company_id = request.state.user.company_id
    if request.state.user.role == 0:
        # Superadmin should specify company_id via query param
        raise PermissionDeniedException(
            custom_message="specify company_id for superadmin access"
        )
    
    prompts = await get_prompts_by_company(session, company_id, offset, limit)
    return prompts


@router.get("/{prompt_id}")
async def get_prompt(
    request: Request,
    prompt_id: int,
    session: AsyncSession = Depends(get_db),
) -> PromptManagerPublic:
    """Get a specific prompt by ID"""
    
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="view this prompt")
    
    prompt = await get_prompt_by_id(session, prompt_id)
    
    # Check if user has access to this company's prompt
    if request.state.user.role == 1:
        if prompt.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="view this prompt")
    
    return prompt


@router.post("/")
async def create_new_prompt(
    request: Request,
    prompt_data: PromptManagerCreate,
    session: AsyncSession = Depends(get_db),
) -> PromptManagerPublic:
    """Create a new AI prompt for a company"""
    
    # Only admins can create prompts (superadmins use company_id in payload)
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="create prompts")
    
    # Ensure admin can only create for their own company
    if request.state.user.role == 1:
        if prompt_data.company_id != request.state.user.company_id:
            raise PermissionDeniedException(
                custom_message="create prompts for other companies"
            )
    
    prompt = await create_prompt(session, prompt_data)
    return prompt


@router.put("/{prompt_id}")
async def update_existing_prompt(
    request: Request,
    prompt_id: int,
    prompt_data: PromptManagerUpdate,
    session: AsyncSession = Depends(get_db),
) -> PromptManagerPublic:
    """Update an existing prompt"""
    
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="update prompts")
    
    # Check ownership
    db_prompt = await get_prompt_by_id(session, prompt_id)
    if request.state.user.role == 1:
        if db_prompt.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="update this prompt")
    
    prompt = await update_prompt(session, prompt_id, prompt_data)
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(
    request: Request,
    prompt_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Soft delete a prompt"""
    
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="delete prompts")
    
    # Check ownership
    db_prompt = await get_prompt_by_id(session, prompt_id)
    if request.state.user.role == 1:
        if db_prompt.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="delete this prompt")
    
    await soft_delete_prompt(session, prompt_id)
    return {"message": "Prompt deleted successfully"}
