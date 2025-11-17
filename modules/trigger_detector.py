"""
Trigger Detector - Identify 12 betting triggers
6 Pre-match + 6 Live HT triggers
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TriggerDetector:
    def analyze_patterns(self, historical_data: List[Dict], minimum_stats: Dict) -> Dict:
        """
        Analyze historical data to identify trigger patterns
        Returns pre-match and live HT triggers with success rates
        """
        return {
            'pre_match': self._analyze_prematch_triggers(historical_data),
            'live_ht': self._analyze_ht_triggers(historical_data)
        }
        
    def _analyze_prematch_triggers(self, matches: List[Dict]) -> Dict:
        """Analyze pre-match trigger patterns"""
        triggers = {}
        
        # 1. vs_bottom5_home - Home vs teams 16th-18th position
        bottom5_home = self._filter_by_opponent_rank(matches, is_home=True, rank_range=(16, 18))
        triggers['vs_bottom5_home'] = {
            'total_matches': len(bottom5_home),
            'avg_team_goals': self._safe_avg([m['team_goals'] for m in bottom5_home]),
            'win_rate': self._calc_rate(bottom5_home, lambda m: m['result'] == 'W'),
            'over_25_rate': self._calc_rate(bottom5_home, lambda m: m['over_2_5']),
            'confidence': 'high' if len(bottom5_home) > 10 else 'medium'
        }
        
        # 2. vs_top3_home - Home vs other big 3
        top3_home = self._filter_top3_matches(matches, is_home=True)
        triggers['vs_top3_home'] = {
            'total_matches': len(top3_home),
            'avg_team_goals': self._safe_avg([m['team_goals'] for m in top3_home]),
            'btts_rate': self._calc_rate(top3_home, lambda m: m['btts']),
            'over_25_rate': self._calc_rate(top3_home, lambda m: m['over_2_5']),
            'confidence': 'high' if len(top3_home) > 5 else 'medium'
        }
        
        # 3. post_loss_home - After losing, next home game
        post_loss = self._find_post_loss_matches(matches, is_home=True)
        triggers['post_loss_home'] = {
            'total_matches': len(post_loss),
            'win_rate': self._calc_rate(post_loss, lambda m: m['result'] == 'W'),
            'over_15_rate': self._calc_rate(post_loss, lambda m: m['total_goals'] > 1.5),
            'avg_team_goals': self._safe_avg([m['team_goals'] for m in post_loss]),
            'confidence': 'medium'
        }
        
        # 4. classico - Porto vs Benfica/Sporting
        classicos = self._filter_classicos(matches)
        triggers['classico'] = {
            'total_matches': len(classicos),
            'btts_rate': self._calc_rate(classicos, lambda m: m['btts']),
            'over_25_rate': self._calc_rate(classicos, lambda m: m['over_2_5']),
            'avg_total_goals': self._safe_avg([m['total_goals'] for m in classicos]),
            'confidence': 'high'
        }
        
        # 5. champions_week - Champions League same week
        # (Requires additional calendar data - placeholder)
        triggers['champions_week'] = {
            'total_matches': 0,
            'note': 'Requires Champions League calendar integration',
            'confidence': 'pending'
        }
        
        # 6. vs_bottom5_away - Away vs weak teams
        bottom5_away = self._filter_by_opponent_rank(matches, is_home=False, rank_range=(16, 18))
        triggers['vs_bottom5_away'] = {
            'total_matches': len(bottom5_away),
            'avg_team_goals': self._safe_avg([m['team_goals'] for m in bottom5_away]),
            'win_rate': self._calc_rate(bottom5_away, lambda m: m['result'] == 'W'),
            'over_15_rate': self._calc_rate(bottom5_away, lambda m: m['total_goals'] > 1.5),
            'confidence': 'medium' if len(bottom5_away) > 8 else 'low'
        }
        
        return triggers
        
    def _analyze_ht_triggers(self, matches: List[Dict]) -> Dict:
        """Analyze half-time trigger patterns"""
        triggers = {}
        
        # 7. ht_0x0_after_30min_home - 0-0 at 30-45min at home
        ht_00_home = [m for m in matches if m['is_home'] and m['ht_team_goals'] == 0 and m['ht_opponent_goals'] == 0]
        triggers['ht_0x0_after_30min_home'] = {
            'total_occurrences': len(ht_00_home),
            'second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_00_home]),
            'second_half_over_15': self._calc_rate(ht_00_home, lambda m: (m['team_goals'] + m['opponent_goals'] - m['ht_total']) > 1.5),
            'win_from_00': self._calc_rate(ht_00_home, lambda m: m['result'] == 'W'),
            'confidence': 'high' if len(ht_00_home) > 10 else 'medium'
        }
        
        # 8. ht_1x0_winning_home - Winning 1-0 at HT at home
        ht_10_home = [m for m in matches if m['is_home'] and m['ht_team_goals'] == 1 and m['ht_opponent_goals'] == 0]
        triggers['ht_1x0_winning_home'] = {
            'total_occurrences': len(ht_10_home),
            'maintained_win': self._calc_rate(ht_10_home, lambda m: m['result'] == 'W'),
            'second_half_team_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_10_home]),
            'clean_sheet_rate': self._calc_rate(ht_10_home, lambda m: m['clean_sheet']),
            'confidence': 'high'
        }
        
        # 9. ht_losing_home - Losing at HT at home
        ht_losing_home = [m for m in matches if m['is_home'] and m['ht_team_goals'] < m['ht_opponent_goals']]
        triggers['ht_losing_home'] = {
            'total_occurrences': len(ht_losing_home),
            'comeback_rate': self._calc_rate(ht_losing_home, lambda m: m['result'] == 'W'),
            'draw_recovery': self._calc_rate(ht_losing_home, lambda m: m['result'] == 'D'),
            'second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_losing_home]),
            'confidence': 'medium'
        }
        
        # 10. ht_drawing_away - Drawing at HT away
        ht_draw_away = [m for m in matches if not m['is_home'] and m['ht_team_goals'] == m['ht_opponent_goals']]
        triggers['ht_drawing_away'] = {
            'total_occurrences': len(ht_draw_away),
            'win_from_draw': self._calc_rate(ht_draw_away, lambda m: m['result'] == 'W'),
            'maintain_draw': self._calc_rate(ht_draw_away, lambda m: m['result'] == 'D'),
            'second_half_btts': self._calc_rate(ht_draw_away, lambda m: (m['team_goals'] - m['ht_team_goals'] > 0) and (m['opponent_goals'] - m['ht_opponent_goals'] > 0)),
            'confidence': 'medium'
        }
        
        # 11. ht_0x0_after_30min_away - 0-0 at 30-45min away
        ht_00_away = [m for m in matches if not m['is_home'] and m['ht_team_goals'] == 0 and m['ht_opponent_goals'] == 0]
        triggers['ht_0x0_after_30min_away'] = {
            'total_occurrences': len(ht_00_away),
            'second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_00_away]),
            'second_half_over_15': self._calc_rate(ht_00_away, lambda m: (m['team_goals'] + m['opponent_goals'] - m['ht_total']) > 1.5),
            'win_from_00': self._calc_rate(ht_00_away, lambda m: m['result'] == 'W'),
            'confidence': 'medium' if len(ht_00_away) > 8 else 'low'
        }
        
        # 12. second_half_momentum - Team pressing in 2nd half
        second_half_strong = [m for m in matches if (m['team_goals'] - m['ht_team_goals']) >= 2]
        triggers['second_half_momentum'] = {
            'total_occurrences': len(second_half_strong),
            'avg_second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in second_half_strong]),
            'strong_finish_rate': self._calc_rate(matches, lambda m: (m['team_goals'] - m['ht_team_goals']) >= 2),
            'context': 'Historical 2nd half strength',
            'confidence': 'high'
        }
        
        return triggers
        
    def check_match_triggers(self, match: Dict, analysis: Dict) -> List[str]:
        """Check which triggers are active for upcoming match"""
        active = []
        
        # Check pre-match triggers based on opponent/context
        # (Simplified - would need opponent ranking data)
        
        return active
        
    # Helper methods
    def _filter_by_opponent_rank(self, matches: List[Dict], is_home: bool, rank_range: tuple) -> List[Dict]:
        """Filter matches by opponent ranking (placeholder - needs league table data)"""
        # Placeholder: return subset
        filtered = [m for m in matches if m['is_home'] == is_home]
        return filtered[:len(filtered)//3]  # Approximate bottom third
        
    def _filter_top3_matches(self, matches: List[Dict], is_home: bool) -> List[Dict]:
        """Filter matches vs other big 3 teams"""
        big3 = ['Benfica', 'FC Porto', 'Sporting']
        return [m for m in matches if m['is_home'] == is_home and m['opponent'] in big3]
        
    def _find_post_loss_matches(self, matches: List[Dict], is_home: bool) -> List[Dict]:
        """Find matches that came after a loss"""
        post_loss = []
        sorted_matches = sorted(matches, key=lambda x: x['date'])
        
        for i in range(1, len(sorted_matches)):
            if sorted_matches[i-1]['result'] == 'L' and sorted_matches[i]['is_home'] == is_home:
                post_loss.append(sorted_matches[i])
                
        return post_loss
        
    def _filter_classicos(self, matches: List[Dict]) -> List[Dict]:
        """Filter Clássico matches"""
        big3 = ['Benfica', 'FC Porto', 'Sporting']
        return [m for m in matches if m['opponent'] in big3]
        
    def _calc_rate(self, matches: List[Dict], condition) -> float:
        """Calculate percentage rate for condition"""
        if not matches:
            return 0.0
        count = len([m for m in matches if condition(m)])
        return (count / len(matches)) * 100
        
    def _safe_avg(self, values: List) -> float:
        """Safe average calculation"""
        if not values:
            return 0.0
        return sum(values) / len(values)
