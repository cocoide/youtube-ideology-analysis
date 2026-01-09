#!/usr/bin/env python3
"""収集したサンプルデータの基本分析"""

import csv
import sqlite3
from collections import Counter
import os
import sys

def analyze_csv(csv_path):
    """CSVファイルからコメントデータを分析"""
    print(f"\n分析対象: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        comments = list(reader)
    
    print(f"総コメント数: {len(comments)}")
    
    # 基本統計
    like_counts = [int(c['likeCount']) for c in comments]
    reply_counts = [int(c['totalReplyCount']) for c in comments]
    
    print(f"いいね数の平均: {sum(like_counts) / len(like_counts):.2f}")
    print(f"いいね数の最大: {max(like_counts)}")
    print(f"返信数の平均: {sum(reply_counts) / len(reply_counts):.2f}")
    print(f"返信数の最大: {max(reply_counts)}")
    
    # テキスト長の分析
    text_lengths = [len(c['text']) for c in comments]
    print(f"\nコメント文字数:")
    print(f"  平均: {sum(text_lengths) / len(text_lengths):.1f}文字")
    print(f"  最短: {min(text_lengths)}文字")
    print(f"  最長: {max(text_lengths)}文字")
    
    # よく使われる単語（簡易版）
    print(f"\nよく使われる単語TOP10:")
    words = []
    for c in comments:
        # 簡易的な単語分割（日本語対応なし）
        words.extend([w for w in c['text'].split() if len(w) > 3])
    
    word_counter = Counter(words)
    for word, count in word_counter.most_common(10):
        print(f"  {word}: {count}回")
    
    # サンプルコメント表示
    print(f"\n最もいいねが多いコメントTOP3:")
    sorted_comments = sorted(comments, key=lambda x: int(x['likeCount']), reverse=True)
    for i, c in enumerate(sorted_comments[:3], 1):
        print(f"\n{i}. いいね数: {c['likeCount']}")
        print(f"   {c['text'][:100]}{'...' if len(c['text']) > 100 else ''}")

def analyze_db(db_path):
    """SQLiteデータベースの統計情報"""
    print(f"\n\nデータベース分析: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 動画数
    cursor.execute("SELECT COUNT(DISTINCT video_id) FROM comments")
    video_count = cursor.fetchone()[0]
    print(f"収録動画数: {video_count}")
    
    # コメント数
    cursor.execute("SELECT COUNT(*) FROM comments")
    comment_count = cursor.fetchone()[0]
    print(f"総コメント数: {comment_count}")
    
    # 動画ごとのコメント数
    cursor.execute("""
        SELECT video_id, COUNT(*) as count 
        FROM comments 
        GROUP BY video_id
    """)
    for video_id, count in cursor.fetchall():
        print(f"  {video_id}: {count}コメント")
    
    conn.close()

if __name__ == '__main__':
    # 最新のファイルを探す
    samples_dir = 'out/samples'
    if not os.path.exists(samples_dir):
        print("サンプルディレクトリが見つかりません")
        sys.exit(1)
    
    csv_files = [f for f in os.listdir(samples_dir) if f.endswith('.csv')]
    db_files = [f for f in os.listdir(samples_dir) if f.endswith('.sqlite')]
    
    if csv_files:
        latest_csv = sorted(csv_files)[-1]
        analyze_csv(os.path.join(samples_dir, latest_csv))
    
    if db_files:
        latest_db = sorted(db_files)[-1]
        analyze_db(os.path.join(samples_dir, latest_db))