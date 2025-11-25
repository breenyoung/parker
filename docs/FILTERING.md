# Series Page v4 - API Does the Filtering

## Problem in v2/v3

### Backend (Python)
```python
# Had NON_PLAIN_FORMATS list
NON_PLAIN_FORMATS = ['annual', 'giant-size', 'limited series', ...]
```

### Frontend (JavaScript)
```javascript
// But didn't have access to that list!
this.plainIssues = sorted.filter(issue => !issue.format);  // ❌ Wrong
this.annuals = sorted.filter(issue => 
    issue.format && issue.format.toLowerCase() === 'annual'
);
this.specials = sorted.filter(issue => 
    issue.format && issue.format.toLowerCase() !== 'annual'  // ❌ Wrong
);
```

**Result:** Issues with format='Limited Series' were showing in Issues tab because JavaScript only checked `!issue.format`

## Solution in v4

✅ **API does ALL the filtering and sorting**  
✅ **Frontend just displays the pre-categorized lists**  
✅ **Single source of truth: NON_PLAIN_FORMATS list in Python**

## How It Works Now

### Backend API Response
```json
{
  "volumes": [...],
  "plain_issues": [...],    // ✅ Pre-filtered & sorted
  "annuals": [...],         // ✅ Pre-filtered & sorted
  "specials": [...],        // ✅ Pre-filtered & sorted
  "total_issues": 120,      // Count of plain_issues
  "annual_count": 15,
  "special_count": 8
}
```

### Frontend JavaScript
```javascript
async loadSeries() {
    const data = await response.json();
    
    // Just assign! No filtering needed!
    this.plainIssues = data.plain_issues || [];
    this.annuals = data.annuals || [];
    this.specials = data.specials || [];
}
```

## Backend Filtering Logic

```python
# Module-level constant
NON_PLAIN_FORMATS = [
    'annual',
    'giant-size',
    'graphic novel',
    'one shot',
    'one-shot',
    'hardcover',
    'limited series',      # ✅ Now properly excluded!
    'trade paperback',
    'tpb',
]

def is_plain_issue(comic: Comic) -> bool:
    """Plain = no format OR format not in exclusion list"""
    if not comic.format:
        return True
    return comic.format.lower().strip() not in NON_PLAIN_FORMATS

def is_annual(comic: Comic) -> bool:
    """Annual = format is 'annual'"""
    if not comic.format:
        return False
    return comic.format.lower().strip() == 'annual'

def is_special(comic: Comic) -> bool:
    """Special = in NON_PLAIN_FORMATS but not 'annual'"""
    if not comic.format:
        return False
    format_lower = comic.format.lower().strip()
    return format_lower != 'annual' and format_lower in NON_PLAIN_FORMATS

# Use them
plain_issues = [c for c in comics if is_plain_issue(c)]
annuals = [c for c in comics if is_annual(c)]
specials = [c for c in comics if is_special(c)]

# Sort before sending
plain_issues_sorted = sort_by_volume_and_number(plain_issues)
annuals_sorted = sort_by_volume_and_number(annuals)
specials_sorted = sort_by_volume_and_number(specials)

# Convert to JSON
return {
    "plain_issues": [comic_to_dict(c) for c in plain_issues_sorted],
    "annuals": [comic_to_dict(c) for c in annuals_sorted],
    "specials": [comic_to_dict(c) for c in specials_sorted],
    # ...
}
```

## Benefits

✅ **Single source of truth** - NON_PLAIN_FORMATS only defined once  
✅ **Consistent filtering** - Same logic everywhere  
✅ **Easier to maintain** - Update list in one place  
✅ **Better performance** - Filtering happens once on server  
✅ **Less JavaScript complexity** - Frontend just displays data  
✅ **Correct counts** - Statistics match what users see  

## Format Categories

| Format | is_plain_issue() | is_annual() | is_special() | Tab |
|--------|-----------------|-------------|--------------|-----|
| `null` | ✅ Yes | No | No | Issues |
| `""` | ✅ Yes | No | No | Issues |
| `"Annual"` | No | ✅ Yes | No | Annuals |
| `"Giant-Size"` | No | No | ✅ Yes | Specials |
| `"Limited Series"` | No | No | ✅ Yes | Specials |
| `"One-Shot"` | No | No | ✅ Yes | Specials |
| `"Graphic Novel"` | No | No | ✅ Yes | Specials |
| `"Hardcover"` | No | No | ✅ Yes | Specials |
| `"TPB"` | No | No | ✅ Yes | Specials |

## Installation

### Step 1: Update API
```bash
cp series_api_v4.py /path/to/your-project/app/api/series.py
```

### Step 2: Update Template
```bash
cp series_detail_v4.html /path/to/your-project/app/templates/series_detail.html
```

### Step 3: Restart
```bash
python main.py
```

## Testing

### Before (v2/v3)
- Comic with format="Limited Series" → Shows in **Issues** tab ❌

### After (v4)
- Comic with format="Limited Series" → Shows in **Specials** tab ✅

### Test Cases

1. **Plain Issue** (format=null)
   - Should appear in: Issues tab
   - Should count toward: total_issues

2. **Annual** (format="Annual")
   - Should appear in: Annuals tab
   - Should count toward: annual_count

3. **Limited Series** (format="Limited Series")
   - Should appear in: Specials tab ✅ FIXED
   - Should count toward: special_count

4. **Giant-Size** (format="Giant-Size")
   - Should appear in: Specials tab
   - Should count toward: special_count

## Adding New Formats

Just update the Python list:

```python
NON_PLAIN_FORMATS = [
    'annual',
    'giant-size',
    # ... existing
    'special',          # ADD NEW
    'king-size',        # ADD NEW
    'treasury',         # ADD NEW
]
```

No JavaScript changes needed! 🎉

## API Endpoint Changes

### Old Response (v2/v3)
```json
{
  "issues": [
    // All issues mixed together
  ]
}
```

### New Response (v4)
```json
{
  "plain_issues": [
    // Only plain issues, pre-filtered & sorted
  ],
  "annuals": [
    // Only annuals, pre-filtered & sorted
  ],
  "specials": [
    // Only specials, pre-filtered & sorted
  ]
}
```

## Frontend Code Changes

### Before (v2/v3) - Filtering in JS
```javascript
processIssues(issues) {
    const sorted = [...issues].sort(...);
    
    // Frontend does filtering ❌
    this.plainIssues = sorted.filter(issue => !issue.format);
    this.annuals = sorted.filter(issue => 
        issue.format && issue.format.toLowerCase() === 'annual'
    );
    this.specials = sorted.filter(issue => 
        issue.format && issue.format.toLowerCase() !== 'annual'
    );
}
```

### After (v4) - Just Assign
```javascript
async loadSeries() {
    const data = await response.json();
    
    // Just assign pre-filtered data ✅
    this.plainIssues = data.plain_issues || [];
    this.annuals = data.annuals || [];
    this.specials = data.specials || [];
}
```

