## CMP9134 - Create GitHub Issues
## Run from repo root:  .\create-issues.ps1

Write-Host ""
Write-Host "Creating labels..." -ForegroundColor Cyan

gh label create "Must Have"      --color "d73a4a" --force
gh label create "Should Have"    --color "f9a825" --force
gh label create "Could Have"     --color "0075ca" --force
gh label create "Frontend"       --color "1d76db" --force
gh label create "Backend/API"    --color "d97706" --force
gh label create "DevOps"         --color "7c3aed" --force
gh label create "Testing"        --color "0e8a16" --force
gh label create "Documentation"  --color "6b7280" --force
gh label create "Sprint 1"       --color "c5def5" --force
gh label create "Sprint 2"       --color "bfd4f2" --force
gh label create "Sprint 3"       --color "d4c5f9" --force

Write-Host ""
Write-Host "Creating Sprint 1 issues..." -ForegroundColor Yellow

gh issue create --title "Project Setup and Repository" --label "DevOps,Must Have,Sprint 1" --body-file ".github/issue-bodies/01-project-setup.md"
gh issue create --title "Docker Development Environment" --label "DevOps,Must Have,Sprint 1" --body-file ".github/issue-bodies/02-docker-environment.md"
gh issue create --title "Connect to Robot REST API" --label "Backend/API,Must Have,Sprint 1" --body-file ".github/issue-bodies/03-connect-robot-api.md"
gh issue create --title "Display Robot on Grid Map" --label "Frontend,Must Have,Sprint 1" --body-file ".github/issue-bodies/04-grid-map.md"
gh issue create --title "Send Movement Commands" --label "Frontend,Backend/API,Must Have,Sprint 1" --body-file ".github/issue-bodies/05-movement-commands.md"

Write-Host ""
Write-Host "Creating Sprint 2 issues..." -ForegroundColor Yellow

gh issue create --title "Battery and Sensor Dashboard" --label "Frontend,Backend/API,Must Have,Sprint 2" --body-file ".github/issue-bodies/06-battery-sensor-dashboard.md"
gh issue create --title "WebSocket Telemetry Feed" --label "Backend/API,Frontend,Should Have,Sprint 2" --body-file ".github/issue-bodies/07-websocket-telemetry.md"
gh issue create --title "Handle Connection Dropouts (Chaos Monkey)" --label "Backend/API,Must Have,Sprint 2" --body-file ".github/issue-bodies/08-chaos-monkey.md"
gh issue create --title "Reset Robot" --label "Frontend,Backend/API,Should Have,Sprint 2" --body-file ".github/issue-bodies/09-reset-robot.md"
gh issue create --title "Unit Tests" --label "Testing,Must Have,Sprint 2" --body-file ".github/issue-bodies/10-unit-tests.md"
gh issue create --title "Integration Tests" --label "Testing,Should Have,Sprint 2" --body-file ".github/issue-bodies/11-integration-tests.md"

Write-Host ""
Write-Host "Creating Sprint 3 issues..." -ForegroundColor Yellow

gh issue create --title "Obstacle Alerts and Notifications" --label "Frontend,Could Have,Sprint 3" --body-file ".github/issue-bodies/12-obstacle-alerts.md"
gh issue create --title "CI/CD Pipeline" --label "DevOps,Must Have,Sprint 3" --body-file ".github/issue-bodies/13-ci-cd-pipeline.md"
gh issue create --title "UI/UX Polish and Accessibility" --label "Frontend,Should Have,Sprint 3" --body-file ".github/issue-bodies/14-ui-ux-polish.md"
gh issue create --title "Error Logging and Sensor Noise Handling" --label "Backend/API,Should Have,Sprint 3" --body-file ".github/issue-bodies/15-error-logging.md"
gh issue create --title "Report and Documentation" --label "Documentation,Must Have,Sprint 3" --body-file ".github/issue-bodies/16-report-documentation.md"
gh issue create --title "Video Demo" --label "Documentation,Must Have,Sprint 3" --body-file ".github/issue-bodies/17-video-demo.md"

Write-Host ""
Write-Host "All 17 issues created!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Go to your repo > Issues tab to see all issues"
Write-Host "   2. Create 3 Milestones: Sprint 1, Sprint 2, Sprint 3"
Write-Host "   3. Assign each issue to its milestone"
Write-Host "   4. Use Projects > Board view for a Kanban board"
Write-Host "   5. Screenshot the board at each sprint for your report"
