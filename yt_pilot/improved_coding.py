"""Improved coding with priority rules and mobilization detection"""

import sqlite3
import csv
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class ImprovedDictionaryLabeler:
    """Dictionary-based labeling with priority rules and conflict resolution"""
    
    def __init__(self):
        # Define dictionaries for each label
        self.vp_keywords = [
            "投票行く", "投票いく", "投票いき", "投票に行", "行ってくる", "行ってきた", 
            "投票した", "期日前", "投票する", "選挙行", "投票所",
            "投票済", "投票しよう"
        ]
        
        self.e_ext_keywords = [
            "一票でも", "変えられる", "声が届く", 
            "政治を変える", "社会を変える", "民主主義", "主権在民",
            "私たちの声"
        ]
        
        self.e_int_keywords = [
            "調べる", "調べて", "調べた", "勉強する", "ちゃんと考え", 
            "理解して", "判断する", "情報収集", "比較して"
        ]
        
        self.cyn_keywords = [
            "どうせ変わらない", "意味ない", "無駄", "変わらん",
            "茶番", "出来レース", "利権", "癒着", "腐って"
        ]
        
        self.norm_keywords = [
            "行くべき", "行かなきゃ", "行かないのは", "責任",
            "国民の義務", "権利を行使"
        ]
        
        self.info_keywords = [
            "どこで", "やり方", "方法", "候補者", "政策",
            "何時から", "持ち物", "場所", "投票用紙"
        ]
        
        # New: Mobilization keywords
        self.mobi_keywords = [
            "みんなで", "一緒に行こう", "友達と", "家族と",
            "声をかけて", "誘って", "広めて", "シェアして",
            "拡散", "周りの人"
        ]
        
        # Cynicism modifiers that intensify cynicism detection
        self.cyn_modifiers = [
            "本当に", "マジで", "ガチで", "絶対", "どうせ", "結局"
        ]
        
        # VP negation patterns
        self.vp_negations = [
            "投票行かない", "投票に行かない", "投票しない", "選挙行かない",
            "投票できない", "投票やめ", "投票いかない"
        ]
    
    def _check_keywords(self, text: str, keywords: List[str]) -> Tuple[int, List[str]]:
        """Check if any keyword exists in text and return matches"""
        text_lower = text.lower()
        matches = []
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        return (1 if matches else 0, matches)
    
    def _check_negations(self, text: str, patterns: List[str]) -> bool:
        """Check for negation patterns"""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in patterns)
    
    def predict_with_priority(self, text: str) -> Dict[str, Any]:
        """Predict all labels with priority rules and conflict resolution"""
        results = {
            'pred_VP': 0,
            'pred_E_int': 0,
            'pred_E_ext': 0,
            'pred_Cyn': 0,
            'pred_Norm': 0,
            'pred_Info': 0,
            'pred_Mobi': 0,
            'priority_applied': [],
            'detected_keywords': {}
        }
        
        # First, detect all potential labels
        vp_detected, vp_matches = self._check_keywords(text, self.vp_keywords)
        e_ext_detected, e_ext_matches = self._check_keywords(text, self.e_ext_keywords)
        e_int_detected, e_int_matches = self._check_keywords(text, self.e_int_keywords)
        cyn_detected, cyn_matches = self._check_keywords(text, self.cyn_keywords)
        norm_detected, norm_matches = self._check_keywords(text, self.norm_keywords)
        info_detected, info_matches = self._check_keywords(text, self.info_keywords)
        mobi_detected, mobi_matches = self._check_keywords(text, self.mobi_keywords)
        
        # Check for VP negations
        vp_negated = self._check_negations(text, self.vp_negations)
        
        # Store detected keywords for transparency
        if vp_matches: results['detected_keywords']['VP'] = vp_matches
        if e_ext_matches: results['detected_keywords']['E_ext'] = e_ext_matches
        if e_int_matches: results['detected_keywords']['E_int'] = e_int_matches
        if cyn_matches: results['detected_keywords']['Cyn'] = cyn_matches
        if norm_matches: results['detected_keywords']['Norm'] = norm_matches
        if info_matches: results['detected_keywords']['Info'] = info_matches
        if mobi_matches: results['detected_keywords']['Mobi'] = mobi_matches
        
        # Priority 1: Check VP negation first (before applying VP)
        if vp_negated:
            vp_detected = 0  # Override VP detection if negated
            results['priority_applied'].append('VP_negated')
        
        # Priority 2: Cynicism overrides positive labels
        if cyn_detected:
            results['pred_Cyn'] = 1
            results['priority_applied'].append('Cyn_overrides_positive')
            
            # Cynicism typically contradicts VP, E_ext, and Norm
            # But can coexist with E_int (studying but cynical) and Info (asking how but cynical)
            results['pred_VP'] = 0
            results['pred_E_ext'] = 0
            results['pred_Norm'] = 0
            
            # Allow these if detected
            results['pred_E_int'] = e_int_detected
            results['pred_Info'] = info_detected
            results['pred_Mobi'] = 0  # Cynicism contradicts mobilization
            
        else:
            # Apply labels without cynicism
            results['pred_VP'] = vp_detected
            results['pred_E_ext'] = e_ext_detected
            results['pred_E_int'] = e_int_detected
            results['pred_Norm'] = norm_detected
            results['pred_Info'] = info_detected
            results['pred_Mobi'] = mobi_detected
        
        # Priority 3: Mobilization can coexist with VP but enhances it
        if mobi_detected and vp_detected and not cyn_detected:
            results['priority_applied'].append('Mobi_enhances_VP')
        
        return results
    
    def predict_all(self, text: str) -> Dict[str, int]:
        """Legacy method for compatibility - returns simple predictions"""
        full_results = self.predict_with_priority(text)
        return {
            'pred_VP': full_results['pred_VP'],
            'pred_E_int': full_results['pred_E_int'],
            'pred_E_ext': full_results['pred_E_ext'],
            'pred_Cyn': full_results['pred_Cyn'],
            'pred_Norm': full_results['pred_Norm'],
            'pred_Info': full_results['pred_Info'],
            'pred_Mobi': full_results['pred_Mobi']
        }


