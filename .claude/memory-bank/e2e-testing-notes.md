# E2E Testing Notes (2025-10-30)

> **Source**: Notes from external LLM analysis of HA custom integration + Lovelace card testing
> **Purpose**: Document best practices and solutions for testing integration + frontend together

## Key Insights

### Current Status
✅ **Docker stack working**: Home Assistant running in container with integration loaded
✅ **Code deployment working**: Build pipeline successfully deploys card to container
❌ **Browser caching**: Fix deployed but browser loads stale JavaScript

### Solution: Frontend Cache Busting

**Problem**: Browsers aggressively cache JavaScript modules, even after hard refresh.

**Solution** (from HA docs, line 336-342 of source document):
```yaml
# In configuration.yaml under lovelace: resources:
- url: /local/lovelace-emergency-alerts-card.js?v=0.1
  type: module
```

**How it works**: Query parameter makes browser treat it as new URL, forcing reload.

**When to update**: Change version number (e.g., `?v=0.2`) after each card rebuild.

## Development Workflow

### Option A: VS Code DevContainer (Recommended)
- Uses `.devcontainer/devcontainer.json` configuration
- Mounts custom component code automatically
- Includes tasks to run HA on port 9123
- Supports Python debugger with breakpoints

### Option B: Docker Compose (Current Setup)
```bash
# What we're using now
docker-compose.yml:
  - Mounts: custom_components/, config/www/
  - Runs official homeassistant/home-assistant image
  - Port 8123 exposed
```

### Option C: Thomas Loven's hass-custom-devcontainer
```bash
docker run --rm -it -p 8123:8123 \
  -v $(pwd):/workspaces/test \
  -v $(pwd):/config/www/workspace \
  -e LOVELACE_LOCAL_FILES="my_card.js" \
  thomasloven/hass-custom-devcontainer
```

**Features**:
- Auto-creates admin user (dev/dev)
- Skips onboarding
- Installs HACS automatically
- Auto-registers Lovelace resources via LOVELACE_LOCAL_FILES env var

## Testing Integration + Card Together

### 1. Backend Setup (Integration)
- Place in `custom_components/emergency_alerts/`
- Must have `manifest.json` with version key
- Enable via config flow UI or `configuration.yaml`:
  ```yaml
  emergency_alerts:
    # config here or leave blank
  ```

### 2. Frontend Setup (Lovelace Card)
- Build card: `npm run build` → outputs `.js` file
- Copy to `www/` directory (served at `/local/`)
- Register resource in `configuration.yaml`:
  ```yaml
  lovelace:
    mode: yaml
    resources:
      - url: /local/lovelace-emergency-alerts-card.js?v=VERSION
        type: module
  ```

### 3. Testing Workflow
1. Add card to dashboard: `type: custom:emergency-alerts-card`
2. Interact with card (click buttons, etc.)
3. Observe outcomes:
   - **Developer Tools → Logs**: Integration logging
   - **Developer Tools → States**: Entity state changes
   - **Developer Tools → Services**: Manual service testing
4. Iterate:
   - **Frontend changes**: Rebuild, hard refresh browser (or update version param)
   - **Backend changes**: Restart HA container (usually a few seconds)

## Troubleshooting

### Frontend Caching (OUR CURRENT ISSUE)
**Symptoms**: Browser loads old JavaScript even after rebuild and container restart

**Solutions**:
1. **Cache-busting query param** (RECOMMENDED): `/local/card.js?v=0.1`
2. Hard reload: Ctrl+F5 or Ctrl+Shift+R
3. Different browser or incognito mode
4. Clear browser cache completely

### Docker Volume Mounts
Verify files are accessible:
```bash
docker exec emergency-alerts-ha ls -la /config/custom_components/emergency_alerts/
docker exec emergency-alerts-ha ls -la /config/www/
```

### State Synchronization
- Card calls `hass.callService(...)` to trigger backend actions
- Backend uses `hass.states.set(...)` or entity state updates
- Frontend automatically receives state updates via `set hass()` method
- Use logging in both Python (backend) and `console.log` (frontend)

## Automated Testing (Future)

### hass-taste-test
- Tool for automated E2E testing of Lovelace cards
- Sets up HA instance, installs card, runs interaction suite
- Example: Timer Bar card uses it in CI
- More complex setup, optional for now

### Integration Unit Tests
- Use `pytest` with `pytest-homeassistant-custom-component`
- Test service calls and state changes in isolation
- Already have good coverage (>90%)

## References

### Our Current Setup
- **Integration repo**: `/home/vania/Projects/1.Personal/home_assistant/emergency-alerts-integration/`
- **Card repo**: `/home/vania/Projects/1.Personal/home_assistant/lovelace-emergency-alerts-card/`
- **Config**: `emergency-alerts-integration/config/configuration.yaml`
- **Docker Compose**: `emergency-alerts-integration/docker-compose.yml`

### Key Files
- `config/configuration.yaml:44`: Lovelace resource registration
- `config/www/emergency-alerts-card.js`: Deployed card file
- `custom_components/emergency_alerts/`: Integration code

## Current Work (2025-10-30)

### Bug Fix Status
- ✅ Fixed: `_convertToSwitchId()` in alert-service.ts (strips "emergency_" prefix)
- ✅ Built: Card rebuilt with npm
- ✅ Deployed: File copied to container
- ✅ Verified: Fix present in dist file (grep confirmed)
- ❌ Blocked: Browser caching prevents verification

### Next Steps
1. Add cache-busting parameter to configuration.yaml
2. Restart HA container
3. Verify browser loads new JavaScript
4. Manual test button clicks
5. Document success

### Lessons Learned
- **Docker setup is solid**: Volume mounts work, integration loads correctly
- **Build pipeline works**: npm build + deploy script successful
- **Browser caching is aggressive**: Hard refresh alone insufficient
- **Query parameters are the solution**: Standard HA pattern for cache busting
