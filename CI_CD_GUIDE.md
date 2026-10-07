# CI/CD Pipeline Guide

## What is CI/CD?

**CI** = Continuous Integration: Automatically test code every time you push
**CD** = Continuous Deployment: Automatically deploy if tests pass

Our pipeline automatically:
✅ Runs on every push
✅ Checks code quality (linting)
✅ Validates modules can be imported
✅ Tests configuration loading
✅ Scans for security issues

---

## How It Works

### 1. You Create a Feature Branch
```bash
git checkout -b feature/add-new-source
```

### 2. You Make Changes & Commit
```bash
git add backend/services/news_fetcher.py
git commit -m "Add new news source fetcher"
git push origin feature/add-new-source
```

### 3. GitHub Actions Automatically Tests Your Code
- ✅ Installs dependencies
- ✅ Runs linting checks (flake8, black)
- ✅ Tests imports
- ✅ Scans for security issues

### 4. You See Results in GitHub

**If tests pass:** ✅ Green checkmark - safe to merge!
**If tests fail:** ❌ Red X - fix issues before merging

### 5. Create a Pull Request
- Click "New Pull Request" on GitHub
- Describe your changes
- Reviewers see CI/CD results
- Merge to main when ready

---

## Workflow Details

### What Gets Tested

| Test | Purpose | Fails If... |
|------|---------|-----------|
| Syntax (flake8) | Python style violations | Missing semicolon, wrong indentation |
| Format (black) | Code formatting consistency | Inconsistent spacing (warning only) |
| Imports | Modules can be loaded | Import errors in code |
| Config | Settings load properly | Invalid environment variables |
| FastAPI | Backend app initializes | Route registration errors |
| Security (bandit) | Security vulnerabilities | Hardcoded passwords, SQL injection risk |

### Runs On

**Branch pushes:**
- `main`
- `feature/*` (any feature branch)
- `bugfix/*` (any bugfix branch)

**Pull Requests:**
- All PRs to `main` are tested before merge

---

## Example Workflow

### Scenario: Add a new interest category

```bash
# Step 1: Create feature branch
git checkout -b feature/add-health-category

# Step 2: Edit interests in news_fetcher.py
# Add "health": "/health" to interest_section_map

# Step 3: Commit
git add backend/services/news_fetcher.py
git commit -m "Add health category to interests

- Add health → /health section mapping
- Update interest filtering documentation"

# Step 4: Push
git push origin feature/add-health-category

# Step 5: GitHub Actions automatically tests
# - Runs linting
# - Tests imports
# - Verifies no syntax errors
# ✅ Shows green checkmark if all pass

# Step 6: Create Pull Request on GitHub
# Describe: "Added health category to interest filtering"

# Step 7: Merge when CI passes
```

---

## CI/CD Configuration

**File:** `.github/workflows/test.yml`

**Triggers:**
- Any push to `main`, `feature/*`, `bugfix/*`
- Any pull request to `main`

**Python Versions Tested:**
- 3.11
- 3.12

**Tools Used:**
- `flake8`: Style checker
- `black`: Code formatter
- `bandit`: Security scanner
- `pylint`: Code analysis

---

## How to Check Results

### On GitHub
1. Go to your PR
2. Scroll down to "Checks" section
3. Click on "Tests & Quality Checks"
4. See detailed pass/fail results

### In Command Line (Local)
```bash
# Before pushing, run tests locally
python -m flake8 backend/ frontend/
python -m black backend/ frontend/ --check
python -c "from backend.main import app; print('✅ App loads')"
```

---

## Common CI Failures & Fixes

### ❌ "Linting failed: line too long"
```python
# ❌ Bad
result = some_very_long_function_name(arg1, arg2, arg3, arg4, arg5)

# ✅ Good
result = some_very_long_function_name(
    arg1, arg2, arg3, arg4, arg5
)
```

### ❌ "Import error: No module named 'xyz'"
- Check you installed dependencies: `pip install -r requirements.txt`
- Verify file exists at the correct path
- Check for typos in import statement

### ❌ "Code not formatted (black check failed)"
```bash
# Auto-fix formatting
black backend/ frontend/
git add .
git commit -m "Auto-format with black"
git push
```

### ❌ "Syntax error in config"
- Verify `.env` file exists with correct format
- Check YAML syntax in workflow files
- Ensure all quotes are closed

---

## Next Steps

1. **Try it:** Push a small change and watch CI/CD run
2. **Fix failures:** If something fails, review logs and fix it
3. **Use branches:** Always work on feature branches, not main
4. **Request reviews:** Have team members review before merging

---

## Questions?

Check the logs on GitHub Actions for detailed error messages!
