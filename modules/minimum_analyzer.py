1	"""
     2	Minimum Analyzer - Calculate MINIMUM values (NOT averages)
     3	70%, 80%, 90% confidence thresholds
     4	"""
     5	
     6	import logging
     7	import numpy as np
     8	from typing import Dict, List
     9	
    10	logger = logging.getLogger(__name__)
    11	
    12	class MinimumAnalyzer:
    13	    def calculate_minimums(self, historical_data: List[Dict]) -> Dict:
    14	        """
    15	        Calculate minimum values at 70%, 80%, 90% confidence
    16	        Example: 90% minimum = value guaranteed in 90% of cases
    17	        """
    18	        home_matches = [m for m in historical_data if m['is_home']]
    19	        away_matches = [m for m in historical_data if not m['is_home']]
    20	        
    21	        return {
    22	            'home': self._analyze_matches(home_matches, 'home'),
    23	            'away': self._analyze_matches(away_matches, 'away'),
    24	            'min_70': self._calculate_confidence_minimums(historical_data, 70),
    25	            'min_80': self._calculate_confidence_minimums(historical_data, 80),
    26	            'min_90': self._calculate_confidence_minimums(historical_data, 90)
    27	        }
    28	        
    29	    def _analyze_matches(self, matches: List[Dict], venue: str) -> Dict:
    30	        """Analyze matches for specific venue"""
    31	        if not matches:
    32	            return {}
    33	            
    34	        team_goals = [m['team_goals'] for m in matches]
    35	        opponent_goals = [m['opponent_goals'] for m in matches]
    36	        total_goals = [m['total_goals'] for m in matches]
    37	        ht_goals = [m['ht_total'] for m in matches]
    38	        
    39	        wins = len([m for m in matches if m['result'] == 'W'])
    40	        draws = len([m for m in matches if m['result'] == 'D'])
    41	        losses = len([m for m in matches if m['result'] == 'L'])
    42	        
    43	        clean_sheets = len([m for m in matches if m['clean_sheet']])
    44	        btts = len([m for m in matches if m['btts']])
    45	        over_25 = len([m for m in matches if m['over_2_5']])
    46	        
    47	        return {
    48	            'total_matches': len(matches),
    49	            'team_goals': {
    50	                'min': min(team_goals),
    51	                'max': max(team_goals),
    52	                'average': np.mean(team_goals),
    53	                'percentile_10': np.percentile(team_goals, 10),  # Minimum 90%
    54	                'percentile_20': np.percentile(team_goals, 20),  # Minimum 80%
    55	                'percentile_30': np.percentile(team_goals, 30)   # Minimum 70%
    56	            },
    57	            'opponent_goals': {
    58	                'min': min(opponent_goals),
    59	                'max': max(opponent_goals),
    60	                'average': np.mean(opponent_goals),
    61	                'percentile_10': np.percentile(opponent_goals, 10),
    62	                'percentile_20': np.percentile(opponent_goals, 20),
    63	                'percentile_30': np.percentile(opponent_goals, 30)
    64	            },
    65	            'total_goals': {
    66	                'min': min(total_goals),
    67	                'max': max(total_goals),
    68	                'average': np.mean(total_goals),
    69	                'percentile_10': np.percentile(total_goals, 10),
    70	                'percentile_20': np.percentile(total_goals, 20),
    71	                'percentile_30': np.percentile(total_goals, 30)
    72	            },
    73	            'ht_goals': {
    74	                'min': min(ht_goals),
    75	                'max': max(ht_goals),
    76	                'average': np.mean(ht_goals),
    77	                'percentile_10': np.percentile(ht_goals, 10),
    78	                'percentile_20': np.percentile(ht_goals, 20),
    79	                'percentile_30': np.percentile(ht_goals, 30)
    80	            },
    81	            'results': {
    82	                'wins': wins,
    83	                'draws': draws,
    84	                'losses': losses,
    85	                'win_rate': (wins / len(matches)) * 100,
    86	                'clean_sheet_rate': (clean_sheets / len(matches)) * 100,
    87	                'btts_rate': (btts / len(matches)) * 100,
    88	                'over_25_rate': (over_25 / len(matches)) * 100
    89	            }
    90	        }
    91	        
    92	    def _calculate_confidence_minimums(self, matches: List[Dict], confidence: int) -> Dict:
    93	        """
    94	        Calculate minimum values at specific confidence level
    95	        Example: 90% confidence = value guaranteed in 90% of historical cases
    96	        """
    97	        percentile = 100 - confidence  # 90% confidence = 10th percentile
    98	        
    99	        team_goals = [m['team_goals'] for m in matches]
   100	        total_goals = [m['total_goals'] for m in matches]
   101	        ht_goals = [m['ht_total'] for m in matches]
   102	        
   103	        return {
   104	            'confidence_level': f'{confidence}%',
   105	            'minimum_team_goals': np.percentile(team_goals, percentile),
   106	            'minimum_total_goals': np.percentile(total_goals, percentile),
   107	            'minimum_ht_goals': np.percentile(ht_goals, percentile),
   108	            'interpretation': f'Values guaranteed in {confidence}% of historical cases'
   109	        }
   110	        
   111	    def get_scenario_probability(self, matches: List[Dict], scenario: str) -> float:
   112	        """
   113	        Calculate probability of specific scenario
   114	        Returns minimum probability (conservative estimate)
   115	        """
   116	        if not matches:
   117	            return 0.0
   118	            
   119	        total = len(matches)
   120	        
   121	        scenario_map = {
   122	            'over_1.5': lambda m: m['total_goals'] > 1.5,
   123	            'over_2.5': lambda m: m['total_goals'] > 2.5,
   124	            'over_3.5': lambda m: m['total_goals'] > 3.5,
   125	            'btts': lambda m: m['btts'],
   126	            'clean_sheet': lambda m: m['clean_sheet'],
   127	            'team_over_1.5': lambda m: m['team_goals'] > 1.5,
   128	            'team_over_2.5': lambda m: m['team_goals'] > 2.5,
   129	            'ht_over_0.5': lambda m: m['ht_total'] > 0.5,
   130	            'ht_over_1.5': lambda m: m['ht_total'] > 1.5
   131	        }
   132	        
   133	        if scenario not in scenario_map:
   134	            return 0.0
   135	            
   136	        count = len([m for m in matches if scenario_map[scenario](m)])
   137	        return count / total
