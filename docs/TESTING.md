# SIETE CX - TESTING DOCUMENTATION

**Version:** 1.0  
**Last Updated:** January 2025  
**Coverage Target:** 80%+

---

## TABLE OF CONTENTS

1. [Testing Strategy](#1-testing-strategy)
2. [Backend Testing (Pytest)](#2-backend-testing-pytest)
3. [Frontend Testing (Jasmine/Karma)](#3-frontend-testing-jasminekarma)
4. [Integration Testing](#4-integration-testing)
5. [E2E Testing](#5-e2e-testing)
6. [Performance Testing](#6-performance-testing)
7. [CI/CD Testing](#7-cicd-testing)

---

## 1. TESTING STRATEGY

### 1.1 Testing Pyramid

```
         /\
        /E2E\          10% - Full user flows
       /------\
      /  API   \       20% - Integration tests
     /----------\
    /   UNIT     \     70% - Unit tests
   /--------------\
```

### 1.2 Coverage Goals

- **Unit Tests:** 80%+ coverage
- **Integration Tests:** Critical paths covered
- **E2E Tests:** Core user journeys
- **API Tests:** All endpoints tested

### 1.3 Testing Tools

**Backend:**
- pytest (test runner)
- pytest-asyncio (async tests)
- pytest-cov (coverage)
- httpx (API testing)
- faker (test data)

**Frontend:**
- Jasmine (test framework)
- Karma (test runner)
- Protractor/Playwright (E2E)
- Angular Testing Utilities

---

## 2. BACKEND TESTING (Pytest)

### 2.1 Setup

**Install dependencies:**
```bash
cd /app/cx-backend
pip install pytest pytest-asyncio pytest-cov httpx faker
```

**Configuration:** `/app/cx-backend/tests/conftest.py`
- Database fixtures
- Test data generators
- Session management

### 2.2 Running Tests

**All tests:**
```bash
pytest
```

**With coverage:**
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

**Specific test file:**
```bash
pytest tests/test_users.py -v
```

**Watch mode:**
```bash
pytest-watch
```

### 2.3 Test Structure

```
tests/
├── conftest.py              # Fixtures and configuration
├── test_users.py            # User service tests
├── test_auth.py             # Authentication tests
├── test_campaigns.py        # Campaign tests
├── test_evaluations.py      # Evaluation tests
├── test_intelligence.py     # Intelligence engine tests
├── test_dashboard.py        # Dashboard tests
└── test_api_endpoints.py    # API integration tests
```

### 2.4 Example Unit Test

```python
import pytest
from app.services.intelligence_services import generate_insights_from_analysis

@pytest.mark.asyncio
async def test_generate_insights_high_ird(db_session):
    """Test insight generation for high IRD score"""
    
    # Mock analysis with high IRD
    mock_analysis = MockAnalysis(
        operative_view={
            "IRD": {"score": 85, "justificacion": "Cliente insatisfecho"},
            "CES": {"score": 30},
            "IOC": {"score": 50}
        }
    )
    
    # Generate insights
    insights = await generate_insights_from_analysis(
        db_session,
        evaluation_id=1,
        analysis=mock_analysis,
        company_id=1
    )
    
    # Assertions
    assert len(insights) >= 1
    assert any(i.insight_type == "ird_alert" for i in insights)
    assert any(i.severity == "high" for i in insights)
```

### 2.5 Example API Test

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_campaign_endpoint():
    """Test campaign creation endpoint"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login to get token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "password"}
        )
        token = login_response.json()["access_token"]
        
        # Create campaign
        response = await client.post(
            "/api/v1/campaigns",
            json={
                "name": "Q1 2025 Campaign",
                "description": "Test campaign",
                "company_id": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Q1 2025 Campaign"
```

### 2.6 Test Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html
```

---

## 3. FRONTEND TESTING (JASMINE/KARMA)

### 3.1 Setup

**Angular testing is built-in:**
```bash
cd /app/cx-frontend
npm install
```

### 3.2 Running Tests

**All tests:**
```bash
ng test
```

**Single run (CI):**
```bash
ng test --watch=false --code-coverage
```

**Specific test:**
```bash
ng test --include='**/dashboard.component.spec.ts'
```

### 3.3 Example Component Test

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { DashboardService } from '../../services/dashboard.service';
import { of } from 'rxjs';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let dashboardService: jasmine.SpyObj<DashboardService>;

  beforeEach(async () => {
    const dashboardServiceSpy = jasmine.createSpyObj('DashboardService', ['getDashboard']);

    await TestBed.configureTestingModule({
      declarations: [ DashboardComponent ],
      providers: [
        { provide: DashboardService, useValue: dashboardServiceSpy }
      ]
    })
    .compileComponents();

    dashboardService = TestBed.inject(DashboardService) as jasmine.SpyObj<DashboardService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load dashboard data on init', () => {
    const mockData = {
      total_evaluations: 100,
      completed_evaluations: 80,
      avg_nps: 8.5
    };
    dashboardService.getDashboard.and.returnValue(of(mockData));

    component.ngOnInit();

    expect(dashboardService.getDashboard).toHaveBeenCalled();
    expect(component.dashboardData).toEqual(mockData);
  });
});
```

### 3.4 Example Service Test

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthService]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should login successfully', () => {
    const mockResponse = {
      access_token: 'test-token',
      user: { id: 1, email: 'test@example.com' }
    };

    service.login('test@example.com', 'password').subscribe(response => {
      expect(response.access_token).toBe('test-token');
    });

    const req = httpMock.expectOne(`${service.apiUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
  });
});
```

---

## 4. INTEGRATION TESTING

### 4.1 API Integration Tests

**Test full request-response cycle:**

```python
@pytest.mark.asyncio
async def test_evaluation_workflow():
    """Test complete evaluation workflow"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Login
        token = await get_auth_token(client)
        
        # 2. Create campaign
        campaign = await create_campaign(client, token)
        
        # 3. Submit evaluation
        evaluation = await submit_evaluation(client, token, campaign.id)
        
        # 4. Wait for analysis (mock)
        await trigger_analysis(evaluation.id)
        
        # 5. Get analysis results
        response = await client.get(
            f"/api/v1/evaluation-analysis/{evaluation.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        analysis = response.json()
        assert "executive_view" in analysis
        assert "operative_view" in analysis
```

### 4.2 Database Integration Tests

**Test with real PostgreSQL:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_cascade_delete():
    """Test cascade delete behavior"""
    
    # Create company → campaign → evaluation
    company = await create_test_company(session)
    campaign = await create_test_campaign(session, company.id)
    evaluation = await create_test_evaluation(session, campaign.id)
    
    # Delete company (should cascade)
    await delete_company(session, company.id)
    
    # Verify cascade
    assert await get_campaign(session, campaign.id) is None
    assert await get_evaluation(session, evaluation.id) is None
```

---

## 5. E2E TESTING

### 5.1 Playwright Setup

```bash
cd /app/cx-frontend
npm install --save-dev @playwright/test
npx playwright install
```

### 5.2 Example E2E Test

```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:4200/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should display dashboard metrics', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="total-evaluations"]');
    
    // Check KPI cards
    const totalEvaluations = await page.textContent('[data-testid="total-evaluations"]');
    expect(parseInt(totalEvaluations!)).toBeGreaterThan(0);
    
    // Check chart is rendered
    await expect(page.locator('canvas')).toBeVisible();
  });

  test('should filter evaluations by status', async ({ page }) => {
    await page.click('[data-testid="filter-dropdown"]');
    await page.click('text=Completed');
    
    // Wait for filtered results
    await page.waitForSelector('[data-testid="evaluation-row"]');
    
    const rows = await page.locator('[data-testid="evaluation-row"]').count();
    expect(rows).toBeGreaterThan(0);
  });
});
```

---

## 6. PERFORMANCE TESTING

### 6.1 Load Testing (Locust)

```python
from locust import HttpUser, task, between

class SieteCXUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def view_dashboard(self):
        self.client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def view_evaluations(self):
        self.client.get(
            "/api/v1/evaluations",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

**Run:**
```bash
locust -f tests/performance/locustfile.py --host=https://cx-api.sieteic.com
```

---

## 7. CI/CD TESTING

### 7.1 GitHub Actions Workflow

See `.github/workflows/deploy.yml` for complete CI/CD pipeline.

**Test stages:**
1. ✅ Linting (ruff)
2. ✅ Unit tests (pytest)
3. ✅ Coverage report
4. ✅ Integration tests
5. ✅ Deployment
6. ✅ Health check

### 7.2 Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install
```

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

---

## APPENDIX A: Test Data Generators

```python
from faker import Faker
import random

fake = Faker()

def generate_test_user():
    return {
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "role": random.choice([1, 2, 3]),
        "password": "TestPassword123"
    }

def generate_test_evaluation():
    return {
        "location": fake.address(),
        "evaluated_collaborator": fake.name(),
        "status": random.choice(["completed", "pending", "analyzing"])
    }
```

---

## APPENDIX B: Coverage Badge

**Add to README.md:**
```markdown
[![codecov](https://codecov.io/gh/juanfamilia/cx-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/juanfamilia/cx-backend)
```

---

**End of Testing Documentation**

For deployment instructions, see `DEPLOYMENT.md`.
