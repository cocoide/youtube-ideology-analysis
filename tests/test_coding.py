import pytest
import tempfile
import sqlite3
import csv
from pathlib import Path
from yt_pilot.coding import (
    CodingDatasetGenerator,
    DictionaryLabeler,
    create_coding_sheet
)


class TestDictionaryLabeler:
    def test_vote_pledge_detection(self):
        """投票宣言の検出テスト"""
        labeler = DictionaryLabeler()
        
        # Positive cases
        assert labeler.predict_vp("明日投票行く") == 1
        assert labeler.predict_vp("投票いきます") == 1
        assert labeler.predict_vp("期日前投票してきた") == 1
        assert labeler.predict_vp("選挙行ってきた") == 1
        assert labeler.predict_vp("投票した") == 1
        assert labeler.predict_vp("投票する予定") == 1
        
        # Negative cases
        assert labeler.predict_vp("投票について考える") == 0
        assert labeler.predict_vp("選挙は大事") == 0
        assert labeler.predict_vp("みんな行こう") == 0
    
    def test_external_efficacy_detection(self):
        """外部効力感の検出テスト"""
        labeler = DictionaryLabeler()
        
        # Positive cases
        assert labeler.predict_e_ext("一票でも変えられる") == 1
        assert labeler.predict_e_ext("私たちの声が届く") == 1
        assert labeler.predict_e_ext("政治を変える力がある") == 1
        assert labeler.predict_e_ext("社会を変えることができる") == 1
        
        # Negative cases
        assert labeler.predict_e_ext("変わらない") == 0
        assert labeler.predict_e_ext("政治は複雑") == 0
    
    def test_internal_efficacy_detection(self):
        """内部効力感の検出テスト"""
        labeler = DictionaryLabeler()
        
        # Positive cases
        assert labeler.predict_e_int("政策をよく調べる") == 1
        assert labeler.predict_e_int("もっと勉強する必要がある") == 1
        assert labeler.predict_e_int("ちゃんと考えて投票") == 1
        assert labeler.predict_e_int("理解してから判断") == 1
        
        # Negative cases
        assert labeler.predict_e_int("よくわからない") == 0
        assert labeler.predict_e_int("難しい") == 0
    
    def test_cynicism_detection(self):
        """シニシズムの検出テスト"""
        labeler = DictionaryLabeler()
        
        # Positive cases
        assert labeler.predict_cyn("どうせ変わらない") == 1
        assert labeler.predict_cyn("投票なんて意味ない") == 1
        assert labeler.predict_cyn("選挙は無駄") == 1
        assert labeler.predict_cyn("何も変わらんよ") == 1
        
        # Negative cases
        assert labeler.predict_cyn("変わるかもしれない") == 0
        assert labeler.predict_cyn("意味があると思う") == 0
    
    def test_multiple_labels(self):
        """複数ラベルが付く場合のテスト"""
        labeler = DictionaryLabeler()
        
        text = "投票行くけど、どうせ変わらないと思う"
        assert labeler.predict_vp(text) == 1
        assert labeler.predict_cyn(text) == 1
        
        text2 = "ちゃんと調べてから投票する。一票でも変えられる"
        assert labeler.predict_vp(text2) == 1
        assert labeler.predict_e_int(text2) == 1
        assert labeler.predict_e_ext(text2) == 1


class TestCodingDatasetGenerator:
    def create_test_db(self, db_path: str):
        """テスト用のデータベースを作成"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE comments (
                comment_id TEXT PRIMARY KEY,
                video_id TEXT,
                published_at TEXT,
                like_count INTEGER,
                total_reply_count INTEGER,
                text TEXT
            )
        ''')
        
        # Insert test data
        test_comments = [
            ('c1', 'v1', '2024-01-01T00:00:00Z', 10, 2, '明日投票行く'),
            ('c2', 'v1', '2024-01-01T01:00:00Z', 5, 0, 'どうせ変わらない'),
            ('c3', 'v2', '2024-01-02T00:00:00Z', 0, 0, '政策をよく調べる必要がある'),
            ('c4', 'v2', '2024-01-02T01:00:00Z', 20, 5, '一票でも社会を変えられる'),
            ('c5', 'v2', '2024-01-02T02:00:00Z', 1, 0, 'テキストに,カンマと\n改行がある場合'),
        ]
        
        cursor.executemany(
            'INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?)',
            test_comments
        )
        
        conn.commit()
        conn.close()
    
    def test_extract_comments(self):
        """データベースからのコメント抽出テスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            self.create_test_db(db_path)
            generator = CodingDatasetGenerator(db_path)
            
            # Extract all comments
            comments = generator.extract_comments()
            assert len(comments) == 5
            
            # Extract with limit
            comments_limited = generator.extract_comments(limit=3)
            assert len(comments_limited) == 3
            
            # Check fields
            first = comments[0]
            assert 'comment_id' in first
            assert 'video_id' in first
            assert 'text' in first
            assert 'like_count' in first
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    def test_generate_coding_sheet(self):
        """コーディングシート生成テスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_csv:
            csv_path = tmp_csv.name
        
        try:
            self.create_test_db(db_path)
            generator = CodingDatasetGenerator(db_path)
            labeler = DictionaryLabeler()
            
            generator.generate_coding_sheet(csv_path, labeler)
            
            # Check CSV exists and has correct structure
            assert Path(csv_path).exists()
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 5
            
            # Check headers
            expected_headers = {
                'video_id', 'comment_id', 'published_at', 'like_count', 
                'total_reply_count', 'text',
                'pred_VP', 'pred_E_int', 'pred_E_ext', 'pred_Cyn', 'pred_Norm', 'pred_Info',
                'VP', 'E_int', 'E_ext', 'Cyn', 'Norm', 'Info', 'unsure', 'coder_memo'
            }
            assert set(rows[0].keys()) == expected_headers
            
            # Check predictions
            assert rows[0]['pred_VP'] == '1'  # "明日投票行く"
            assert rows[1]['pred_Cyn'] == '1'  # "どうせ変わらない"
            assert rows[2]['pred_E_int'] == '1'  # "政策をよく調べる"
            assert rows[3]['pred_E_ext'] == '1'  # "一票でも社会を変えられる"
            
            # Check empty manual coding columns
            assert rows[0]['VP'] == ''
            assert rows[0]['coder_memo'] == ''
            
            # Check CSV handles special characters
            assert '改行がある場合' in rows[4]['text']
            
        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)
    
    def test_reproducible_with_seed(self):
        """シード固定で再現可能なテスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            self.create_test_db(db_path)
            generator = CodingDatasetGenerator(db_path)
            
            # Same seed should give same results
            comments1 = generator.extract_comments(limit=3, seed=42)
            comments2 = generator.extract_comments(limit=3, seed=42)
            
            assert [c['comment_id'] for c in comments1] == [c['comment_id'] for c in comments2]
            
            # Different seed should (likely) give different results
            comments3 = generator.extract_comments(limit=3, seed=123)
            # This could theoretically be the same but unlikely with 5 items
            
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestCLIFunction:
    def test_create_coding_sheet_cli(self):
        """CLI関数のテスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_csv:
            csv_path = tmp_csv.name
        
        try:
            # Create test DB
            generator = CodingDatasetGenerator(':memory:')
            test_gen = TestCodingDatasetGenerator()
            test_gen.create_test_db(db_path)
            
            # Call CLI function
            create_coding_sheet(
                db_path=db_path,
                output_path=csv_path,
                limit=None,
                seed=42
            )
            
            # Check output exists
            assert Path(csv_path).exists()
            
        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)