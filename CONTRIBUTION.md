# Contributing to DKBlytics 🤝

This document provides comprehensive guidelines for contributing to DKBlytics, whether you're a human developer or an AI assistant like Claude. It covers our development workflow, code conventions, architectural patterns, and best practices.

## 🎯 **Development Philosophy**

DKBlytics follows a **full-stack integrated approach** with:
- **Backend-first design** - API endpoints drive frontend features
- **Consistent patterns** - Established conventions across both tiers
- **User-centric features** - Every change should improve the user experience
- **Maintainable code** - Clear, documented, and testable implementations

---

## 🔧 **Development Environment Setup**

### **Prerequisites**
- Python 3.11+
- `uv` package manager (strongly recommended)
- Git for version control
- IDE with Python support (VS Code recommended)

### **Initial Setup**

1. **Clone and Branch**
   ```bash
   git clone https://github.com/your-username/DKBlytics.git
   cd DKBlytics
   git checkout -b feature/your-feature-name
   ```

2. **Backend Environment**
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   uv pip install pytest pytest-cov  # For testing
   ```

3. **Frontend Environment**
   ```bash
   cd ../frontend-nicegui
   uv add "nicegui[highcharts]"
   uv pip install -e .
   ```

4. **Database Setup**
   ```bash
   cd ../backend
   python -m src.main  # Creates SQLite database with tables
   ```

### **Development Workflow**

1. **Start Backend** (Terminal 1)
   ```bash
   cd backend
   python -m src.main
   # API: http://localhost:8000
   # Docs: http://localhost:8000/docs
   ```

2. **Start Frontend** (Terminal 2)  
   ```bash
   cd frontend-nicegui
   python -m app.main
   # Web UI: http://localhost:8081
   ```

3. **Run Tests**
   ```bash
   cd backend
   pytest tests/ -v
   pytest tests/ --cov=src --cov-report=html  # With coverage
   ```

---

## 🏗️ **Architecture Patterns**

### **Backend Architecture (FastAPI)**

#### **Layered Structure**
```
backend/src/
├── routers/     # API endpoints (thin layer, validation only)
├── services/    # Business logic (core functionality)  
├── models.py    # SQLAlchemy ORM models
├── schemas.py   # Pydantic request/response schemas
└── database.py  # Database session management
```

#### **API Endpoint Pattern**
```python
# routers/example.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import ItemCreate, Item
from ..services.items import create_item_db, get_item_db

router = APIRouter(prefix="/items", tags=["Items"])

@router.post("/", response_model=Item, status_code=201)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db)
) -> Item:
    try:
        return create_item_db(db, payload)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### **Service Layer Pattern**
```python
# services/items.py
from sqlalchemy.orm import Session
from ..models import Item as ItemORM
from ..schemas import ItemCreate, Item
from ..utils import NotFound

def create_item_db(db: Session, payload: ItemCreate) -> Item:
    # Business logic here
    item = ItemORM(**payload.model_dump())
    db.add(item)
    db.flush()
    return Item.model_validate(item)
```

### **Frontend Architecture (NiceGUI)**

#### **Page Structure Pattern**
```python
# pages/example.py
from nicegui import ui
from app.api.items import get_items
from app.utils import create_empty_state, create_error_message
from app.constants import CSS_CLASSES

def render_example_page():
    """Main page render function."""
    ui.label("Page Title").classes(CSS_CLASSES['page_title'])
    
    # State containers
    controls_container = ui.column().classes('mb-4')
    content_container = ui.column()
    
    # Filter state
    current_filters = {'key': 'default_value'}
    
    def load_data():
        """Load and display data."""
        content_container.clear()
        try:
            data = get_items(**current_filters)
            create_data_view(content_container, data)
        except Exception as e:
            create_error_message(content_container, f"Error: {str(e)}")
    
    # Create UI components
    create_filters(controls_container, current_filters, load_data)
    load_data()  # Initial load
```

#### **Component Reuse Pattern**
```python
# components/data_table.py
from nicegui import ui
from typing import List, Dict, Callable

def create_data_table(
    container, 
    data: List[Dict],
    columns: List[Dict],
    on_select: Callable = None
):
    """Reusable data table component."""
    with container:
        table = ui.table(columns=columns, rows=data)
        if on_select:
            table.on('selection', on_select)
        return table
```

---

## 🎨 **Code Style & Conventions**

### **Python Code Style**

#### **General Guidelines**
- **PEP 8 compliance** - Use consistent formatting
- **Type hints** - All function parameters and returns
- **Docstrings** - Document all public functions and classes
- **No unused imports** - Keep imports clean and necessary

