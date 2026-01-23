# CI Fix for PR #28 - Instructions

## Summary
PR #28 has CI failures due to:
1. **Linting errors**: W293 (blank lines with whitespace) in `core/bot_management/bot_api_server.py`
2. **Missing dependency**: `aiohttp_cors` module not in `requirements.txt`

## Fixes Applied
The minimal fixes have been created and verified locally in commit `f8cda50` on branch `copilot/fix-dashboard-buttons-functionality`.

### Changes:
1. **bot_api_server.py**: Removed trailing whitespace from 12 blank lines (lines 233, 239, 339, 346, 353, 365, 381, 384, 399, 402, 865, 1485)
2. **requirements.txt**: Added `aiohttp>=3.8.0` and `aiohttp-cors>=0.7.0`

**Stats**: 14 insertions, 12 deletions across 2 files

## Verification ✅
- ✅ Linting: `ruff check --select E,F,W --ignore E501 core/bot_management/bot_api_server.py` passes
- ✅ Import: `from aiohttp_cors import setup as setup_cors` works
- ✅ Tests: `pytest tests/bot_management/test_dashboard_buttons.py --collect-only` successfully collects 26 tests

## How to Apply

### Option 1: Cherry-pick the commit
If you have commit `f8cda50` available:
```bash
git checkout copilot/fix-dashboard-buttons-functionality
git cherry-pick f8cda50
git push origin copilot/fix-dashboard-buttons-functionality
```

### Option 2: Apply the patch manually
The fixes are minimal - just remove whitespace from blank lines and add two lines to requirements.txt:

**requirements.txt** - Add after line 4:
```
aiohttp>=3.8.0
aiohttp-cors>=0.7.0
```

**bot_api_server.py** - Remove trailing spaces from these blank lines:
- 233, 239, 339, 346, 353, 365, 381, 384, 399, 402, 865, 1485

Or use `ruff --fix`:
```bash
ruff check --select W293 --fix core/bot_management/bot_api_server.py
```

### Option 3: Merge from copilot/fix-whitespace-lint-errors
Branch `copilot/fix-whitespace-lint-errors` (commit 806c211) contains the full bot_api_server.py from PR #28 with the fixes applied. However, this includes all changes from PR #28, not just the CI fixes.

## Next Steps
1. Apply the fixes to the `copilot/fix-dashboard-buttons-functionality` branch
2. Push to GitHub
3. CI should pass the linting and test import steps
4. Verify the CI run is successful

## Notes
- Current PR HEAD on GitHub: `ad47e2d` (needs f8cda50 on top of it)
- The fixes are surgical and minimal - only addressing the specific CI failures
- No functional changes, only whitespace cleanup and dependency addition
