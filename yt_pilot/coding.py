"""Coding dataset generation and dictionary-based labeling"""

import sqlite3
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path


class DictionaryLabeler:
    """Dictionary-based preliminary labeling for comments"""
    
    def __init__(self):
        # Define dictionaries for each label
        self.vp_keywords = [
            "投票行く", "投票いく", "投票いき", "行ってくる", "行ってきた", 
            "投票した", "期日前", "投票する", "選挙行"
        ]
        
        self.e_ext_keywords = [
            "一票でも", "変えられる", "声が届く", 
            "政治を変える", "社会を変える"
        ]
        
        self.e_int_keywords = [
            "調べる", "調べて", "勉強する", "ちゃんと考え", 
            "理解して", "判断する"
        ]
        
        self.cyn_keywords = [
            "どうせ変わらない", "意味ない", "無駄", "変わらん"
        ]
        
        self.norm_keywords = [
            "行くべき", "行かなきゃ", "行かないのは"
        ]
        
        self.info_keywords = [
            "どこで", "やり方", "方法", "候補者", "政策"
        ]
    
    def _check_keywords(self, text: str, keywords: List[str]) -> int:
        """Check if any keyword exists in text"""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return 1
        return 0
    
    def predict_vp(self, text: str) -> int:
        """Predict vote pledge"""
        return self._check_keywords(text, self.vp_keywords)
    
    def predict_e_ext(self, text: str) -> int:
        """Predict external efficacy"""
        return self._check_keywords(text, self.e_ext_keywords)
    
    def predict_e_int(self, text: str) -> int:
        """Predict internal efficacy"""
        return self._check_keywords(text, self.e_int_keywords)
    
    def predict_cyn(self, text: str) -> int:
        """Predict cynicism"""
        return self._check_keywords(text, self.cyn_keywords)
    
    def predict_norm(self, text: str) -> int:
        """Predict normative appeal"""
        return self._check_keywords(text, self.norm_keywords)
    
    def predict_info(self, text: str) -> int:
        """Predict information seeking"""
        return self._check_keywords(text, self.info_keywords)
    
    def predict_all(self, text: str) -> Dict[str, int]:
        """Predict all labels for a text"""
        return {
            'pred_VP': self.predict_vp(text),
            'pred_E_int': self.predict_e_int(text),
            'pred_E_ext': self.predict_e_ext(text),
            'pred_Cyn': self.predict_cyn(text),
            'pred_Norm': self.predict_norm(text),
            'pred_Info': self.predict_info(text)
        }


class CodingDatasetGenerator:
    """Generate coding sheets from comment database"""
    
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
    
    def generate_coding_sheet(self, output_path: str, labeler: DictionaryLabeler, 
                             limit: Optional[int] = None, seed: Optional[int] = None):
        """Generate coding sheet CSV with preliminary labels"""
        # Extract comments
        comments = self.extract_comments(limit, seed)
        
        # Define all columns
        fieldnames = [
            'video_id', 'comment_id', 'published_at', 'like_count', 'total_reply_count', 'text',
            'pred_VP', 'pred_E_int', 'pred_E_ext', 'pred_Cyn', 'pred_Norm', 'pred_Info',
            'VP', 'E_int', 'E_ext', 'Cyn', 'Norm', 'Info', 'unsure', 'coder_memo'
        ]
        
        # Create output directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for comment in comments:
                # Get predictions
                predictions = labeler.predict_all(comment['text'])
                
                # Prepare row
                row = {
                    'video_id': comment['video_id'],
                    'comment_id': comment['comment_id'],
                    'published_at': comment['published_at'],
                    'like_count': comment['like_count'],
                    'total_reply_count': comment['total_reply_count'],
                    'text': comment['text'],
                    # Predictions
                    'pred_VP': predictions['pred_VP'],
                    'pred_E_int': predictions['pred_E_int'],
                    'pred_E_ext': predictions['pred_E_ext'],
                    'pred_Cyn': predictions['pred_Cyn'],
                    'pred_Norm': predictions['pred_Norm'],
                    'pred_Info': predictions['pred_Info'],
                    # Empty columns for manual coding
                    'VP': '',
                    'E_int': '',
                    'E_ext': '',
                    'Cyn': '',
                    'Norm': '',
                    'Info': '',
                    'unsure': '',
                    'coder_memo': ''
                }
                
                writer.writerow(row)
        
        return len(comments)


def create_coding_sheet(db_path: str, output_path: str, limit: Optional[int] = None, 
                       seed: Optional[int] = None) -> int:
    """CLI function to create coding sheet"""
    generator = CodingDatasetGenerator(db_path)
    labeler = DictionaryLabeler()
    
    count = generator.generate_coding_sheet(output_path, labeler, limit, seed)
    print(f"Generated coding sheet with {count} comments: {output_path}")
    
    return count