"""
Kelly Criterion Calculator - Stake sizing based on MINIMUM probabilities
f = (bp - q) / b
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class KellyCalculator:
    def __init__(self):
        self.max_kelly_fraction = 0.25  # Never bet more than 25% of bankroll
        
    def create_trading_plan(self, match: Dict, analysis: Dict, triggers: List[str]) -> Dict:
        """
        Create complete trading plan with Kelly stakes
        Based on MINIMUM probabilities (70%, 80%, 90%)
        """
        is_home = match['is_home']
        venue_stats = analysis['home_stats'] if is_home else analysis['away_stats']
        
        scenarios = {
            'min_70': self._calculate_scenarios(venue_stats, analysis['min_70_confidence'], 'conservative'),
            'min_80': self._calculate_scenarios(venue_stats, analysis['min_80_confidence'], 'moderate'),
            'min_90': self._calculate_scenarios(venue_stats, analysis['min_90_confidence'], 'aggressive')
        }
        
        # Select recommended scenario based on triggers
        confidence_level = self._select_confidence_level(triggers)
        recommended = scenarios[confidence_level]
        
        return {
            'match_id': match['match_id'],
            'confidence_level': confidence_level,
            'recommended_stake': recommended['kelly_stake'],
            'scenarios': scenarios,
            'primary_bet': recommended['primary_bet'],
            'backup_bets': recommended['backup_bets'],
            'entry_phases': self._create_entry_phases(recommended),
            'stop_loss': recommended['stop_loss'],
            'take_profit': recommended['take_profit']
        }
        
    def create_live_plan(self, match: Dict, analysis: Dict, ht_triggers: List[str]) -> Dict:
        """Create live trading plan for HT triggers"""
        ht_patterns = analysis.get('half_time_patterns', {})
        
        # Select pattern based on current HT situation
        pattern_key = self._detect_ht_pattern(match, ht_triggers)
        
        if pattern_key not in ht_patterns:
            return {'status': 'no_pattern_matched'}
            
        pattern = ht_patterns[pattern_key]
        
        # Calculate live Kelly stake
        live_odds = 2.0  # Placeholder - would come from live odds feed
        probability = pattern.get('second_half_over_15', 0) / 100
        
        kelly = self.calculate_kelly(probability, live_odds)
        
        return {
            'trigger': pattern_key,
            'kelly_stake': kelly,
            'suggested_bet': 'Over 1.5 Goals 2nd Half',
            'probability': f'{probability * 100:.1f}%',
            'odds_needed': live_odds,
            'max_stake': f'{kelly * 100:.2f}%',
            'timing': 'HT - 2nd half kickoff'
        }
        
    def calculate_kelly(self, probability: float, odds: float) -> float:
        """
        Kelly Criterion formula
        f = (bp - q) / b
        
        f = fraction of bankroll
        b = odds - 1
        p = probability of win
        q = probability of loss (1 - p)
        """
        if probability <= 0 or odds <= 1:
            return 0.0
            
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Never bet if Kelly is negative (no edge)
        if kelly <= 0:
            return 0.0
            
        # Cap at max fraction (risk management)
        kelly = min(kelly, self.max_kelly_fraction)
        
        return kelly
        
    def _calculate_scenarios(self, venue_stats: Dict, min_confidence: Dict, strategy: str) -> Dict:
        """Calculate betting scenarios for confidence level"""
        
        # Extract minimum values
        min_team_goals = min_confidence.get('minimum_team_goals', 1.5)
        min_total_goals = min_confidence.get('minimum_total_goals', 2.5)
        
        # Base probabilities (from historical minimums)
        prob_over_15 = 0.7 if strategy == 'conservative' else 0.8 if strategy == 'moderate' else 0.9
        prob_over_25 = 0.6 if strategy == 'conservative' else 0.7 if strategy == 'moderate' else 0.8
        
        # Placeholder odds (would come from bookmaker API)
        odds_over_15 = 1.5
        odds_over_25 = 2.0
        odds_btts = 1.8
        
        kelly_over_15 = self.calculate_kelly(prob_over_15, odds_over_15)
        kelly_over_25 = self.calculate_kelly(prob_over_25, odds_over_25)
        kelly_btts = self.calculate_kelly(0.65, odds_btts)
        
        return {
            'strategy': strategy,
            'primary_bet': {
                'market': 'Over 1.5 Goals',
                'probability': f'{prob_over_15 * 100:.0f}%',
                'odds': odds_over_15,
                'kelly_stake': f'{kelly_over_15 * 100:.2f}%',
                'minimum_guarantee': f'{min_team_goals:.1f} goals'
            },
            'backup_bets': [
                {
                    'market': 'Over 2.5 Goals',
                    'probability': f'{prob_over_25 * 100:.0f}%',
                    'odds': odds_over_25,
                    'kelly_stake': f'{kelly_over_25 * 100:.2f}%'
                },
                {
                    'market': 'BTTS',
                    'probability': '65%',
                    'odds': odds_btts,
                    'kelly_stake': f'{kelly_btts * 100:.2f}%'
                }
            ],
            'kelly_stake': max(kelly_over_15, kelly_over_25),
            'stop_loss': '50% of stake',
            'take_profit': '80% profit target'
        }
        
    def _create_entry_phases(self, scenario: Dict) -> List[Dict]:
        """Create phased entry strategy"""
        total_kelly = float(scenario['kelly_stake'].replace('%', ''))
        
        return [
            {
                'phase': 'Pre-match',
                'stake': f'{total_kelly * 0.4:.2f}%',
                'timing': '30 minutes before kickoff',
                'markets': ['Over 1.5 Goals']
            },
            {
                'phase': 'Live Entry 1',
                'stake': f'{total_kelly * 0.3:.2f}%',
                'timing': '15-20 minutes if 0-0',
                'markets': ['Over 1.5 Goals', 'Team to score']
            },
            {
                'phase': 'Live Entry 2',
                'stake': f'{total_kelly * 0.3:.2f}%',
                'timing': 'HT if triggers active',
                'markets': ['2nd Half Over 0.5', '2nd Half Over 1.5']
            }
        ]
        
    def _select_confidence_level(self, triggers: List[str]) -> str:
        """Select confidence level based on active triggers"""
        high_confidence_triggers = ['vs_bottom5_home', 'classico', 'post_loss_home']
        
        if any(t in triggers for t in high_confidence_triggers):
            return 'min_80'
        elif len(triggers) >= 2:
            return 'min_80'
        else:
            return 'min_70'
            
    def _detect_ht_pattern(self, match: Dict, ht_triggers: List[str]) -> str:
        """Detect which HT pattern is active"""
        ht_score = match.get('ht_score', {})
        
        if ht_score.get('home') == 0 and ht_score.get('away') == 0:
            return 'ht_0x0_after_30min_home' if match['is_home'] else 'ht_0x0_after_30min_away'
        elif match['is_home'] and ht_score.get('home', 0) > ht_score.get('away', 0):
            return 'ht_1x0_winning_home'
        elif match['is_home'] and ht_score.get('home', 0) < ht_score.get('away', 0):
            return 'ht_losing_home'
        else:
            return 'ht_drawing_away'
