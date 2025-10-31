"""
Test cases for user services
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import UserCreate
from app.models.company_model import CompanyCreate
from app.services.users_services import create_user, get_user_by_email
from app.services.company_services import create_company


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession, test_user_data, test_company_data):
    """Test user creation"""
    
    # First create a company
    company = await create_company(db_session, CompanyCreate(**test_company_data))
    
    # Create user
    test_user_data["company_id"] = company.id
    user = await create_user(db_session, UserCreate(**test_user_data))
    
    assert user.id is not None
    assert user.email == test_user_data["email"]
    assert user.first_name == test_user_data["first_name"]
    assert user.role == test_user_data["role"]


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession, test_user_data, test_company_data):
    """Test getting user by email"""
    
    # Create company and user
    company = await create_company(db_session, CompanyCreate(**test_company_data))
    test_user_data["company_id"] = company.id
    created_user = await create_user(db_session, UserCreate(**test_user_data))
    
    # Retrieve user by email
    retrieved_user = await get_user_by_email(db_session, test_user_data["email"])
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email


@pytest.mark.asyncio
async def test_user_password_hashing(db_session: AsyncSession, test_user_data, test_company_data):
    """Test that passwords are properly hashed"""
    
    company = await create_company(db_session, CompanyCreate(**test_company_data))
    test_user_data["company_id"] = company.id
    user = await create_user(db_session, UserCreate(**test_user_data))
    
    # Password should be hashed, not plain text
    assert user.hashed_password != test_user_data["password"]
    assert len(user.hashed_password) > 50  # Bcrypt hashes are long
