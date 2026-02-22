# DEV-WORKFLOW.md — Task Lifecycle & Git Workflow

> Based on 胡渊鸣's Claude Code task management system.
> Adapted for Meridian: single-developer + AI-agent workflow on VPS.

## Architecture

```
/home/raven/meridian/                      ← main worktree (main branch)
/home/raven/meridian-worktrees/            ← task worktrees
  └── task-xxx/                            ← isolated per-task
      ├── (full repo checkout)
      └── .port                            ← assigned dev port
```

## Task Lifecycle

### 1. Claim Task
```bash
# Read dev-tasks.json, pick highest priority pending task
# Update status: "pending" → "in_progress"
# Set assigned_to, started_at
```

### 2. Create Worktree
```bash
cd /home/raven/meridian
git fetch origin

# Create task branch + worktree
git worktree add -b task/<task-id> ../meridian-worktrees/<task-id>
cd ../meridian-worktrees/<task-id>

# Install frontend deps if needed
cd frontend/sveltekit && npm install && cd ../..
```

### 3. Implement
- Work in isolated worktree
- `npm run build` in frontend/sveltekit/ to verify
- Test API: `docker compose build api && docker compose up -d api`
- Curl test endpoints

### 4. Commit
```bash
git add -A
git commit -m "feat/fix: <description>"
# Conventional commits: feat, fix, refactor, docs, perf, test
```

### 5. Merge to Main
```bash
git fetch origin main
git rebase origin/main
# Resolve conflicts if any
git checkout main
git merge task/<task-id>
git push origin main
```

### 6. Mark Complete
```bash
# Update dev-tasks.json BEFORE cleanup
# Set completed_at, commit hash
```

### 7. Cleanup
```bash
cd /home/raven/meridian
git worktree remove ../meridian-worktrees/<task-id>
git branch -d task/<task-id>
```

### 8. Deploy
```bash
cd /home/raven/meridian
docker compose build api frontend
docker compose up -d
# Verify: curl http://localhost:8502/api/health
```

### 9. Lessons Learned
```bash
# Update PROGRESS.md with problem/solution/prevention/commit ID
```

---

## When to Use Worktrees vs Direct Main

**Worktree**: New features, refactors, anything touching multiple files
**Direct Main**: Hotfixes (< 5 min, < 3 files), docs, config changes

## Port Allocation

| Service | Main | Task 1 | Task 2 |
|---------|------|--------|--------|
| Frontend | 3001 | 3003 | 3005 |
| API | 8502 | 8503 | 8504 |

## Deploy Checklist

- [ ] `npm run build` succeeds
- [ ] `docker compose build api frontend`
- [ ] `docker compose up -d`
- [ ] API health: `curl http://localhost:8502/api/health`
- [ ] Data health: `curl http://localhost:8502/api/data-health`
- [ ] Spot-check 3+ pages
- [ ] No SSR errors in `docker logs meridian-frontend`
- [ ] Update PROGRESS.md, CHANGELOG.md
