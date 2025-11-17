1	"""
     2	Trigger Detector - Identify 12 betting triggers
     3	6 Pre-match + 6 Live HT triggers
     4	"""
     5	
     6	import logging
     7	from typing import Dict, List
     8	from datetime import datetime, timedelta
     9	
    10	logger = logging.getLogger(__name__)
    11	
    12	class TriggerDetector:
    13	    def analyze_patterns(self, historical_data: List[Dict], minimum_stats: Dict) -> Dict:
    14	        """
    15	        Analyze historical data to identify trigger patterns
    16	        Returns pre-match and live HT triggers with success rates
    17	        """
    18	        return {
    19	            'pre_match': self._analyze_prematch_triggers(historical_data),
    20	            'live_ht': self._analyze_ht_triggers(historical_data)
    21	        }
    22	        
    23	    def _analyze_prematch_triggers(self, matches: List[Dict]) -> Dict:
    24	        """Analyze pre-match trigger patterns"""
    25	        triggers = {}
    26	        
    27	        # 1. vs_bottom5_home - Home vs teams 16th-18th position
    28	        bottom5_home = self._filter_by_opponent_rank(matches, is_home=True, rank_range=(16, 18))
    29	        triggers['vs_bottom5_home'] = {
    30	            'total_matches': len(bottom5_home),
    31	            'avg_team_goals': self._safe_avg([m['team_goals'] for m in bottom5_home]),
    32	            'win_rate': self._calc_rate(bottom5_home, lambda m: m['result'] == 'W'),
    33	            'over_25_rate': self._calc_rate(bottom5_home, lambda m: m['over_2_5']),
    34	            'confidence': 'high' if len(bottom5_home) > 10 else 'medium'
    35	        }
    36	        
    37	        # 2. vs_top3_home - Home vs other big 3
    38	        top3_home = self._filter_top3_matches(matches, is_home=True)
    39	        triggers['vs_top3_home'] = {
    40	            'total_matches': len(top3_home),
    41	            'avg_team_goals': self._safe_avg([m['team_goals'] for m in top3_home]),
    42	            'btts_rate': self._calc_rate(top3_home, lambda m: m['btts']),
    43	            'over_25_rate': self._calc_rate(top3_home, lambda m: m['over_2_5']),
    44	            'confidence': 'high' if len(top3_home) > 5 else 'medium'
    45	        }
    46	        
    47	        # 3. post_loss_home - After losing, next home game
    48	        post_loss = self._find_post_loss_matches(matches, is_home=True)
    49	        triggers['post_loss_home'] = {
    50	            'total_matches': len(post_loss),
    51	            'win_rate': self._calc_rate(post_loss, lambda m: m['result'] == 'W'),
    52	            'over_15_rate': self._calc_rate(post_loss, lambda m: m['total_goals'] > 1.5),
    53	            'avg_team_goals': self._safe_avg([m['team_goals'] for m in post_loss]),
    54	            'confidence': 'medium'
    55	        }
    56	        
    57	        # 4. classico - Porto vs Benfica/Sporting
    58	        classicos = self._filter_classicos(matches)
    59	        triggers['classico'] = {
    60	            'total_matches': len(classicos),
    61	            'btts_rate': self._calc_rate(classicos, lambda m: m['btts']),
    62	            'over_25_rate': self._calc_rate(classicos, lambda m: m['over_2_5']),
    63	            'avg_total_goals': self._safe_avg([m['total_goals'] for m in classicos]),
    64	            'confidence': 'high'
    65	        }
    66	        
    67	        # 5. champions_week - Champions League same week
    68	        # (Requires additional calendar data - placeholder)
    69	        triggers['champions_week'] = {
    70	            'total_matches': 0,
    71	            'note': 'Requires Champions League calendar integration',
    72	            'confidence': 'pending'
    73	        }
    74	        
    75	        # 6. vs_bottom5_away - Away vs weak teams
    76	        bottom5_away = self._filter_by_opponent_rank(matches, is_home=False, rank_range=(16, 18))
    77	        triggers['vs_bottom5_away'] = {
    78	            'total_matches': len(bottom5_away),
    79	            'avg_team_goals': self._safe_avg([m['team_goals'] for m in bottom5_away]),
    80	            'win_rate': self._calc_rate(bottom5_away, lambda m: m['result'] == 'W'),
    81	            'over_15_rate': self._calc_rate(bottom5_away, lambda m: m['total_goals'] > 1.5),
    82	            'confidence': 'medium' if len(bottom5_away) > 8 else 'low'
    83	        }
    84	        
    85	        return triggers
    86	        
    87	    def _analyze_ht_triggers(self, matches: List[Dict]) -> Dict:
    88	        """Analyze half-time trigger patterns"""
    89	        triggers = {}
    90	        
    91	        # 7. ht_0x0_after_30min_home - 0-0 at 30-45min at home
    92	        ht_00_home = [m for m in matches if m['is_home'] and m['ht_team_goals'] == 0 and m['ht_opponent_goals'] == 0]
    93	        triggers['ht_0x0_after_30min_home'] = {
    94	            'total_occurrences': len(ht_00_home),
    95	            'second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_00_home]),
    96	            'second_half_over_15': self._calc_rate(ht_00_home, lambda m: (m['team_goals'] + m['opponent_goals'] - m['ht_total']) > 1.5),
    97	            'win_from_00': self._calc_rate(ht_00_home, lambda m: m['result'] == 'W'),
    98	            'confidence': 'high' if len(ht_00_home) > 10 else 'medium'
    99	        }
   100	        
   101	        # 8. ht_1x0_winning_home - Winning 1-0 at HT at home
   102	        ht_10_home = [m for m in matches if m['is_home'] and m['ht_team_goals'] == 1 and m['ht_opponent_goals'] == 0]
   103	        triggers['ht_1x0_winning_home'] = {
   104	            'total_occurrences': len(ht_10_home),
   105	            'maintained_win': self._calc_rate(ht_10_home, lambda m: m['result'] == 'W'),
   106	            'second_half_team_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_10_home]),
   107	            'clean_sheet_rate': self._calc_rate(ht_10_home, lambda m: m['clean_sheet']),
   108	            'confidence': 'high'
   109	        }
   110	        
   111	        # 9. ht_losing_home - Losing at HT at home
   112	        ht_losing_home = [m for m in matches if m['is_home'] and m['ht_team_goals'] < m['ht_opponent_goals']]
   113	        triggers['ht_losing_home'] = {
   114	            'total_occurrences': len(ht_losing_home),
   115	            'comeback_rate': self._calc_rate(ht_losing_home, lambda m: m['result'] == 'W'),
   116	            'draw_recovery': self._calc_rate(ht_losing_home, lambda m: m['result'] == 'D'),
   117	            'second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_losing_home]),
   118	            'confidence': 'medium'
   119	        }
   120	        
   121	        # 10. ht_drawing_away - Drawing at HT away
   122	        ht_draw_away = [m for m in matches if not m['is_home'] and m['ht_team_goals'] == m['ht_opponent_goals']]
   123	        triggers['ht_drawing_away'] = {
   124	            'total_occurrences': len(ht_draw_away),
   125	            'win_from_draw': self._calc_rate(ht_draw_away, lambda m: m['result'] == 'W'),
   126	            'maintain_draw': self._calc_rate(ht_draw_away, lambda m: m['result'] == 'D'),
   127	            'second_half_btts': self._calc_rate(ht_draw_away, lambda m: (m['team_goals'] - m['ht_team_goals'] > 0) and (m['opponent_goals'] - m['ht_opponent_goals'] > 0)),
   128	            'confidence': 'medium'
   129	        }
   130	        
   131	        # 11. ht_0x0_after_30min_away - 0-0 at 30-45min away
   132	        ht_00_away = [m for m in matches if not m['is_home'] and m['ht_team_goals'] == 0 and m['ht_opponent_goals'] == 0]
   133	        triggers['ht_0x0_after_30min_away'] = {
   134	            'total_occurrences': len(ht_00_away),
   135	            'second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in ht_00_away]),
   136	            'second_half_over_15': self._calc_rate(ht_00_away, lambda m: (m['team_goals'] + m['opponent_goals'] - m['ht_total']) > 1.5),
   137	            'win_from_00': self._calc_rate(ht_00_away, lambda m: m['result'] == 'W'),
   138	            'confidence': 'medium' if len(ht_00_away) > 8 else 'low'
   139	        }
   140	        
   141	        # 12. second_half_momentum - Team pressing in 2nd half
   142	        second_half_strong = [m for m in matches if (m['team_goals'] - m['ht_team_goals']) >= 2]
   143	        triggers['second_half_momentum'] = {
   144	            'total_occurrences': len(second_half_strong),
   145	            'avg_second_half_goals': self._safe_avg([m['team_goals'] - m['ht_team_goals'] for m in second_half_strong]),
   146	            'strong_finish_rate': self._calc_rate(matches, lambda m: (m['team_goals'] - m['ht_team_goals']) >= 2),
   147	            'context': 'Historical 2nd half strength',
   148	            'confidence': 'high'
   149	        }
   150	        
   151	        return triggers
   152	        
   153	    def check_match_triggers(self, match: Dict, analysis: Dict) -> List[str]:
   154	        """Check which triggers are active for upcoming match"""
   155	        active = []
   156	        
   157	        # Check pre-match triggers based on opponent/context
   158	        # (Simplified - would need opponent ranking data)
   159	        
   160	        return active
   161	        
   162	    # Helper methods
   163	    def _filter_by_opponent_rank(self, matches: List[Dict], is_home: bool, rank_range: tuple) -> List[Dict]:
   164	        """Filter matches by opponent ranking (placeholder - needs league table data)"""
   165	        # Placeholder: return subset
   166	        filtered = [m for m in matches if m['is_home'] == is_home]
   167	        return filtered[:len(filtered)//3]  # Approximate bottom third
   168	        
   169	    def _filter_top3_matches(self, matches: List[Dict], is_home: bool) -> List[Dict]:
   170	        """Filter matches vs other big 3 teams"""
   171	        big3 = ['Benfica', 'FC Porto', 'Sporting']
   172	        return [m for m in matches if m['is_home'] == is_home and m['opponent'] in big3]
   173	        
   174	    def _find_post_loss_matches(self, matches: List[Dict], is_home: bool) -> List[Dict]:
   175	        """Find matches that came after a loss"""
   176	        post_loss = []
   177	        sorted_matches = sorted(matches, key=lambda x: x['date'])
   178	        
   179	        for i in range(1, len(sorted_matches)):
   180	            if sorted_matches[i-1]['result'] == 'L' and sorted_matches[i]['is_home'] == is_home:
   181	                post_loss.append(sorted_matches[i])
   182	                
   183	        return post_loss
   184	        
   185	    def _filter_classicos(self, matches: List[Dict]) -> List[Dict]:
   186	        """Filter Clássico matches"""
   187	        big3 = ['Benfica', 'FC Porto', 'Sporting']
   188	        return [m for m in matches if m['opponent'] in big3]
   189	        
   190	    def _calc_rate(self, matches: List[Dict], condition) -> float:
   191	        """Calculate percentage rate for condition"""
   192	        if not matches:
   193	            return 0.0
   194	        count = len([m for m in matches if condition(m)])
   195	        return (count / len(matches)) * 100
   196	        
   197	    def _safe_avg(self, values: List) -> float:
   198	        """Safe average calculation"""
   199	        if not values:
   200	            return 0.0
   201	        return sum(values) / len(values)