class ImprovedCodingDatasetGenerator:
    """Generate coding sheets with improved labeling"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def extract_comments(self, limit: Optional[int] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract comments from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT comment_id, video_id, published_at, 
                   like_count, total_reply_count, text
            FROM comments
        """
        
        # Add random ordering if seed is specified
        if seed is not None:
            # Use a deterministic but pseudo-random ordering
            query += f" ORDER BY ((length(comment_id) * {seed}) % 100), comment_id"
        
        # Add limit
        if limit is not None:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        comments = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return comments
    
    def generate_improved_coding_sheet(self, output_path: str, labeler: ImprovedDictionaryLabeler, 
                                      limit: Optional[int] = None, seed: Optional[int] = None,
                                      include_debug: bool = True):
        """Generate coding sheet CSV with improved labels and debug info"""
        # Extract comments
        comments = self.extract_comments(limit, seed)
        
        # Define all columns
        fieldnames = [
            'video_id', 'comment_id', 'published_at', 'like_count', 'total_reply_count', 'text',
            'pred_VP', 'pred_E_int', 'pred_E_ext', 'pred_Cyn', 'pred_Norm', 'pred_Info', 'pred_Mobi',
            'VP', 'E_int', 'E_ext', 'Cyn', 'Norm', 'Info', 'Mobi', 'unsure', 'coder_memo'
        ]
        
        if include_debug:
            fieldnames.extend(['priority_rules', 'detected_keywords'])
        
        # Create output directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for comment in comments:
                # Get predictions with priority info
                full_predictions = labeler.predict_with_priority(comment['text'])
                
                # Prepare row
                row = {
                    'video_id': comment['video_id'],
                    'comment_id': comment['comment_id'],
                    'published_at': comment['published_at'],
                    'like_count': comment['like_count'],
                    'total_reply_count': comment['total_reply_count'],
                    'text': comment['text'],
                    # Predictions
                    'pred_VP': full_predictions['pred_VP'],
                    'pred_E_int': full_predictions['pred_E_int'],
                    'pred_E_ext': full_predictions['pred_E_ext'],
                    'pred_Cyn': full_predictions['pred_Cyn'],
                    'pred_Norm': full_predictions['pred_Norm'],
                    'pred_Info': full_predictions['pred_Info'],
                    'pred_Mobi': full_predictions['pred_Mobi'],
                    # Empty columns for manual coding
                    'VP': '',
                    'E_int': '',
                    'E_ext': '',
                    'Cyn': '',
                    'Norm': '',
                    'Info': '',
                    'Mobi': '',
                    'unsure': '',
                    'coder_memo': ''
                }
                
                if include_debug:
                    row['priority_rules'] = ';'.join(full_predictions['priority_applied'])
                    row['detected_keywords'] = str(full_predictions['detected_keywords'])
                
                writer.writerow(row)
        
        return len(comments)


def create_improved_coding_sheet(db_path: str, output_path: str, limit: Optional[int] = None, 
                                seed: Optional[int] = None, include_debug: bool = True) -> int:
    """CLI function to create improved coding sheet"""
    generator = ImprovedCodingDatasetGenerator(db_path)
    labeler = ImprovedDictionaryLabeler()
    
    count = generator.generate_improved_coding_sheet(
        output_path, labeler, limit, seed, include_debug
    )
    print(f"Generated improved coding sheet with {count} comments: {output_path}")
    
    return count