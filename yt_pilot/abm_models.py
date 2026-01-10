"""Agent-Based Models for YouTube comment behavior prediction"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random
from enum import Enum
import mesa
import networkx as nx


class PoliticalOrientation(Enum):
    """政治的志向性"""
    ENGAGED = "engaged"       # 政治参加に積極的
    CYNICAL = "cynical"       # シニカル
    UNDECIDED = "undecided"   # 未決定
    

@dataclass
class CommentBehavior:
    """コメント行動の予測結果"""
    will_vote: float          # 投票する確率
    will_comment: float       # コメントする確率
    sentiment: str           # positive/negative/neutral
    engagement_level: float  # 0-1のエンゲージメントレベル


class CitizenAgent(mesa.Agent):
    """市民エージェント：コメント行動をモデル化"""
    
    def __init__(self, unique_id: int, model: 'CommentDiffusionModel',
                 initial_orientation: PoliticalOrientation = PoliticalOrientation.UNDECIDED):
        super().__init__(unique_id, model)
        
        # エージェントの属性
        self.orientation = initial_orientation
        self.voting_intention = 0.5  # 0-1の投票意向
        self.external_efficacy = random.uniform(0.2, 0.8)  # 外的効力感
        self.internal_efficacy = random.uniform(0.2, 0.8)  # 内的効力感
        self.cynicism = random.uniform(0.1, 0.6)  # シニシズムレベル
        
        # ネットワーク影響
        self.influence_susceptibility = random.uniform(0.3, 0.7)
        self.influenced_by_frame = None  # Loss/Gain
        
        # 行動履歴
        self.commented = False
        self.comment_sentiment = None
        self.influenced_others = 0
        
    def step(self):
        """各ステップでの行動決定"""
        # 1. 近隣エージェントからの影響を受ける
        self._receive_influence()
        
        # 2. コメント行動を決定
        if not self.commented and self._decide_to_comment():
            self._post_comment()
            
        # 3. 投票意向を更新
        self._update_voting_intention()
        
    def _receive_influence(self):
        """近隣エージェントからの影響を計算"""
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False
        )
        
        if not neighbors:
            return
            
        # 近隣の平均的な投票意向を計算
        avg_voting_intention = sum(n.voting_intention for n in neighbors) / len(neighbors)
        
        # 影響を受けて自分の意向を更新
        influence = (avg_voting_intention - self.voting_intention) * self.influence_susceptibility
        self.voting_intention = max(0, min(1, self.voting_intention + influence * 0.1))
        
    def _decide_to_comment(self) -> bool:
        """コメントするかどうかの決定"""
        # エンゲージメントレベルに基づく
        engagement = (self.external_efficacy + self.internal_efficacy) / 2
        
        # シニシズムが高いと否定的コメントの確率上昇
        if self.cynicism > 0.5:
            comment_prob = self.cynicism * 0.8
        else:
            comment_prob = engagement * 0.6
            
        return random.random() < comment_prob
        
    def _post_comment(self):
        """コメントを投稿"""
        self.commented = True
        
        # センチメントを決定
        if self.cynicism > 0.6:
            self.comment_sentiment = "negative"
        elif self.voting_intention > 0.7:
            self.comment_sentiment = "positive" 
        else:
            self.comment_sentiment = "neutral"
            
        # 周囲への影響力を記録
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False
        )
        self.influenced_others = len(neighbors)
        
    def _update_voting_intention(self):
        """投票意向の更新"""
        # フレーミング効果
        if self.influenced_by_frame == "Loss":
            # Loss frameは投票意向を高める
            self.voting_intention *= 1.05
        elif self.influenced_by_frame == "Gain":
            # Gain frameは効力感を高める
            self.external_efficacy *= 1.05
            
        # 境界値の調整
        self.voting_intention = max(0, min(1, self.voting_intention))
        self.external_efficacy = max(0, min(1, self.external_efficacy))


class CommentDiffusionModel(mesa.Model):
    """コメント拡散ABMモデル"""
    
    def __init__(self, n_agents: int = 100, width: int = 10, height: int = 10,
                 video_frame: str = "Neutral"):
        super().__init__()
        self.num_agents = n_agents
        self.video_frame = video_frame  # Loss/Gain/Neutral
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        
        # データコレクター
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Voting_Intention": self._get_avg_voting_intention,
                "Comments_Posted": self._get_comment_count,
                "Positive_Comments": self._get_positive_comments,
                "Negative_Comments": self._get_negative_comments
            },
            agent_reporters={
                "Voting_Intention": "voting_intention",
                "Cynicism": "cynicism",
                "Commented": "commented"
            }
        )
        
        # エージェントの初期化
        self._create_agents()
        
    def _create_agents(self):
        """エージェントを作成して配置"""
        for i in range(self.num_agents):
            # 初期の政治的志向性をランダムに設定
            orientation = random.choice(list(PoliticalOrientation))
            agent = CitizenAgent(i, self, orientation)
            
            # フレーミングの影響を設定
            agent.influenced_by_frame = self.video_frame
            
            # グリッド上にランダム配置
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
            
    def step(self):
        """モデルの1ステップ実行"""
        self.datacollector.collect(self)
        self.schedule.step()
        
    def _get_avg_voting_intention(self) -> float:
        """平均投票意向"""
        agents = [a for a in self.schedule.agents]
        if not agents:
            return 0
        return sum(a.voting_intention for a in agents) / len(agents)
        
    def _get_comment_count(self) -> int:
        """コメント投稿数"""
        return sum(1 for a in self.schedule.agents if a.commented)
        
    def _get_positive_comments(self) -> int:
        """ポジティブコメント数"""
        return sum(1 for a in self.schedule.agents 
                  if a.commented and a.comment_sentiment == "positive")
                  
    def _get_negative_comments(self) -> int:
        """ネガティブコメント数"""
        return sum(1 for a in self.schedule.agents 
                  if a.commented and a.comment_sentiment == "negative")


class CommentPredictor:
    """コメントデータから行動を予測"""
    
    def __init__(self, historical_data: Optional[Dict] = None):
        self.historical_data = historical_data or {}
        
    def predict_from_comment(self, comment_text: str, 
                           comment_features: Dict) -> CommentBehavior:
        """単一コメントから行動を予測"""
        # 簡単な実装例
        # 実際にはNLP + 機械学習モデルを使用
        
        # キーワードベースの簡易判定
        voting_keywords = ["投票", "選挙", "行く", "行こう"]
        cynical_keywords = ["意味ない", "無駄", "変わらない"]
        
        will_vote = 0.5  # ベースライン
        
        # キーワードで調整
        for keyword in voting_keywords:
            if keyword in comment_text:
                will_vote += 0.1
                
        for keyword in cynical_keywords:
            if keyword in comment_text:
                will_vote -= 0.2
                
        # エンゲージメントレベル
        engagement = min(1.0, (comment_features.get('like_count', 0) + 
                              comment_features.get('reply_count', 0) * 2) / 10)
        
        # センチメント（簡易版）
        if any(kw in comment_text for kw in cynical_keywords):
            sentiment = "negative"
        elif any(kw in comment_text for kw in voting_keywords):
            sentiment = "positive"
        else:
            sentiment = "neutral"
            
        return CommentBehavior(
            will_vote=max(0, min(1, will_vote)),
            will_comment=0.3 if sentiment == "positive" else 0.1,
            sentiment=sentiment,
            engagement_level=engagement
        )
        
    def predict_network_effect(self, agent_comments: List[Tuple[str, Dict]],
                              network: nx.Graph) -> Dict[int, float]:
        """ネットワーク効果を含めた予測"""
        # コメントネットワークでの影響伝播をモデル化
        influence_scores = {}
        
        for node in network.nodes():
            # 隣接ノードの影響を計算
            neighbors = list(network.neighbors(node))
            if not neighbors:
                influence_scores[node] = 0.5
                continue
                
            # 簡易的な影響スコア計算
            neighbor_sentiments = []
            for n in neighbors:
                if n < len(agent_comments):
                    comment, features = agent_comments[n]
                    behavior = self.predict_from_comment(comment, features)
                    neighbor_sentiments.append(behavior.will_vote)
                    
            if neighbor_sentiments:
                influence_scores[node] = sum(neighbor_sentiments) / len(neighbor_sentiments)
            else:
                influence_scores[node] = 0.5
                
        return influence_scores


# 使用例
if __name__ == "__main__":
    # ABMシミュレーション実行
    model = CommentDiffusionModel(n_agents=100, video_frame="Loss")
    
    for i in range(20):
        model.step()
        
    # 結果の取得
    model_data = model.datacollector.get_model_vars_dataframe()
    print("Average voting intention over time:")
    print(model_data["Voting_Intention"])
    
    # 個別コメント予測
    predictor = CommentPredictor()
    behavior = predictor.predict_from_comment(
        "明日投票に行きます！みんなで政治を変えよう",
        {"like_count": 10, "reply_count": 3}
    )
    print(f"\nPredicted behavior: {behavior}")