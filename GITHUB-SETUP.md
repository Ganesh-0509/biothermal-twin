# GitHub Setup & Push Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `biothermal-twin`
3. Description: `Physics-Informed Heat Stress Early Warning System - Future Health Challenge 2026`
4. **Public** repository
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

## Step 2: Add Remote & Push

```bash
# In your project directory
cd "C:\Users\Ganesh\OneDrive\Desktop\project-report\future-health-challenge-2026"

# Add GitHub remote
git remote add origin https://github.com/Ganesh-0509/biothermal-twin.git

# Verify remote
git remote -v

# Push all commits to GitHub
git push -u origin main
```

## Step 3: Verify on GitHub

Visit: https://github.com/Ganesh-0509/biothermal-twin

You should see:
- ✅ 8 commits
- ✅ README with metrics
- ✅ All source code (core/, models/, backend/, frontend/, voice/)
- ✅ Documentation (PRD, Architecture, Timeline, Validation)

## Step 4: GitHub Actions (Optional)

Create `.github/workflows/test.yml` for automated testing:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## Troubleshooting

### Large Files Error
If git push fails due to large files (training data):

```bash
# Data files are already gitignored, but if pushed accidentally:
git rm --cached -r core/data/
git rm --cached -r models/checkpoints/
git commit -m "Remove large files"
git push origin main
```

### Authentication
If prompted for credentials, use GitHub Personal Access Token:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Scopes: repo (all)
4. Use token as password when pushing

---

**After pushing to GitHub, update submission form with:**
- Repository URL: https://github.com/Ganesh-0509/biothermal-twin
- Demo Video: (record after deployment)
- Prototype Link: (after Vercel/Render deployment)
