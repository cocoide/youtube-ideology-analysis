#!/usr/bin/env python3
"""Generate improved coding sheet with priority rules and mobilization detection"""

from pathlib import Path
from yt_pilot.improved_coding import create_improved_coding_sheet

def main():
    # Ensure output directory exists
    Path("out").mkdir(exist_ok=True)
    
    # Generate coding sheet with debug information
    db_path = "out/comments.db"
    output_path = "out/improved_coding_sheet.csv"
    
    if Path(db_path).exists():
        count = create_improved_coding_sheet(
            db_path=db_path,
            output_path=output_path,
            limit=100,  # Sample 100 comments
            seed=42,    # For reproducibility
            include_debug=True  # Include priority rules and detected keywords
        )
        print(f"\nGenerated improved coding sheet with {count} comments")
        print(f"File saved to: {output_path}")
        print("\nNew features:")
        print("- Mobilization (Mobi) label detection")
        print("- Priority rules for conflicting labels")
        print("- Cynicism overrides positive labels (VP, E_ext, Norm)")
        print("- VP negation patterns detected")
        print("- Debug columns show applied rules and detected keywords")
    else:
        print(f"Database not found at {db_path}")
        print("Please run data collection first:")
        print("python -m yt_pilot collect --video VIDEO_ID --db out/comments.db")

if __name__ == "__main__":
    main()