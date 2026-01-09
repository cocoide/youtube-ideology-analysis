# Improved Labeling System

This document describes the enhanced labeling system with priority rules and mobilization detection.

## New Features

### 1. Mobilization (Mobi) Label
Detects comments encouraging collective action and social sharing:
- Keywords: "みんなで", "一緒に行こう", "友達と", "家族と", "声をかけて", "誘って", "広めて", "シェアして", "拡散", "周りの人"
- Example: "みんなで投票に行こう！友達も誘って" → VP + Mobi

### 2. Priority Rules for Conflicting Labels

#### Cynicism Override (Priority 1)
When cynicism is detected, it overrides positive labels:
- Overrides: VP, E_ext, Norm, Mobi
- Allows: E_int (studying but cynical), Info (asking how but cynical)
- Example: "投票に行くけど、どうせ変わらないよね" → Cyn only (VP overridden)

#### VP Negation (Priority 2)
Detects negative voting intentions:
- Patterns: "投票行かない", "投票に行かない", "投票しない", "選挙行かない", etc.
- Example: "今回は投票に行かない" → No VP despite "投票" keyword

#### Mobilization Enhancement
When both Mobi and VP are detected without cynicism:
- Marks as "Mobi_enhances_VP" in priority rules
- Example: "みんなで投票所に行こう！" → VP + Mobi + enhancement

## Usage

### CLI Command
```bash
# Generate improved coding sheet
python -m yt_pilot make-improved-coding-sheet \
    --db out/comments.db \
    --out out/improved_coding_sheet.csv \
    --limit 100 \
    --seed 42

# Without debug columns
python -m yt_pilot make-improved-coding-sheet \
    --db out/comments.db \
    --out out/improved_coding_sheet.csv \
    --no-debug
```

### Python API
```python
from yt_pilot.improved_coding import ImprovedDictionaryLabeler

labeler = ImprovedDictionaryLabeler()

# Get predictions with priority info
result = labeler.predict_with_priority("投票に行くけど、どうせ変わらないよね")
print(result['priority_applied'])  # ['Cyn_overrides_positive']
print(result['detected_keywords'])  # {'VP': ['投票に行'], 'Cyn': ['どうせ変わらない']}

# Get simple predictions
predictions = labeler.predict_all("みんなで投票に行こう")
print(predictions)  # {'pred_VP': 1, 'pred_Mobi': 1, ...}
```

## Output Format

The improved coding sheet includes:
- All original fields (video_id, comment_id, text, etc.)
- Predictions: pred_VP, pred_E_int, pred_E_ext, pred_Cyn, pred_Norm, pred_Info, **pred_Mobi**
- Manual coding columns: VP, E_int, E_ext, Cyn, Norm, Info, **Mobi**, unsure, coder_memo
- Debug columns (optional):
  - priority_rules: Applied priority rules (e.g., "Cyn_overrides_positive;VP_negated")
  - detected_keywords: Dictionary of detected keywords by label

## Priority Rule Examples

1. **Cynicism wins**
   - Text: "投票は国民の義務だけど、結局は茶番で意味ない"
   - Detected: Norm + Cyn
   - Result: Cyn only (Norm overridden)

2. **VP negation**
   - Text: "期日前投票もあるけど投票しないつもり"
   - Detected: VP keyword "期日前" + negation "投票しない"
   - Result: No VP

3. **Complex case**
   - Text: "明日期日前投票に行く！友達も誘って。私たちの声で政治を変えよう"
   - Result: VP + E_ext + Mobi (with enhancement)

## Testing

Run tests for the improved labeling system:
```bash
python3 -m pytest tests/test_improved_coding.py -v
```

## Demo

Run the demo to see labeling examples:
```bash
python3 demo_improved_labeling.py
```