# PowerShell script to test PR Surgeon with Django PR 18056
# This PR has 43 files with sparse dependencies (only 10 edges)
# Expected: 4-8 sub-PRs after path-prefix clustering

Write-Host "=== PR Surgeon Manual Test ===" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "Checking if server is running on http://localhost:8000..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 2
    Write-Host "✓ Server is running" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "✗ Server is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the server first:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Gray
    Write-Host "  uvicorn main:app --reload" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Test Django PR 18056
Write-Host "Testing Django PR 18056 (43 files, sparse dependencies)..." -ForegroundColor Yellow
Write-Host "PR URL: https://github.com/django/django/pull/18056" -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/analyze" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"pr_url": "https://github.com/django/django/pull/18056"}'
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "✓ Analysis complete in $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
    Write-Host ""
    
    # Display summary
    Write-Host "=== PR Summary ===" -ForegroundColor Cyan
    Write-Host "  Repository: $($response.repo_full_name)" -ForegroundColor White
    Write-Host "  PR Title: $($response.pr_title)" -ForegroundColor White
    Write-Host "  Total Files: $($response.total_files)" -ForegroundColor White
    Write-Host "  Total Additions: +$($response.total_additions)" -ForegroundColor Green
    Write-Host "  Total Deletions: -$($response.total_deletions)" -ForegroundColor Red
    Write-Host "  Analysis Duration: $($response.analysis_duration_ms) ms" -ForegroundColor Gray
    Write-Host ""
    
    # Display sub-PRs
    Write-Host "=== Sub-PRs Created: $($response.sub_prs.Count) ===" -ForegroundColor Cyan
    
    if ($response.sub_prs.Count -ge 4 -and $response.sub_prs.Count -le 8) {
        Write-Host "✓ Sub-PR count is in target range (4-8)" -ForegroundColor Green
    } elseif ($response.sub_prs.Count -lt 4) {
        Write-Host "⚠ Sub-PR count is below target (expected 4-8)" -ForegroundColor Yellow
    } else {
        Write-Host "⚠ Sub-PR count is above target (expected 4-8)" -ForegroundColor Yellow
    }
    Write-Host ""
    
    $totalReviewTime = 0
    foreach ($subpr in $response.sub_prs) {
        Write-Host "[$($subpr.merge_order)] $($subpr.suggested_title)" -ForegroundColor White
        Write-Host "    Files: $($subpr.files.Count) | Layer: $($subpr.layer) | Risk: $($subpr.risk_level)" -ForegroundColor Gray
        Write-Host "    Review Time: $($subpr.estimated_review_minutes) min" -ForegroundColor Gray
        
        # Show first 3 files as examples
        $fileCount = [Math]::Min(3, $subpr.files.Count)
        for ($i = 0; $i -lt $fileCount; $i++) {
            Write-Host "      - $($subpr.files[$i])" -ForegroundColor DarkGray
        }
        if ($subpr.files.Count -gt 3) {
            Write-Host "      ... and $($subpr.files.Count - 3) more files" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        $totalReviewTime += $subpr.estimated_review_minutes
    }
    
    Write-Host "=== Total Estimated Review Time: $totalReviewTime minutes ===" -ForegroundColor Cyan
    Write-Host ""
    
    # Display graph stats
    Write-Host "=== Dependency Graph ===" -ForegroundColor Cyan
    Write-Host "  Nodes: $($response.graph_nodes.Count)" -ForegroundColor White
    Write-Host "  Edges: $($response.graph_edges.Count)" -ForegroundColor White
    Write-Host ""
    
    # Success message
    Write-Host "=== Test Complete ===" -ForegroundColor Green
    Write-Host "The decomposition successfully reduced 43 files into $($response.sub_prs.Count) reviewable sub-PRs." -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "✗ Analysis failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "HTTP Status Code: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 403) {
            Write-Host "This is likely a GitHub API rate limit error." -ForegroundColor Yellow
            Write-Host "Please set GITHUB_TOKEN in backend/.env file." -ForegroundColor Yellow
        }
    }
    
    exit 1
}

# Made with Bob
