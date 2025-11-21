"""
Team Specialist Bot - Trigger Detection Module
Detects specific game patterns/triggers based on historical analysis
"""

from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TriggerDetector:
    """Analyzes matches and detects triggers based on historical patterns"""
    
    def __init__(self, data_collector):
        self.data_collector = data_collector
        
        # Portuguese League Team IDs for classics detection
        self.BENFICA_ID = 211
        self.PORTO_ID = 212
        self.SPORTING_ID = 228
        self.BIG3_IDS = {self.BENFICA_ID, self.PORTO_ID, self.SPORTING_ID}
        
        # Competition IDs
        self.PRIMEIRA_LIGA_ID = 94
        self.TACA_PORTUGAL_ID = 96
        self.CHAMPIONS_LEAGUE_ID = 2
        self.EUROPA_LEAGUE_ID = 3
        
    def analyze_patterns(self, team_id: int, matches: List[Dict]) -> Dict:
        """
        Analyze historical match patterns for a team
        Returns percentile analysis and special triggers
        """
        if not matches:
            return {}
            
        logger.info(f"🔍 Analyzing {len(matches)} matches for team {team_id}")
        
        # Separate home and away matches
        home_matches = [m for m in matches if m['teams']['home']['id'] == team_id]
        away_matches = [m for m in matches if m['teams']['away']['id'] == team_id]
        
        analysis = {
            'team_id': team_id,
            'total_matches': len(matches),
            'home_matches': len(home_matches),
            'away_matches': len(away_matches),
            'home_stats': self._calculate_percentiles(home_matches, team_id, is_home=True),
            'away_stats': self._calculate_percentiles(away_matches, team_id, is_home=False),
            'special_triggers': self._detect_special_patterns(matches, team_id)
        }
        
        logger.info(f"✅ Analysis complete - {analysis['special_triggers']['total_triggers']} triggers found")
        
        return analysis
    
    def _calculate_percentiles(self, matches: List[Dict], team_id: int, is_home: bool) -> Dict:
        """Calculate P10/P20/P30 for goals scored/conceded and corners"""
        if not matches:
            return {}
            
        goals_scored = []
        goals_conceded = []
        corners_for = []
        corners_against = []
        
        for match in matches:
            if not match.get('goals') or not match.get('statistics'):
                continue
                
            home_team = match['teams']['home']
            away_team = match['teams']['away']
            
            # Get goals
            home_goals = match['goals']['home'] or 0
            away_goals = match['goals']['away'] or 0
            
            if is_home:
                goals_scored.append(home_goals)
                goals_conceded.append(away_goals)
            else:
                goals_scored.append(away_goals)
                goals_conceded.append(home_goals)
            
            # Get corners from statistics
            stats = match['statistics']
            home_corners = self._extract_stat(stats, 'home', 'Corner Kicks')
            away_corners = self._extract_stat(stats, 'away', 'Corner Kicks')
            
            if home_corners is not None and away_corners is not None:
                if is_home:
                    corners_for.append(home_corners)
                    corners_against.append(away_corners)
                else:
                    corners_for.append(away_corners)
                    corners_against.append(home_corners)
        
        def calc_percentile(data: List[float], p: int) -> float:
            if not data:
                return 0
            sorted_data = sorted(data)
            index = int(len(sorted_data) * (p / 100))
            return sorted_data[min(index, len(sorted_data) - 1)]
        
        return {
            'goals_scored': {
                'p10': calc_percentile(goals_scored, 10),
                'p20': calc_percentile(goals_scored, 20),
                'p30': calc_percentile(goals_scored, 30)
            },
            'goals_conceded': {
                'p10': calc_percentile(goals_conceded, 10),
                'p20': calc_percentile(goals_conceded, 20),
                'p30': calc_percentile(goals_conceded, 30)
            },
            'corners_for': {
                'p10': calc_percentile(corners_for, 10),
                'p20': calc_percentile(corners_for, 20),
                'p30': calc_percentile(corners_for, 30)
            },
            'corners_against': {
                'p10': calc_percentile(corners_against, 10),
                'p20': calc_percentile(corners_against, 20),
                'p30': calc_percentile(corners_against, 30)
            },
            'sample_size': len(goals_scored)
        }
    
    def _extract_stat(self, statistics: List[Dict], team_type: str, stat_name: str) -> int:
        """Extract a specific statistic from match statistics"""
        try:
            for stat_group in statistics:
                if stat_group['team']['name'].lower() == team_type:
                    for stat in stat_group['statistics']:
                        if stat['type'] == stat_name:
                            value = stat['value']
                            return int(value) if value is not None else 0
        except:
            pass
        return None
    
    def _detect_special_patterns(self, matches: List[Dict], team_id: int) -> Dict:
        """Detect special patterns/triggers in historical data"""
        triggers = {
            'vs_bottom5_home': 0,
            'vs_top3_home': 0,
            'post_loss_home': 0,
            'classico': 0,
            'champions_week': 0,
            'vs_bottom5_away': 0,
            'ht_0x0_after_30min_home': 0,
            'ht_1x0_winning_home': 0,
            'ht_losing_home': 0,
            'ht_drawing_away': 0,
            'ht_0x0_after_30min_away': 0,
            'second_half_momentum': 0
        }
        
        # Sort matches chronologically
        sorted_matches = sorted(matches, key=lambda x: x['fixture']['date'])
        
        for i, match in enumerate(sorted_matches):
            is_home = match['teams']['home']['id'] == team_id
            opponent_id = match['teams']['away']['id'] if is_home else match['teams']['home']['id']
            
            # Pre-match triggers
            if is_home:
                # Classico detection
                if opponent_id in self.BIG3_IDS:
                    triggers['classico'] += 1
                
                # Post loss detection
                if i > 0:
                    prev_match = sorted_matches[i-1]
                    if self._is_loss(prev_match, team_id):
                        triggers['post_loss_home'] += 1
            
            # Half-time triggers (would need half-time data)
            # Simplified - based on final score patterns
            if match.get('goals'):
                home_goals = match['goals']['home'] or 0
                away_goals = match['goals']['away'] or 0
                
                if is_home and home_goals == 0 and away_goals == 0:
                    triggers['ht_0x0_after_30min_home'] += 1
                elif is_home and home_goals > away_goals:
                    triggers['ht_1x0_winning_home'] += 1
                elif is_home and home_goals < away_goals:
                    triggers['ht_losing_home'] += 1
                elif not is_home and home_goals == away_goals:
                    triggers['ht_drawing_away'] += 1
        
        triggers['total_triggers'] = sum(triggers.values())
        
        return triggers
    
    def _is_loss(self, match: Dict, team_id: int) -> bool:
        """Check if match was a loss for the team"""
        if not match.get('goals'):
            return False
            
        home_goals = match['goals']['home'] or 0
        away_goals = match['goals']['away'] or 0
        
        is_home = match['teams']['home']['id'] == team_id
        
        if is_home:
            return home_goals < away_goals
        else:
            return away_goals < home_goals
    
    def check_match_triggers(self, match: Dict, analysis: Dict) -> List[str]:
        """
        Check which triggers are active for upcoming match
        
        Args:
            match: Match data from API
            analysis: Historical analysis for the team
            
        Returns:
            List of active trigger names
        """
        active = []
        
        # Extract match details
        team_id = None
        opponent_id = None
        is_home = False
        match_date = datetime.fromisoformat(match['fixture']['date'].replace('Z', '+00:00'))
        league_id = match['league']['id']
        
        # Determine if our team is home or away
        home_id = match['teams']['home']['id']
        away_id = match['teams']['away']['id']
        
        if home_id in self.BIG3_IDS:
            team_id = home_id
            opponent_id = away_id
            is_home = True
        elif away_id in self.BIG3_IDS:
            team_id = away_id
            opponent_id = home_id
            is_home = False
        else:
            logger.warning(f"⚠️ Match doesn't involve Big 3: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
            return active
        
        logger.info(f"🔍 Checking triggers for: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
        logger.info(f"📍 Team {team_id} is {'HOME' if is_home else 'AWAY'} vs opponent {opponent_id}")
        
        # TRIGGER 1-2: vs_bottom5_home / vs_top3_home
        # Heuristic: If opponent is NOT in Big 3 and league is Taça → assume "bottom 5"
        if is_home:
            if opponent_id not in self.BIG3_IDS:
                if league_id == self.TACA_PORTUGAL_ID:
                    active.append('vs_bottom5_home')
                    logger.info("✅ Trigger: vs_bottom5_home (Taça opponent)")
                elif league_id in [self.CHAMPIONS_LEAGUE_ID, self.EUROPA_LEAGUE_ID]:
                    active.append('vs_top3_home')
                    logger.info("✅ Trigger: vs_top3_home (European competition)")
        
        # TRIGGER 3: post_loss_home
        # Check last match result
        if is_home:
            try:
                # Get recent match from history
recent_matches = self.data_collector.get_team_history(
    team_id=team_id,
    years=1
)
if recent_matches:
    recent_matches = [recent_matches[0]]  # Get only the most recent

                if recent_matches and self._is_loss(recent_matches[0], team_id):
                    active.append('post_loss_home')
                    logger.info("✅ Trigger: post_loss_home (coming from defeat)")
            except Exception as e:
                logger.warning(f"⚠️ Could not check post_loss: {e}")
        
        # TRIGGER 4: classico
        if opponent_id in self.BIG3_IDS:
            active.append('classico')
            logger.info("✅ Trigger: classico (Big 3 derby)")
        
        # TRIGGER 5: champions_week
        # Check if there's a Champions/Europa League match within 3 days
        try:
            start_date = (match_date - timedelta(days=3)).strftime('%Y-%m-%d')
            end_date = (match_date + timedelta(days=3)).strftime('%Y-%m-%d')
            
            # Get upcoming fixtures to check for nearby European matches
nearby_matches = self.data_collector.get_upcoming_fixtures(
    team_id=team_id,
    days=7
)
# Need to convert to full match details
nearby_full = []
for nm in nearby_matches[:5]:  # Check up to 5 upcoming matches
    full = self._get_match_details_simple(nm['id'])
    if full:
        nearby_full.append(full)
nearby_matches = nearby_full

            
            for nearby in nearby_matches:
                nearby_date = datetime.fromisoformat(nearby['fixture']['date'].replace('Z', '+00:00'))
                nearby_league = nearby['league']['id']
                
                # Check if it's a different match in Champions/Europa League
                if nearby['fixture']['id'] != match['fixture']['id']:
                    if nearby_league in [self.CHAMPIONS_LEAGUE_ID, self.EUROPA_LEAGUE_ID]:
                        days_diff = abs((nearby_date - match_date).days)
                        if days_diff <= 3:
                            active.append('champions_week')
                            logger.info(f"✅ Trigger: champions_week ({days_diff} days from European match)")
                            break
        except Exception as e:
            logger.warning(f"⚠️ Could not check champions_week: {e}")
        
        # TRIGGER 6: vs_bottom5_away
        if not is_home:
            if opponent_id not in self.BIG3_IDS:
                if league_id == self.TACA_PORTUGAL_ID:
                    active.append('vs_bottom5_away')
                    logger.info("✅ Trigger: vs_bottom5_away (Taça opponent)")
        
        # TRIGGERS 7-12: In-play triggers (ao intervalo)
        # Cannot be detected pre-match - would need live data
        # We skip these for pre-match analysis
        
        logger.info(f"📊 Total active triggers: {len(active)} - {active}")
        
        return active
    
    def calculate_trigger_score(self, active_triggers: List[str], analysis: Dict) -> int:
        """
        Calculate confidence score based on active triggers
        
        Score system:
        - Each trigger: +10 points
        - Classico: +20 points (double weight)
        - Champions week: +15 points (extra weight)
        
        Returns: Score 0-100
        """
        score = 0
        
        for trigger in active_triggers:
            if trigger == 'classico':
                score += 20
            elif trigger == 'champions_week':
                score += 15
            else:
                score += 10
        
        # Cap at 100
        return min(score, 100)
