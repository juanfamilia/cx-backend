from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.prompt_manager_model import (
    PromptManager,
    PromptManagerCreate,
    PromptManagerUpdate,
    PromptManagerPublic,
    PromptManagersPublic,
)
from app.utils.exeptions import NotFoundException


async def get_prompt_by_id(
    session: AsyncSession, prompt_id: int
) -> PromptManagerPublic:
    """Get a specific prompt by ID"""
    query = select(PromptManager).where(
        PromptManager.id == prompt_id,
        
    )
    result = await session.execute(query)
    prompt = result.scalars().first()
    
    if not prompt:
        raise NotFoundException("Prompt not found")
    
    return prompt


async def get_active_prompt_for_company(
    session: AsyncSession, company_id: int, category: str = "dual_analysis"
) -> PromptManagerPublic | None:
    """Get the active prompt for a company by category"""
    query = select(PromptManager).where(
        PromptManager.company_id == company_id,
        PromptManager.category == category,
        PromptManager.is_active == True,
        
    )
    result = await session.execute(query)
    prompt = result.scalars().first()
    
    return prompt


async def get_prompts_by_company(
    session: AsyncSession, 
    company_id: int,
    offset: int = 0,
    limit: int = 10
) -> PromptManagersPublic:
    """Get all prompts for a company with pagination"""
    
    # Count query
    count_query = select(func.count(PromptManager.id)).where(
        PromptManager.company_id == company_id
    )
    count_result = await session.execute(count_query)
    total = count_result.scalar()
    
    # Data query
    query = (
        select(PromptManager)
        .where(
            PromptManager.company_id == company_id
        )
        .offset(offset)
        .limit(limit)
        .order_by(PromptManager.created_at.desc())
    )
    result = await session.execute(query)
    prompts = result.scalars().all()
    
    return PromptManagersPublic(data=prompts, total=total)


async def create_prompt(
    session: AsyncSession, prompt_data: PromptManagerCreate
) -> PromptManagerPublic:
    """Create a new prompt"""
    
    # If this prompt is active, deactivate other prompts of same category
    if prompt_data.is_active:
        await deactivate_company_prompts(
            session, 
            prompt_data.company_id, 
            prompt_data.category
        )
    
    db_prompt = PromptManager(**prompt_data.model_dump())
    session.add(db_prompt)
    await session.commit()
    await session.refresh(db_prompt)
    
    return db_prompt


async def update_prompt(
    session: AsyncSession, prompt_id: int, prompt_data: PromptManagerUpdate
) -> PromptManagerPublic:
    """Update an existing prompt"""
    db_prompt = await get_prompt_by_id(session, prompt_id)
    
    # If activating this prompt, deactivate others of same category
    if prompt_data.is_active and not db_prompt.is_active:
        await deactivate_company_prompts(
            session,
            db_prompt.company_id,
            db_prompt.category,
            exclude_id=prompt_id
        )
    
    update_data = prompt_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    
    session.add(db_prompt)
    await session.commit()
    await session.refresh(db_prompt)
    
    return db_prompt


async def deactivate_company_prompts(
    session: AsyncSession,
    company_id: int,
    category: str,
    exclude_id: int | None = None
):
    """Deactivate all prompts of a category for a company (except one)"""
    query = select(PromptManager).where(
        PromptManager.company_id == company_id,
        PromptManager.category == category,
        PromptManager.is_active == True,
        
    )
    
    if exclude_id:
        query = query.where(PromptManager.id != exclude_id)
    
    result = await session.execute(query)
    prompts = result.scalars().all()
    
    for prompt in prompts:
        prompt.is_active = False
        session.add(prompt)
    
    await session.commit()


async def soft_delete_prompt(
    session: AsyncSession, prompt_id: int
) -> PromptManagerPublic:
    """Soft delete a prompt by deactivating it (deleted_at field doesn't exist in schema)"""
    db_prompt = await get_prompt_by_id(session, prompt_id)
    db_prompt.is_active = False
    
    session.add(db_prompt)
    await session.commit()
    await session.refresh(db_prompt)
    
    return db_prompt
