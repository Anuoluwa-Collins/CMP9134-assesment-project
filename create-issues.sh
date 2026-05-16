#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# CMP9134 — Create GitHub Issues from Trello Board Plan
# Run this from your repo root:  bash create-issues.sh
# Requires: gh cli (https://cli.github.com) — run `gh auth login` first
# ─────────────────────────────────────────────────────────────────

set -e

echo "🏷  Creating labels..."
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

echo ""
echo "📋 Creating Sprint 1 issues..."

gh issue create \
  --title "Project Setup & Repository" \
  --label "DevOps,Must Have,Sprint 1" \
  --body "## User Story
As a developer, I want a well-structured project repo with a README, so the codebase is professional from day one.

**Effort:** S

## Checklist
- [ ] Create public GitHub repo from template
- [ ] Initialise project structure
- [ ] Add .gitignore, README.md
- [ ] Set up folder structure (src/, tests/, docs/)
- [ ] First commit with project skeleton
- [ ] Add branch protection on main"

gh issue create \
  --title "Docker Development Environment" \
  --label "DevOps,Must Have,Sprint 1" \
  --body "## User Story
As a developer, I want a containerised dev environment with Docker Compose, so the app and virtual robot run together easily.

**Effort:** M

## Checklist
- [ ] Create Dockerfile for dashboard
- [ ] Create docker-compose.yml (dashboard + robot)
- [ ] Configure VS Code DevContainer
- [ ] Test \`docker-compose up\` starts both services
- [ ] Document setup instructions in README
- [ ] Verify robot API accessible on port 5000"

gh issue create \
  --title "Connect to Robot REST API" \
  --label "Backend/API,Must Have,Sprint 1" \
  --body "## User Story
As an operator, I want the dashboard to connect to the robot's API, so I can retrieve robot data.

**Effort:** M

## Checklist
- [ ] Create API service/client module (robot_client.py)
- [ ] Implement GET /api/status call
- [ ] Implement GET /api/map call
- [ ] Implement GET /api/sensors call
- [ ] Add error handling for failed requests
- [ ] Test all endpoints return valid data"

gh issue create \
  --title "Display Robot on Grid Map" \
  --label "Frontend,Must Have,Sprint 1" \
  --body "## User Story
As an operator, I want to see the robot's live position on a 21×21 grid, so I can monitor its location.

**Effort:** L

## Checklist
- [ ] Create 21×21 grid component
- [ ] Fetch map data from /api/map endpoint
- [ ] Render robot position on grid
- [ ] Render obstacles on grid
- [ ] Add colour key/legend
- [ ] Auto-refresh grid on interval or event"

gh issue create \
  --title "Send Movement Commands" \
  --label "Frontend,Backend/API,Must Have,Sprint 1" \
  --body "## User Story
As an operator, I want to send movement commands (N/S/E/W) to the robot, so I can control it remotely.

**Effort:** M

## Checklist
- [ ] Create directional control buttons (N/S/E/W)
- [ ] Implement POST /api/move with direction payload
- [ ] Update grid after each move
- [ ] Disable buttons while request pending
- [ ] Show feedback on successful/failed move
- [ ] Handle edge-of-grid boundary validation"

echo ""
echo "📋 Creating Sprint 2 issues..."

gh issue create \
  --title "Battery & Sensor Dashboard" \
  --label "Frontend,Backend/API,Must Have,Sprint 2" \
  --body "## User Story
As an operator, I want to see battery level and sensor data, so I can monitor robot health.

**Effort:** M

## Checklist
- [ ] Create status panel component
- [ ] Display battery level with visual indicator (bar/gauge)
- [ ] Display sensor readings (proximity, temperature)
- [ ] Add warning colours when battery low (<20% danger, <40% warn)
- [ ] Poll /api/status endpoint on interval
- [ ] Show last-updated timestamp"

gh issue create \
  --title "WebSocket Telemetry Feed" \
  --label "Backend/API,Frontend,Should Have,Sprint 2" \
  --body "## User Story
As an operator, I want a live telemetry feed via WebSocket, so I get real-time updates without polling.

**Effort:** L

## Checklist
- [ ] Establish WebSocket connection to /ws/telemetry
- [ ] Parse incoming telemetry JSON messages
- [ ] Update grid position in real-time from WebSocket data
- [ ] Update sensor panel from telemetry
- [ ] Display connection status indicator (connected/reconnecting)
- [ ] Handle WebSocket disconnect with auto-reconnect and backoff"

gh issue create \
  --title "Handle Connection Dropouts (Chaos Monkey)" \
  --label "Backend/API,Must Have,Sprint 2" \
  --body "## User Story
As an operator, I want the system to handle connection dropouts (503s) gracefully, so I don't lose control.

**Effort:** M

## Checklist
- [ ] Detect 503 errors from robot API
- [ ] Implement retry logic with exponential backoff
- [ ] Show \"connection lost\" alert to user on frontend
- [ ] Queue/disable commands during outage
- [ ] Resume automatically when connection restored
- [ ] Log dropout events for debugging and report evidence"

gh issue create \
  --title "Reset Robot" \
  --label "Frontend,Backend/API,Should Have,Sprint 2" \
  --body "## User Story
As an operator, I want to reset the robot to its starting position, so I can restart a mission.

**Effort:** S

## Checklist
- [ ] Add reset button to UI
- [ ] Implement POST /api/reset endpoint
- [ ] Show confirmation dialog before reset
- [ ] Clear and refresh grid after reset
- [ ] Reset telemetry/sensor displays"

gh issue create \
  --title "Unit Tests" \
  --label "Testing,Must Have,Sprint 2" \
  --body "## User Story
As a developer, I want unit tests for core functions, so I can verify the code works correctly.

**Effort:** L

## Checklist
- [ ] Set up pytest + pytest-asyncio framework
- [ ] Write tests for robot_client.py (get_status, move, reset, map, sensors)
- [ ] Write tests for retry logic (503 retry, exhaustion)
- [ ] Write tests for API endpoint validation (invalid coords → 422)
- [ ] Write tests for error handling (RobotConnectionError)
- [ ] Write tests for legacy_stats.py helper functions
- [ ] Run coverage report with pytest-cov"

gh issue create \
  --title "Integration Tests" \
  --label "Testing,Should Have,Sprint 2" \
  --body "## User Story
As a developer, I want integration tests that test the full API flow, so I know the system works end-to-end.

**Effort:** M

## Checklist
- [ ] Write test: health endpoint returns 200
- [ ] Write test: status endpoint returns robot data / error on failure
- [ ] Write test: move endpoint validates coords and returns result
- [ ] Write test: reset endpoint returns confirmation
- [ ] Write test: map and sensors endpoints return data
- [ ] Document how to run tests in README (\`pytest tests/ -v\`)"

echo ""
echo "📋 Creating Sprint 3 issues..."

gh issue create \
  --title "Obstacle Alerts & Notifications" \
  --label "Frontend,Could Have,Sprint 3" \
  --body "## User Story
As an operator, I want to receive alerts when the robot encounters obstacles, so I can reroute it.

**Effort:** M

## Checklist
- [ ] Detect obstacle from sensor/map data
- [ ] Display alert/notification in UI
- [ ] Highlight obstacle cells on grid (red)
- [ ] Suggest alternative direction
- [ ] Log obstacle encounters in activity log"

gh issue create \
  --title "CI/CD Pipeline" \
  --label "DevOps,Must Have,Sprint 3" \
  --body "## User Story
As a developer, I want a CI/CD pipeline, so code is tested automatically on every push.

**Effort:** M

## Checklist
- [ ] Create GitHub Actions workflow file (.github/workflows/ci.yml)
- [ ] Run linting (flake8) on push/PR
- [ ] Run unit tests with coverage on push/PR
- [ ] Build Docker image in pipeline (compose integration test)
- [ ] Add CI status badge to README
- [ ] Verify pipeline triggers correctly on main branch"

gh issue create \
  --title "UI/UX Polish & Accessibility" \
  --label "Frontend,Should Have,Sprint 3" \
  --body "## User Story
As an operator, I want a clean, accessible interface, so the dashboard is easy and safe to use.

**Effort:** M

## Checklist
- [ ] Apply consistent colour scheme / dark theme
- [ ] Add keyboard shortcuts for movement (WASD / arrow keys)
- [ ] Ensure responsive layout for different screen sizes
- [ ] Add ARIA labels for accessibility
- [ ] Apply Nielsen's heuristics (error prevention, visibility of system status)
- [ ] Test with screen reader"

gh issue create \
  --title "Error Logging & Sensor Noise Handling" \
  --label "Backend/API,Should Have,Sprint 3" \
  --body "## User Story
As a developer, I want the system to handle sensor noise and log errors, so data is reliable.

**Effort:** M

## Checklist
- [ ] Add data validation/smoothing for noisy sensor readings
- [ ] Implement structured logging (replace any print statements)
- [ ] Display data confidence indicator on frontend
- [ ] Log API errors with timestamps
- [ ] Add debug mode toggle via LOG_LEVEL env var"

gh issue create \
  --title "Report & Documentation" \
  --label "Documentation,Must Have,Sprint 3" \
  --body "## User Story
As a student, I want all report sections and documentation complete, so I can submit the coursework.

**Effort:** L

## Checklist
- [ ] Section 1: Critical Reflection (20%) — engineering decisions, trade-offs
- [ ] Section 2: Project Planning (15%) — Trello/GitHub screenshots, user stories
- [ ] Section 3: Project Management (15%) — sprint evidence, board progression
- [ ] Section 4: Testing & Containerisation (20%) — test results, Docker setup
- [ ] Section 5: Artefact & Ethics (20%+10%) — code quality, LEPSI/security
- [ ] Appendix: UML diagrams, architecture diagrams
- [ ] Update README with full project documentation"

gh issue create \
  --title "Video Demo" \
  --label "Documentation,Must Have,Sprint 3" \
  --body "## User Story
As a student, I want a 5-minute video demonstrating the system, so the markers can see it working.

**Effort:** M

## Checklist
- [ ] Plan demo script/flow
- [ ] Show Docker startup (docker-compose up)
- [ ] Demo grid map and movement controls
- [ ] Demo telemetry and sensor panel
- [ ] Show error handling (503 chaos monkey recovery)
- [ ] Show tests running and passing (pytest output)
- [ ] Upload/link video in submission"

echo ""
echo "✅ All 17 issues created!"
echo ""
echo "📌 Next steps:"
echo "   1. Go to your repo → Issues tab to see all issues"
echo "   2. Create 3 Milestones: Sprint 1, Sprint 2, Sprint 3"
echo "   3. Assign each issue to its milestone"
echo "   4. Use Projects → Board view for a Kanban board (like Trello)"
echo "   5. Screenshot the board at each sprint start/end for your report"
