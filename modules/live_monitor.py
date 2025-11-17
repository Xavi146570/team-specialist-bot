"""
Live Monitor - Track matches between 30-45 minutes for HT triggers
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class LiveMonitor:
    def check_halftime_triggers(self, match: Dict, analysis: Dict) -> List[str]:
        """
        Check for active HT triggers during live match
        Focuses on 30-45 minute window
        """
        elapsed = match.get('elapsed_time', 0)
        
        # Only process during HT window (30-45 min)
        if elapsed < 30 or elapsed > 45:
            return []
            
        triggers = []
        ht_patterns = analysis.get('half_time_patterns', {})
        ht_score = match.get('ht_score', {})
        is_home = match['is_home']
        
        team_score = ht_score.get('home', 0) if is_home else ht_score.get('away', 0)
        opponent_score = ht_score.get('away', 0) if is_home else ht_score.get('home', 0)
        
        # Check 0-0 trigger
        if team_score == 0 and opponent_score == 0:
            trigger_key = 'ht_0x0_after_30min_home' if is_home else 'ht_0x0_after_30min_away'
            if trigger_key in ht_patterns:
                pattern = ht_patterns[trigger_key]
                if pattern.get('total_occurrences', 0) > 5:  # Minimum sample size
                    triggers.append({
                        'type': trigger_key,
                        'confidence': pattern.get('confidence', 'medium'),
                        'historical_2h_goals': pattern.get('second_half_goals', 0),
                        'win_probability': pattern.get('win_from_00', 0),
                        'recommended_bet': 'Over 1.5 Goals 2nd Half'
                    })
                    
        # Check winning 1-0 trigger (home only)
        if is_home and team_score == 1 and opponent_score == 0:
            trigger_key = 'ht_1x0_winning_home'
            if trigger_key in ht_patterns:
                pattern = ht_patterns[trigger_key]
                triggers.append({
                    'type': trigger_key,
                    'confidence': pattern.get('confidence', 'high'),
                    'maintain_win_rate': pattern.get('maintained_win', 0),
                    'clean_sheet_probability': pattern.get('clean_sheet_rate', 0),
                    'recommended_bet': 'Home Win + Clean Sheet'
                })
                
        # Check losing at HT (home only)
        if is_home and team_score < opponent_score:
            trigger_key = 'ht_losing_home'
            if trigger_key in ht_patterns:
                pattern = ht_patterns[trigger_key]
                if pattern.get('comeback_rate', 0) > 30:  # At least 30% comeback rate
                    triggers.append({
                        'type': trigger_key,
                        'confidence': pattern.get('confidence', 'medium'),
                        'comeback_rate': pattern.get('comeback_rate', 0),
                        'second_half_goals': pattern.get('second_half_goals', 0),
                        'recommended_bet': 'Team to Score Next / Comeback'
                    })
                    
        # Check drawing at HT (away only)
        if not is_home and team_score == opponent_score:
            trigger_key = 'ht_drawing_away'
            if trigger_key in ht_patterns:
                pattern = ht_patterns[trigger_key]
                triggers.append({
                    'type': trigger_key,
                    'confidence': pattern.get('confidence', 'medium'),
                    'win_from_draw': pattern.get('win_from_draw', 0),
                    'second_half_btts': pattern.get('second_half_btts', 0),
                    'recommended_bet': 'BTTS 2nd Half'
                })
                
        # Log detected triggers
        if triggers:
            logger.info(f"🔴 LIVE HT TRIGGERS: {match['opponent']} - {len(triggers)} triggers active at {elapsed}min")
            
        return triggers
        
    def should_send_alert(self, triggers: List[str], last_alert_time: Dict) -> bool:
        """
        Prevent duplicate alerts
        Only send once per HT period
        """
        if not triggers:
            return False
            
        match_id = triggers[0].get('match_id', '')
        
        # Check if already alerted for this HT
        if match_id in last_alert_time:
            return False
            
        return True
