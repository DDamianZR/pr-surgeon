
Run:

cd backend; python -m pytest tests/test_github_client.py -v

============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\damia\Documents\Proyectos\BOB-IA-HACKATHON-2026\backend
configfile: pyproject.toml
plugins: anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

tests/test_github_client.py::TestParseURLs::test_parse_valid_https_url PASSED [  7%]
tests/test_github_client.py::TestParseURLs::test_parse_http_url PASSED   [ 15%]
tests/test_github_client.py::TestParseURLs::test_parse_url_without_protocol PASSED [ 23%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_www PASSED [ 30%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_https_and_www PASSED [ 38%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_trailing_slash PASSED [ 46%]
tests/test_github_client.py::TestParseURLs::test_parse_invalid_url_raises_error PASSED [ 53%]
tests/test_github_client.py::TestParseURLs::test_parse_issues_url_raises_error PASSED [ 61%]
tests/test_github_client.py::TestParseURLs::test_parse_malformed_url_raises_error PASSED [ 69%]
tests/test_github_client.py::TestParseURLs::test_parse_url_missing_pr_number_raises_error PASSED [ 76%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_special_characters_in_names PASSED [ 84%]
tests/test_github_client.py::TestClientInitialization::test_init_with_token_parameter PASSED [ 92%]
tests/test_github_client.py::TestClientInitialization::test_init_without_token_raises_error FAILED [100%]

================================== FAILURES ===================================
________ TestClientInitialization.test_init_without_token_raises_error ________

self = <backend.tests.test_github_client.TestClientInitialization object at 0x000001CE6ECDAAD0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001CE6ECC6780>

    def test_init_without_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that initialization without token raises ValueError."""
        # Remove GITHUB_TOKEN from environment
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    
>       with pytest.raises(ValueError) as exc_info:
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE <class 'ValueError'>

tests\test_github_client.py:149: Failed
---------------------------- Captured stderr call -----------------------------
2026-05-16 21:03:16.506 | INFO     | services.github_client:__init__:49 - GitHubPRClient initialized
=========================== short test summary info ===========================
FAILED tests/test_github_client.py::TestClientInitialization::test_init_without_token_raises_error
======================== 1 failed, 12 passed in 2.63s =========================



Auto-approved commands


Checkpoint
Current




I want to edit this file:


Run:

cd backend; python -m pytest tests/test_github_client.py::TestClientInitialization::test_init_without_token_raises_error -v

============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\damia\Documents\Proyectos\BOB-IA-HACKATHON-2026\backend
configfile: pyproject.toml
plugins: anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 1 item

tests/test_github_client.py::TestClientInitialization::test_init_without_token_raises_error PASSED [100%]

============================== 1 passed in 0.40s ==============================


Auto-approved commands


Run:

cd backend; python -m pytest tests/test_github_client.py -v

============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\damia\Documents\Proyectos\BOB-IA-HACKATHON-2026\backend
configfile: pyproject.toml
plugins: anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

tests/test_github_client.py::TestParseURLs::test_parse_valid_https_url PASSED [  7%]
tests/test_github_client.py::TestParseURLs::test_parse_http_url PASSED   [ 15%]
tests/test_github_client.py::TestParseURLs::test_parse_url_without_protocol PASSED [ 23%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_www PASSED [ 30%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_https_and_www PASSED [ 38%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_trailing_slash PASSED [ 46%]
tests/test_github_client.py::TestParseURLs::test_parse_invalid_url_raises_error PASSED [ 53%]
tests/test_github_client.py::TestParseURLs::test_parse_issues_url_raises_error PASSED [ 61%]
tests/test_github_client.py::TestParseURLs::test_parse_malformed_url_raises_error PASSED [ 69%]
tests/test_github_client.py::TestParseURLs::test_parse_url_missing_pr_number_raises_error PASSED [ 76%]
tests/test_github_client.py::TestParseURLs::test_parse_url_with_special_characters_in_names PASSED [ 84%]
tests/test_github_client.py::TestClientInitialization::test_init_with_token_parameter PASSED [ 92%]
tests/test_github_client.py::TestClientInitialization::test_init_without_token_raises_error PASSED [100%]

============================= 13 passed in 0.42s ==============================



Auto-approved commands


Analyze the task requirements and existing project structure
Create `backend/models/pr.py` with Pydantic v2 models (FileChange, PullRequestData) and language detection helper
Create `backend/services/github_client.py` with GitHubPRClient class for fetching PR data
Create `backend/tests/test_github_client.py` with unit tests for URL parsing
Verify all files follow project conventions (type hints, loguru, Pydantic v2)
Provide Python REPL snippet for testing with a real PR


🎉
Task Completed
✅ GitHub Client Implementation Complete

Successfully created all three files for the PR Surgeon GitHub client:

Files Created
1. backend/models/pr.py (119 lines)
FileChange Pydantic model with filename, status, additions, deletions, patch, and language
PullRequestData Pydantic model with complete PR metadata and file list
detect_language() helper function mapping 12 file extensions to language names
Full Python 3.11 type hints with str | None syntax
Pydantic v2 with model_config for JSON schema examples
2. backend/services/github_client.py (233 lines)
GitHubPRClient class with PyGithub integration
Reads GITHUB_TOKEN from environment via python-dotenv
parse_pr_url() method supporting multiple URL formats (https, http, with/without www, with/without protocol)
fetch_pr() method fetching complete PR data with file truncation at configurable max_files
Structured logging with loguru
Proper error handling for GitHub API exceptions (rate limits, auth errors)
Automatic language detection for each file
3. backend/tests/test_github_client.py (169 lines)
13 unit tests, all passing ✅
Tests for valid URL formats (https, http, www, no protocol, trailing slash)
Tests for invalid URLs (malformed, issues path, missing PR number)
Tests for special characters in owner/repo names
Tests for client initialization with/without token
No network calls (pure unit tests)
Test Results
13 passed in 0.42s

Python REPL Testing Snippet
To test with a real PR, paste this into a Python REPL from the backend/ directory:

# Test the GitHub client with a small real PR
from services.github_client import GitHubPRClient
from models.pr import detect_language

# Initialize client (uses GITHUB_TOKEN from .env)
client = GitHubPRClient()

# Fetch a small PR from a popular repo (example: a small FastAPI PR)
pr_url = "https://github.com/fastapi/fastapi/pull/1"
pr_data = client.fetch_pr(pr_url, max_files=50)

# Print summary statistics
print(f"\n{'='*60}")
print(f"PR #{pr_data.pr_number}: {pr_data.title}")
print(f"{'='*60}")
print(f"Author: {pr_data.author}")
print(f"Base: {pr_data.base_branch} ← Head: {pr_data.head_branch}")
print(f"Repository: {pr_data.repo_full_name}")
print(f"\nFiles changed: {len(pr_data.files)}")
print(f"Total additions: {pr_data.total_additions}")
print(f"Total deletions: {pr_data.total_deletions}")

# Language breakdown
from collections import Counter
languages = Counter(f.language for f in pr_data.files if f.language)
print(f"\nLanguages detected:")
for lang, count in languages.most_common():
    print(f"  {lang}: {count} files")

# Show first 5 files
print(f"\nFirst 5 files:")
for f in pr_data.files[:5]:
    print(f"  [{f.status:8}] {f.filename} (+{f.additions}/-{f.deletions}) [{f.language or 'unknown'}]")


Alternative small PR for testing:

# Or test with a smaller PR from PR Surgeon's own repo (once created)
pr_url = "https://github.com/tiangolo/fastapi/pull/10000"  # Adjust to any small PR

Verification Checklist
✅ Python 3.11 strict type hints everywhere

✅ Pydantic v2 models with proper field types

✅ Loguru structured logging

✅ snake_case naming convention

✅ No global state (dependency injection ready)

✅ Comprehensive error handling

✅ All tests passing

✅ Follows AGENTS.md conventions


Start New Task
What's on your mind?

💻 Code