"""
Minimum Analyzer - Calculate MINIMUM values (NOT averages)
70%, 80%, 90% confidence thresholds
"""

import logging
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)

class MinimumAnalyzer:
    def calculate_minimums(self, historical_data: List[Dict]) -> Dict:
        """
        Calculate minimum values at 70%, 80%, 90% confidence
        Example: 90% minimum = value guaranteed in 90% of cases
        """
        home_matches = [m for m in historical_data if m['is_home']]
        away_matches = [m for m in historical_data if not m['is_home']]
        
        return {
            'home': self._analyze_matches(home_matches, 'home'),
            'away': self._analyze_matches(away_matches, 'away'),
            'min_70': self._calculate_confidence_minimums(historical_data, 70),
            'min_80': self._calculate_confidence_minimums(historical_data, 80),
            'min_90': self._calculate_confidence_minimums(historical_data, 90)
        }
        
    def _analyze_matches(self, matches: List[Dict], venue: str) -> Dict:
        """Analyze matches for specific venue"""
        if not matches:
            return {}
            
        team_goals = [m['team_goals'] for m in matches]
        opponent_goals = [m['opponent_goals'] for m in matches]
        total_goals = [m['total_goals'] for m in matches]
        ht_goals = [m['ht_total'] for m in matches]
        
        wins = len([m for m in matches if m['result'] == 'W'])
        draws = len([m for m in matches if m['result'] == 'D'])
        losses = len([m for m in matches if m['result'] == 'L'])
        
        clean_sheets = len([m for m in matches if m['clean_sheet']])
        btts = len([m for m in matches if m['btts']])
        over_25 = len([m for m in matches if m['over_2_5']])
        
        return {
            'total_matches': len(matches),
            'team_goals': {
                'min': min(team_goals),
                'max': max(team_goals),
                'average': np.mean(team_goals),
                'percentile_10': np.percentile(team_goals, 10),  # Minimum 90%
                'percentile_20': np.percentile(team_goals, 20),  # Minimum 80%
                'percentile_30': np.percentile(team_goals, 30)   # Minimum 70%
            },
            'opponent_goals': {
                'min': min(opponent_goals),
                'max': max(opponent_goals),
                'average': np.mean(opponent_goals),
                'percentile_10': np.percentile(opponent_goals, 10),
                'percentile_20': np.percentile(opponent_goals, 20),
                'percentile_30': np.percentile(opponent_goals, 30)
            },
            'total_goals': {
                'min': min(total_goals),
                'max': max(total_goals),
                'average': np.mean(total_goals),
                'percentile_10': np.percentile(total_goals, 10),
                'percentile_20': np.percentile(total_goals, 20),
                'percentile_30': np.percentile(total_goals, 30)
            },
            'ht_goals': {
                'min': min(ht_goals),
                'max': max(ht_goals),
                'average': np.mean(ht_goals),
                'percentile_10': np.percentile(ht_goals, 10),
                'percentile_20': np.percentile(ht_goals, 20),
                'percentile_30': np.percentile(ht_goals, 30)
            },
            'results': {
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': (wins / len(matches)) * 100,
                'clean_sheet_rate': (clean_sheets / len(matches)) * 100,
                'btts_rate': (btts / len(matches)) * 100,
                'over_25_rate': (over_25 / len(matches)) * 100
            }
        }
        
    def _calculate_confidence_minimums(self, matches: List[Dict], confidence: int) -> Dict:
        """
        Calculate minimum values at specific confidence level
        Example: 90% confidence = value guaranteed in 90% of historical cases
        """
        percentile = 100 - confidence  # 90% confidence = 10th percentile
        
        team_goals = [m['team_goals'] for m in matches]
        total_goals = [m['total_goals'] for m in matches]
        ht_goals = [m['ht_total'] for m in matches]
        
        return {
            'confidence_level': f'{confidence}%',
            'minimum_team_goals': np.percentile(team_goals, percentile),
            'minimum_total_goals': np.percentile(total_goals, percentile),
            'minimum_ht_goals': np.percentile(ht_goals, percentile),
            'interpretation': f'Values guaranteed in {confidence}% of historical cases'
        }
        
    def get_scenario_probability(self, matches: List[Dict], scenario: str) -> float:
        """
        Calculate probability of specific scenario
        Returns minimum probability (conservative estimate)
        """
        if not matches:
            return 0.0
            
        total = len(matches)
        
        scenario_map = {
            'over_1.5': lambda m: m['total_goals'] > 1.5,
            'over_2.5': lambda m: m['total_goals'] > 2.5,
            'over_3.5': lambda m: m['total_goals'] > 3.5,
            'btts': lambda m: m['btts'],
            'clean_sheet': lambda m: m['clean_sheet'],
            'team_over_1.5': lambda m: m['team_goals'] > 1.5,
            'team_over_2.5': lambda m: m['team_goals'] > 2.5,
            'ht_over_0.5': lambda m: m['ht_total'] > 0.5,
            'ht_over_1.5': lambda m: m['ht_total'] > 1.5
        }
        
        if scenario not in scenario_map:
            return 0.0
            
        count = len([m for m in matches if scenario_map[scenario](m)])
        return count / total
