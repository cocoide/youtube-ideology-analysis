"""Tests for improved coding with priority rules"""

import pytest
from yt_pilot.improved_coding import ImprovedDictionaryLabeler


class TestImprovedDictionaryLabeler:
    def test_basic_label_detection(self):
        """Test basic label detection without conflicts"""
        labeler = ImprovedDictionaryLabeler()
        
        # Test VP detection
        result = labeler.predict_all("明日投票に行ってきます")
        assert result['pred_VP'] == 1
        assert result['pred_Cyn'] == 0
        
        # Test E_ext detection
        result = labeler.predict_all("私たちの一票で政治を変えることができる")
        assert result['pred_E_ext'] == 1
        
        # Test Mobi detection
        result = labeler.predict_all("みんなで投票に行こう！友達も誘って")
        assert result['pred_Mobi'] == 1
        assert result['pred_VP'] == 1
    
    def test_cynicism_priority_rule(self):
        """Test that cynicism overrides positive labels"""
        labeler = ImprovedDictionaryLabeler()
        
        # Cynicism should override VP
        result = labeler.predict_with_priority("投票に行くけど、どうせ変わらないよね")
        assert result['pred_Cyn'] == 1
        assert result['pred_VP'] == 0  # VP overridden by cynicism
        assert 'Cyn_overrides_positive' in result['priority_applied']
        
        # Cynicism should override E_ext
        result = labeler.predict_with_priority("一票で変えられるなんて言うけど、結局無駄だよ")
        assert result['pred_Cyn'] == 1
        assert result['pred_E_ext'] == 0  # E_ext overridden
        
        # Cynicism allows E_int (studying but cynical)
        result = labeler.predict_with_priority("ちゃんと調べたけど、どうせ意味ないよね")
        assert result['pred_Cyn'] == 1
        assert result['pred_E_int'] == 1  # E_int allowed with cynicism
    
    def test_vp_negation(self):
        """Test VP negation patterns"""
        labeler = ImprovedDictionaryLabeler()
        
        # Direct negation
        result = labeler.predict_with_priority("今回は投票に行かない")
        assert result['pred_VP'] == 0
        assert 'VP_negated' in result['priority_applied']
        
        # Negation even with other VP keywords
        result = labeler.predict_with_priority("期日前投票もあるけど投票しないつもり")
        assert result['pred_VP'] == 0
    
    def test_mobilization_with_vp(self):
        """Test mobilization enhancement of VP"""
        labeler = ImprovedDictionaryLabeler()
        
        # Mobi + VP together
        result = labeler.predict_with_priority("みんなで投票所に行こう！一緒に投票する人募集")
        assert result['pred_VP'] == 1
        assert result['pred_Mobi'] == 1
        assert 'Mobi_enhances_VP' in result['priority_applied']
        
        # Mobi alone without VP
        result = labeler.predict_with_priority("この情報をシェアして広めてください")
        assert result['pred_Mobi'] == 1
        assert result['pred_VP'] == 0
    
    def test_keyword_detection_transparency(self):
        """Test that detected keywords are recorded"""
        labeler = ImprovedDictionaryLabeler()
        
        result = labeler.predict_with_priority("投票行く予定。ちゃんと調べて判断する。")
        assert 'VP' in result['detected_keywords']
        assert '投票行く' in result['detected_keywords']['VP']
        assert 'E_int' in result['detected_keywords']
        assert any('調べて' in kw or '判断する' in kw for kw in result['detected_keywords']['E_int'])
    
    def test_complex_comment_with_multiple_labels(self):
        """Test complex comments with multiple conflicting labels"""
        labeler = ImprovedDictionaryLabeler()
        
        # Complex case: cynicism wins
        text = "投票は国民の義務だし行くべきだけど、結局は茶番で意味ないよね。でも一応調べてはいる。"
        result = labeler.predict_with_priority(text)
        assert result['pred_Cyn'] == 1  # Cynicism detected
        assert result['pred_VP'] == 0  # VP overridden
        assert result['pred_Norm'] == 0  # Norm overridden
        assert result['pred_E_int'] == 1  # E_int allowed
        
        # Complex case: no cynicism, multiple positives
        text = "明日期日前投票に行く！友達も誘って一緒に。私たちの声で政治を変えよう"
        result = labeler.predict_with_priority(text)
        assert result['pred_VP'] == 1
        assert result['pred_Mobi'] == 1
        assert result['pred_E_ext'] == 1
        assert result['pred_Cyn'] == 0
    
    def test_info_seeking_coexists(self):
        """Test that info seeking can coexist with other labels"""
        labeler = ImprovedDictionaryLabeler()
        
        # Info + Cynicism
        result = labeler.predict_all("投票所の場所どこ？でもどうせ無駄だけどね")
        assert result['pred_Info'] == 1
        assert result['pred_Cyn'] == 1
        
        # Info + VP
        result = labeler.predict_all("投票用紙の書き方教えて。初めて投票に行く")
        assert result['pred_Info'] == 1
        assert result['pred_VP'] == 1