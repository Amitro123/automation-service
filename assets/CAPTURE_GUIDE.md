# Visual Assets Capture Guide

## Prerequisites
Start the dashboard before capturing assets:
```bash
# Option 1: Docker Compose
docker-compose up -d
# Then access: http://localhost:5173

# Option 2: Dev Mode
python scripts/dev_start.py
# Then access: http://localhost:5173
```

## Assets to Capture

### 1. Hero GIF: Manual Trigger Flow
**Filename**: `manual-trigger-flow.gif`
**Location**: Top of left column (purple gradient panel)

**Steps to Record**:
1. Open dashboard at http://localhost:5173
2. Locate the "Manual Trigger" panel (purple gradient, top-left)
3. Start screen recording
4. Type "main" in the branch input field
5. Click "🚀 Trigger Automation" button
6. Wait for loading spinner to appear
7. Wait for success toast (green with ✓)
8. Scroll down to show System Logs updating
9. Stop recording after 3-4 seconds

**What to Show**:
- Purple gradient panel design
- Input interaction
- Loading state (spinner)
- Toast notification (success)
- Real-time log updates

---

### 2. Screenshot: Failed Run with Retry Button
**Filename**: `failed-run-retry.png`
**Location**: Middle column, "Project Progress" panel

**Steps to Capture**:
1. Navigate to dashboard
2. Scroll to "Project Progress" panel (middle column, bottom)
3. Look for failed runs (red/rose Clock icon)
4. Position view to show:
   - Failed run with rose theme
   - "🔄 Retry" button clearly visible
   - Task title and status
5. Take screenshot

**What to Show**:
- Rose/red theme for failed status
- Retry button with icon
- Clean UI design
- Error handling capability

---

### 3. Screenshot: Config Panel
**Filename**: `config-panel.png`
**Location**: Right column, top

**Steps to Capture**:
1. Navigate to dashboard
2. Scroll to right column
3. Find "Config Panel" at top
4. Position view to show:
   - Panel title
   - Toggle switches
   - Dropdown menus
   - Save button
5. Take screenshot

**What to Show**:
- Configuration options
- Toggle UI elements
- Professional panel design
- System flexibility

---

## Embedding in README

Once captured, add to README.md:

```markdown
## 📸 Dashboard Preview

### Interactive Manual Trigger
![Manual Trigger Flow](./assets/manual-trigger-flow.gif)

*Trigger automation for any commit or branch with instant feedback*

### Error Handling & Recovery
![Failed Run Retry](./assets/failed-run-retry.png)

*One-click retry for failed runs with visual status indicators*

### Flexible Configuration
![Config Panel](./assets/config-panel.png)

*Runtime configuration without server restart*
```

---

## Tips for Best Results

1. **Timing**: Capture during actual automation run for authentic logs
2. **Resolution**: Use 1920x1080 or higher for clarity
3. **GIF Quality**: Keep file size under 5MB for GitHub
4. **Framing**: Show enough context but focus on the feature
5. **Lighting**: Use dashboard's dark theme for consistency

---

## Alternative: Use Screenshots from Browser DevTools

If live capture is difficult:
1. Open dashboard in Chrome
2. Press F12 → Device Toolbar
3. Set viewport to 1920x1080
4. Use "Capture screenshot" in DevTools menu
5. For GIF: Use Chrome's built-in recorder (DevTools → Recorder tab)
