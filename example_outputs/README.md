# Example Outputs

このディレクトリには分析結果の例が含まれています。

## advanced_reports/

高度な分析レポートの出力例：

### ファイル一覧

1. **summary_14days.csv**
   - 14日間フィルタ適用後の要約統計
   - フレーム別（Gain/Loss）の各指標の比率

2. **engagement_metrics.csv**
   - エンゲージメント指標の詳細
   - いいね率、返信率、高エンゲージメント率

3. **loo_analysis.csv**
   - Leave-One-Out分析結果
   - 各動画を除外した場合の仮説検定結果

4. **tests_14days.csv**
   - 統計的仮説検定の詳細結果
   - H1: Loss→VP、H2: Gain→E_extの検定

5. **vp_by_engagement.csv**
   - エンゲージメントレベル別の投票宣言率
   - フレーム×エンゲージメントのクロス集計

6. **robustness_report.txt**
   - 頑健性分析の総合レポート
   - 各仮説の安定性評価

## 使用方法

これらのファイルは以下のコマンドで生成されます：

```bash
python -m yt_pilot advanced-report \
    --coded out/coded_full_simulation_dated.csv \
    --out out/advanced_reports \
    --days 14
```

## 注意事項

- これらは分析パイプラインの出力例です
- 実際のデータは各自で収集・分析してください
- シミュレーションデータに基づく結果です