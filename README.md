# Series Page v5 - Smart Tab Display for Standalone Series

## The Problem

**Scenario:** You have "Batman: The Killing Joke"
- 1 volume
- 1 issue with format="Graphic Novel"

**Old Behavior (v4):**
```
Tabs: [Volumes] [Issues] [Specials] [Related] [Details]
                  ↑ Empty!  ↑ Has the graphic novel
```

User clicks "Issues" → Empty!  
User has to figure out to check "Specials" tab → Confusing UX!

## The Solution (v5)

**New Behavior:**
```
IF no plain issues exist:
  → Show ALL content in Issues tab
  → Hide Annuals tab (redundant)
  → Hide Specials tab (redundant)
  → Keep Volumes tab (for navigation)
```

**Result:**
```
Tabs: [Volumes] [Issues] [Related] [Details]
                  ↑ Shows the graphic novel here!
```

## How It Works

### Frontend Logic

```javascript
// Computed property
get hasPlainIssues() {
    return this.plainIssues && this.plainIssues.length > 0;
}

// What to show in Issues tab?
getIssuesTabContent() {
    if (this.hasPlainIssues) {
        // Normal series: just plain issues
        return this.plainIssues;
    } else {
        // Standalone series: everything!
        return [
            ...(this.annuals || []),
            ...(this.specials || [])
        ];
    }
}
```

### Tab Visibility

```html
<!-- Annuals tab: only show if hasPlainIssues AND annuals exist -->
<button x-show="hasPlainIssues && series?.annual_count > 0">
    Annuals
</button>

<!-- Specials tab: only show if hasPlainIssues AND specials exist -->
<button x-show="hasPlainIssues && series?.special_count > 0">
    Specials
</button>
```

## Examples

### Example 1: Standalone Graphic Novel

**Series:** Batman: The Killing Joke
- 1 volume
- 1 issue (format="Graphic Novel")
- No plain issues

**Tabs Shown:**
```
[Volumes] [Issues] [Related] [Details]
```

**Issues Tab Shows:**
- Batman: The Killing Joke (with purple "Graphic Novel" badge)

---

### Example 2: Standalone One-Shots

**Series:** Superman: Red Son
- 1 volume
- 3 issues (format="One-Shot")
- No plain issues

**Tabs Shown:**
```
[Volumes] [Issues] [Related] [Details]
```

**Issues Tab Shows:**
- Red Son #1 (with purple "One-Shot" badge)
- Red Son #2 (with purple "One-Shot" badge)
- Red Son #3 (with purple "One-Shot" badge)

---

### Example 3: TPB Collection

**Series:** Watchmen
- 1 volume
- 1 issue (format="Trade Paperback")
- No plain issues

**Tabs Shown:**
```
[Volumes] [Issues] [Related] [Details]
```

**Issues Tab Shows:**
- Watchmen TPB (with purple "Trade Paperback" badge)

---

### Example 4: Normal Series (Unchanged)

**Series:** Batman
- 5 volumes
- 120 plain issues
- 15 annuals
- 8 specials

**Tabs Shown:**
```
[Volumes] [Issues] [Annuals] [Specials] [Related] [Details]
```

**Issues Tab Shows:**
- Batman #1
- Batman #2
- ... (120 plain issues)

**Annuals Tab Shows:**
- Batman Annual #1
- ... (15 annuals)

**Specials Tab Shows:**
- Batman Giant-Size #1
- ... (8 specials)

---

### Example 5: Series with Only Annuals

**Series:** Amazing Spider-Man Annuals
- 1 volume
- 5 issues (format="Annual")
- No plain issues, no specials

**Tabs Shown:**
```
[Volumes] [Issues] [Related] [Details]
```

**Issues Tab Shows:**
- Amazing Spider-Man Annual #1 (with yellow "Annual" badge)
- Amazing Spider-Man Annual #2 (with yellow "Annual" badge)
- ... (5 annuals with badges)

## Visual Indicators

When Issues tab shows non-plain issues, they still have their format badges:

```
┌─────────────┐
│   Cover     │
│             │ [Annual] ← Yellow badge
│             │
└─────────────┘
Vol 1 #1
Annual Title
1990
```

```
┌─────────────┐
│   Cover     │
│             │ [Graphic Novel] ← Purple badge
│             │
└─────────────┘
Vol 1 #1
The Killing Joke
1988
```

This way users know these aren't "normal" issues even though they're in the Issues tab.

## Statistics Display

### Normal Series (has plain issues)
```
5 volumes • 120 issues • 15 annuals • 8 specials
           ↑ Plain     ↑ Shown    ↑ Shown
```

### Standalone Series (no plain issues)
```
1 volume • 1 issue
          ↑ Total count (annuals + specials)
```

No separate annual/special counts shown since they're all in Issues tab.

## Key Features

✅ **No empty tabs** - Users always see content in Issues tab  
✅ **Format badges** - Still visible so users know what they're looking at  
✅ **Volumes tab stays** - Can still navigate to future volume detail page  
✅ **Auto-detection** - No configuration needed, just works  
✅ **Backwards compatible** - Normal series work exactly as before  

## Installation

Just replace the template:

```bash
cp series_detail_v5.html /path/to/your-project/app/templates/series_detail.html
python main.py  # Restart
```

No API changes needed! This is pure frontend logic.

## Testing Checklist

After updating:

- [ ] **Standalone graphic novel**: Shows in Issues tab, no Annuals/Specials tabs
- [ ] **Standalone one-shots**: Show in Issues tab, no Annuals/Specials tabs
- [ ] **Normal series**: Issues/Annuals/Specials tabs all visible and correct
- [ ] **Series with annuals only**: Annuals show in Issues tab with badges
- [ ] **Series with specials only**: Specials show in Issues tab with badges
- [ ] **Format badges visible**: Even when shown in Issues tab
- [ ] **Statistics correct**: Shows total count for standalone, separate for normal


---

**No more empty tabs!** 🎉
