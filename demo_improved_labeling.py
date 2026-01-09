#!/usr/bin/env python3
"""Demo of improved labeling with priority rules"""

from yt_pilot.improved_coding import ImprovedDictionaryLabeler
import json

def demo_labeling():
    labeler = ImprovedDictionaryLabeler()
    
    # Test cases demonstrating priority rules
    test_comments = [
        # Basic labels
        "明日投票に行ってきます",
        "私たちの一票で政治を変えられる",
        "ちゃんと調べて投票する",
        
        # Mobilization
        "みんなで投票に行こう！友達も誘って",
        "この情報をシェアして広めてください",
        
        # Cynicism overrides
        "投票に行くけど、どうせ変わらないよね",
        "一票で変えられるなんて言うけど、結局無駄だよ",
        
        # VP negation
        "今回は投票に行かない",
        "期日前投票もあるけど投票しないつもり",
        
        # Complex cases
        "投票は国民の義務だし行くべきだけど、結局は茶番で意味ないよね。でも一応調べてはいる。",
        "明日期日前投票に行く！友達も誘って一緒に。私たちの声で政治を変えよう",
        
        # Info seeking
        "投票所の場所どこ？でもどうせ無駄だけどね",
        "投票用紙の書き方教えて。初めて投票に行く",
    ]
    
    print("=== Improved Labeling Demo ===\n")
    
    for i, comment in enumerate(test_comments, 1):
        print(f"--- Comment {i} ---")
        print(f"Text: {comment}")
        
        # Get full results with priority info
        results = labeler.predict_with_priority(comment)
        
        # Show detected labels
        labels = []
        if results['pred_VP']: labels.append('VP')
        if results['pred_E_ext']: labels.append('E_ext')
        if results['pred_E_int']: labels.append('E_int')
        if results['pred_Cyn']: labels.append('Cyn')
        if results['pred_Norm']: labels.append('Norm')
        if results['pred_Info']: labels.append('Info')
        if results['pred_Mobi']: labels.append('Mobi')
        
        print(f"Labels: {', '.join(labels) if labels else 'None'}")
        
        # Show priority rules applied
        if results['priority_applied']:
            print(f"Priority rules: {', '.join(results['priority_applied'])}")
        
        # Show detected keywords
        if results['detected_keywords']:
            print(f"Keywords detected:")
            for label, keywords in results['detected_keywords'].items():
                print(f"  {label}: {', '.join(keywords)}")
        
        print()

if __name__ == "__main__":
    demo_labeling()