#### **Naming Conventions**
```python
# Classes: PascalCase
class TransactionService:
    pass

# Functions/variables: snake_case  
def get_transaction_by_id():
    pass

current_balance = 0

# Constants: UPPER_SNAKE_CASE
API_BASE_URL = "http://localhost:8000"

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

#### **Function Documentation**
```python
def create_category_rule_db(
    db: Session, 
    rule: CategoryRuleCreate
) -> CategoryRule:
    """Create a new category rule in the database.
    
    Args:
        db: Database session
        rule: Category rule creation payload
        
    Returns:
        CategoryRule: Created rule with resolved category name
        
    Raises:
        NotFound: If referenced category doesn't exist
        Conflict: If rule with same (entity, text) already exists
    """
```

### **Database Patterns**

#### **Model Definition**
```python
# models.py
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(1000), nullable=False)
    entity = Column(String(500), nullable=False, index=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Foreign keys
    account_id = Column(String, ForeignKey("accounts.public_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
```

#### **Pydantic Schema Pattern**
```python
# schemas.py
class TransactionCreate(AppBaseModel):
    """Payload to create a transaction."""
    text: str = Field(..., max_length=1000, description="Transaction description")
    entity: str = Field(..., max_length=500, description="Counterparty name")
    amount: Decimal = Field(..., description="Signed amount")
    date: dt.date = Field(..., description="Booking date")

class Transaction(AppBaseModel):
    """Transaction as returned by API."""
    id: int
    text: str
    entity: str 
    amount: Decimal
    date: dt.date
    category: Optional[str] = None  # Resolved from rules
```

### **Frontend Patterns**

#### **State Management**
```python
# Use dictionaries for reactive state
current_filters = {
    'date_from': None,
    'date_to': None,
    'category': None
}

# Bind UI elements to state
date_input.bind_value(current_filters, 'date_from')
category_select.bind_value(current_filters, 'category')
```

#### **Error Handling**
```python
def load_data():
    container.clear()
    try:
        data = api_call()
        display_success(container, data)
    except Exception as e:
        create_error_message(container, f"Error loading data: {str(e)}")
```

#### **API Client Pattern**
```python
# api/client.py base pattern
class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        # Implementation with error handling
        pass
```

---

## 🧪 **Testing Guidelines**

### **Backend Testing Strategy**

#### **🎯 Core Testing Principles**

1. **Preserve Test Data Integrity** - Tests should NOT make permanent changes to test database
2. **Use Mock Data First** - Define expected test scenarios in JSON mock files
3. **Clean Up Temporary Changes** - Any dynamic test changes must be reverted
4. **Run Complete Test Suite** - Always run full test suite; individual test files depend on setup

#### **📁 Test Structure & Execution**

```bash
# ALWAYS run complete test suite (tests have dependencies)
cd backend
uv run pytest tests/ -v

# NEVER run individual test files (will fail due to missing setup)
# ❌ pytest tests/endpoints/test_category_rules.py  # Don't do this
# ✅ pytest tests/ -v                                # Always do this
```

#### **🗂️ Mock Data Strategy**

**Using JSON Mock Files for Happy Path Testing**

```json
// tests/mock_data/category_rules.json
[
    {
        "text": null,
        "entity": "Edeka", 
        "category_name": "Groceries"
    },
    {
        "transaction_id": 2,
        "entity": null,
        "text": null,
        "category_name": "Car"
    }
]
```

**Benefits of Mock Data Approach:**
- ✅ **Predictable**: Tests relate to stable, known data
- ✅ **Non-destructive**: No permanent database changes
- ✅ **Comprehensive**: Tests complex scenarios like rule hierarchy
- ✅ **Maintainable**: Easy to add new test cases

#### **🔄 Temporary Test Pattern**

For testing edge cases that require dynamic data:

```python
@pytest.mark.order(34)  
def test_transaction_rule_priority_temporarily(client):
    """Test with temporary rule that gets cleaned up."""
    # Get original state
    response = client.get("/api/transactions/1")
    original_tx = response.json()
    original_category = original_tx["category"]
    
    # Create temporary rule
    temp_rule_payload = {
        "transaction_id": 1,
        "entity": None,
        "text": None,
        "category_name": "TempCategory"
    }
    
    create_response = client.post("/api/rules/", json=temp_rule_payload)
    assert create_response.status_code == 201
    rule_id = create_response.json()["id"]
    
    try:
        # Test the temporary change
        response = client.get("/api/transactions/1")
        updated_tx = response.json()
        assert updated_tx["category"] == "TempCategory"
        
    finally:
        # ALWAYS clean up - this is critical!
        client.delete(f"/api/rules/{rule_id}")
        
        # Verify cleanup worked
        response = client.get("/api/transactions/1")
        restored_tx = response.json()
        assert restored_tx["category"] == original_category
```

#### **🏗️ Test Implementation Patterns**

**1. Parametrized Tests with Mock Data**
```python
with open(Path(__file__).parent / "../mock_data/category_rules.json") as f:
    CATEGORY_RULES = json.load(f)

@pytest.mark.parametrize(
    "payload", 
    [pytest.param(c, id=c.get("entity", f"tx_{c.get('transaction_id')}")) 
     for c in CATEGORY_RULES]
)
def test_create_category_rule(client, payload):
    response = client.post("/api/rules/", json=payload)
    assert response.status_code == 201, response.text
```

**2. Skip Transaction-Specific Rules in Entity Tests**
```python
@pytest.mark.parametrize(
    "payload", 
    [pytest.param(c, id=c.get("entity")) for c in CATEGORY_RULES 
     if c.get("entity") is not None]  # Skip transaction-only rules
)
def test_resolve_category_rule(client, payload):
    # Only test entity-based rules in resolution endpoint
    pass
```

**3. Mock Data Testing for Complex Scenarios**
```python
def test_transaction_rule_from_mock_data(client):
    """Test rule hierarchy using predefined mock data."""
    # Transaction ID 2 should be overridden by transaction rule
    response = client.get("/api/transactions/2")
    transaction = response.json()
    
    # Verify transaction rule takes precedence over entity rule
    assert transaction["entity"] == "Edeka"    # Original entity
    assert transaction["category"] == "Car"    # Overridden by transaction rule
    
    # Verify rule exists in database
    rules_response = client.get("/api/rules/")
    rules = rules_response.json()
    
    transaction_rule = next(
        (rule for rule in rules if rule.get("transaction_id") == 2), 
        None
    )
    assert transaction_rule is not None
    assert transaction_rule["category_name"] == "Car"
```

#### **⚠️ Testing Anti-Patterns to Avoid**

❌ **Don't Create Permanent Test Data**
```python
# Bad: Leaves permanent changes
def test_bad_approach(client):
    client.post("/api/rules/", json={"entity": "Test", "category": "Test"})
    # No cleanup - breaks other tests!
```

❌ **Don't Run Individual Test Files**
```bash
# Bad: Missing dependencies
pytest tests/endpoints/test_category_rules.py
```

❌ **Don't Assume Test Data State**
```python
# Bad: Assumes specific transaction exists
def test_bad_assumption(client):
    response = client.get("/api/transactions/999")  # May not exist
    # Should check existence or use known mock data
```

#### **✅ Testing Best Practices**

✅ **Always Clean Up Dynamic Changes**
```python
try:
    # Test logic here
    pass
finally:
    # Always clean up, even if test fails
    cleanup_test_data()
```

✅ **Use Existing Mock Data for Happy Path**
```python
# Good: Use predefined test scenarios
def test_with_mock_data(client):
    # Test scenarios already defined in JSON mock files
    pass
```

✅ **Verify Before and After States**
```python
def test_temporary_change(client):
    # 1. Get original state
    original = get_original_state()
    
    # 2. Make temporary change
    # 3. Test the change
    # 4. Clean up
    # 5. Verify restoration
    
    restored = get_restored_state() 
    assert restored == original
```

### **Test Categories**
- **Mock Data Tests** - Happy path scenarios using predefined JSON data
- **Temporary Tests** - Edge cases with proper cleanup
- **Error Tests** - Invalid inputs and constraint violations
- **Integration Tests** - Full API endpoint testing with database

### **Frontend Testing**

Frontend testing is primarily **manual testing** through the web interface:

1. **Feature Testing**
   - Create transactions and verify categorization
   - Test filtering and pagination
   - Verify chart data accuracy

2. **Error Testing**
   - Test with invalid inputs
   - Test network error scenarios
   - Verify error message display

3. **UI/UX Testing**
   - Test responsive design
   - Verify accessibility
   - Check loading states

---

## 🚀 **Adding New Features**

### **Full-Stack Feature Development**

#### **1. Backend First Approach**

1. **Define the API Contract**
   ```python
   # schemas.py - Define request/response models
   class NewFeatureCreate(AppBaseModel):
       field: str = Field(..., description="Description")
   
   class NewFeature(AppBaseModel):
       id: int
       field: str
   ```

2. **Create Database Models** (if needed)
   ```python
   # models.py - Add new database tables
   class NewFeature(Base):
       __tablename__ = "new_features"
       id = Column(Integer, primary_key=True)
       field = Column(String(255), nullable=False)
   ```

3. **Implement Service Layer**
   ```python
   # services/new_feature.py - Business logic
   def create_new_feature_db(db: Session, payload: NewFeatureCreate):
       # Implementation
       pass
   ```

4. **Add API Endpoints**
   ```python
   # routers/new_feature.py - HTTP endpoints
   @router.post("/", response_model=NewFeature)
   def create_new_feature(payload: NewFeatureCreate, db: Session = Depends(get_db)):
       return create_new_feature_db(db, payload)
   ```

5. **Write Tests**
   ```python
   # tests/endpoints/test_new_feature.py
   def test_create_new_feature():
       # Test implementation
       pass
   ```

#### **2. Frontend Integration**

1. **Create API Client**
   ```python
   # api/new_feature.py - Frontend API client
   def create_new_feature(data: Dict) -> Dict:
       return client.post("/api/new-features/", json=data)
   ```

2. **Build UI Components**
   ```python
   # pages/new_feature.py - UI implementation
   def render_new_feature_page():
       # Page implementation
       pass
   ```

3. **Add Navigation**
   ```python
   # components/navigation.py - Add menu links
   # main.py - Add route handlers
   ```

### **Common Feature Patterns**

#### **CRUD Operations**
- **Create**: POST endpoint + form UI
- **Read**: GET endpoint + table/list UI  
- **Update**: PUT endpoint + edit form UI
- **Delete**: DELETE endpoint + confirmation dialog

#### **Filtering & Pagination**
- **Backend**: Query parameters with validation
- **Frontend**: Filter controls bound to state + pagination controls

#### **Data Visualization**
- **Backend**: Summary/aggregation endpoints
- **Frontend**: Chart components with Highcharts

---

## 🐛 **Debugging & Troubleshooting**

### **Common Issues & Solutions**

#### **Backend Issues**

**Database Connection Errors**
```python
# Check database file exists and has correct permissions
# Recreate database: delete data.db and restart backend
```

**API Validation Errors** 
```python
# Check Pydantic schema matches request data
# Verify field types and constraints
# Use FastAPI docs (/docs) to test endpoints
```

**Import/Circular Dependency Issues**
```python
# Use delayed imports in functions
# Review import order in modules
# Consider refactoring shared utilities
```

#### **Frontend Issues**

**WebSocket Connection Warnings**
```python
# Normal in development with auto-reload
# Check backend server is running
# Verify ports 8000 (API) and 8081 (UI) are available
```

**Chart Rendering Issues**
```python
# Ensure nicegui[highcharts] is installed
# Check data format matches Highcharts expectations
# Verify numeric values are properly converted
```

**State Synchronization Issues**
```python
# Use .bind_value() for automatic UI updates
# Clear containers before repopulating
# Check filter state initialization
```

### **Debugging Tools**

#### **Backend Debugging**
```python
# FastAPI automatic docs
http://localhost:8000/docs

# Database inspection  
sqlite3 backend/data.db
.tables
.schema transactions

# Logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### **Frontend Debugging**
```python
# Print statements in UI callbacks
def load_data():
    print(f"Loading with filters: {current_filters}")
    # ... rest of function

# Browser developer tools for JavaScript errors
# Check network tab for API call failures
```

---

## 📝 **Git Workflow & Commit Guidelines**

### **Branch Management**

#### **Branch Naming**
- `feature/description` - New features
- `fix/issue-description` - Bug fixes  
- `refactor/component-name` - Code improvements
- `docs/update-type` - Documentation updates

#### **Commit Message Format**
```
type: brief description of changes

- Detailed explanation if needed
- List specific changes made
- Reference issues if applicable

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Commit Types:**
- `feat:` - New features
- `fix:` - Bug fixes
- `refactor:` - Code restructuring
- `docs:` - Documentation updates
- `test:` - Testing additions/fixes
- `style:` - Formatting, no logic changes

#### **Example Commits**
```
feat: add transaction bulk categorization with entity rules

- Implement entity-only rule creation for default categorization
- Add bulk rule application to existing transactions  
- Fix rule priority handling (exact rules override entity rules)
- Update UI with separate buttons for exact vs entity rules

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### **Pull Request Process**

1. **Before Creating PR**
   - Run full test suite: `pytest tests/ -v`
   - Verify frontend functionality manually
   - Check code formatting and remove debugging statements
   - Update documentation if needed

2. **PR Description Template**
   ```markdown
   ## Summary
   Brief description of changes and motivation
   
   ## Changes Made
   - List specific changes
   - Include both backend and frontend modifications
   
   ## Testing
   - [ ] Backend tests pass
   - [ ] Manual frontend testing completed
   - [ ] New functionality verified
   
   ## Screenshots (if UI changes)
   [Add screenshots of new/modified UI]
   ```

---

## 🤖 **Guidelines for Claude & AI Assistants**

### **How Claude Should Approach DKBlytics Development**

#### **1. Understanding Context**
- **Read existing code first** - Use Read/Grep tools to understand patterns
- **Follow established conventions** - Match existing code style and architecture
- **Check related files** - Understand how components interact
- **Use TodoWrite** - Track progress and communicate what you're working on

#### **2. Development Process**
- **Backend first** - Always implement API endpoints before frontend
- **Test as you go** - Run tests after backend changes
- **Maintain consistency** - Follow patterns established in existing code
- **Document decisions** - Explain complex logic in comments

#### **3. Problem-Solving Approach**
- **Start with error messages** - Read full error output carefully
- **Check dependencies** - Verify imports and library versions
- **Test incrementally** - Make small changes and verify they work
- **Use existing utilities** - Leverage established helper functions

#### **4. Code Quality Standards**
- **No commented-out code** - Remove debug prints and old code
- **Proper error handling** - Use try/catch with meaningful messages
- **Type hints** - Always include type annotations
- **Clear variable names** - Self-documenting code preferred

#### **5. Communication Guidelines**
- **Be explicit about changes** - Explain what you're modifying and why
- **Ask for clarification** - When requirements are unclear
- **Provide alternatives** - Offer different implementation approaches
- **Document limitations** - Explain any constraints or trade-offs

### **Common Tasks for Claude**

#### **Adding New API Endpoints**
1. Define Pydantic schemas in `schemas.py`
2. Implement service function in `services/`
3. Add router endpoint in `routers/`
4. Write tests in `tests/endpoints/`
5. Create frontend API client in `frontend-nicegui/app/api/`

#### **Enhancing UI Features**
1. Review existing page structure and patterns
2. Implement new components following established patterns
3. Use existing utility functions from `utils.py`
4. Follow CSS class conventions from `constants.py`
5. Test with various data scenarios

#### **Debugging Issues**
1. Read error messages completely
2. Check both backend logs and frontend console
3. Verify API responses match expected schemas
4. Test with different data inputs
5. Use debugging tools mentioned in this guide

### **What Claude Should NOT Do**
- ❌ Change database models without careful consideration
- ❌ Modify core architecture without discussion  
- ❌ Add dependencies without justification
- ❌ Skip testing after making changes
- ❌ Leave debugging code in commits
- ❌ Make breaking changes without planning migration

---

## 📚 **Resources & References**

### **Documentation**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [NiceGUI Documentation](https://nicegui.io/)
- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)

### **Project-Specific Resources**
- **API Documentation**: `http://localhost:8000/docs`
- **Database Schema**: Check `backend/src/models.py`
- **Frontend Components**: Browse `frontend-nicegui/app/components/`
- **Example Usage**: See `USAGE.md` for feature examples

### **Development Tools**
- **Database Browser**: SQLite browser for examining data
- **API Testing**: Postman or curl for API endpoint testing
- **Code Formatting**: Black, isort for Python formatting
- **Type Checking**: mypy for static type analysis

---

## ❓ **Getting Help**

### **Common Questions**

**Q: How do I add a new page to the frontend?**
A: 
1. Create new file in `frontend-nicegui/app/pages/`
2. Implement `render_page_name()` function
3. Add route in `main.py`
4. Add navigation link in `components/navigation.py`

**Q: How do I modify the database schema?**
A: 
1. Update models in `backend/src/models.py`
2. Delete existing `backend/data.db` file
3. Restart backend server to recreate database
4. Update corresponding Pydantic schemas

**Q: Why are my chart animations not working?**
A: Ensure you've installed `nicegui[highcharts]` and that data is in the correct format for Highcharts.

### **Need More Help?**

1. **Check existing code** - Look for similar implementations
2. **Read error messages carefully** - Often contain the solution
3. **Test in isolation** - Create minimal reproduction cases
4. **Review this guide** - Many common patterns are documented here

---

**Happy Contributing! 🚀**

Remember: Good code is not just working code, but code that the next developer (including your future self) can easily understand and maintain.