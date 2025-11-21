"""
Data Collector - API-Football Integration
Fetches 5 years of historical data + upcoming fixtures + live matches
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.api_key = os.getenv('APIFOOTBALL_API_KEY')
        self.base_url = 'https://v3.football.api-sports.io'
        self.headers = {
            'x-apisports-key': self.api_key
        }
        
    def get_team_history(self, team_id: int, years: int = 5) -> List[Dict]:
        """
        Fetch complete match history for team
        Returns last 5 years of matches
        """
        all_matches = []
        current_year = datetime.now().year
        
        for year in range(current_year - years, current_year + 1):
            try:
                response = requests.get(
                    f'{self.base_url}/fixtures',
                    headers=self.headers,
                    params={
                        'team': team_id,
                        'season': year,
                        'status': 'FT'  # Only finished matches
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('response', [])
                    
                    for match in matches:
                        all_matches.append(self._parse_match(match, team_id))
                        
                    logger.info(f"Fetched {len(matches)} matches from {year}")
                    
            except Exception as e:
                logger.error(f"Error fetching {year} data: {e}")
                
        logger.info(f"Total matches collected: {len(all_matches)}")
        return all_matches
        
        def get_upcoming_fixtures(self, team_id: int, days: int = 7) -> List[Dict]:
        """Get upcoming fixtures in next N days"""
        try:
            today = datetime.now()
            end_date = today + timedelta(days=days)
            
            logger.info(f"🔍 Buscando jogos de {today.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')} para team_id={team_id}")
            logger.info(f"🔑 API Key presente: {'Sim' if self.api_key else 'NÃO!'}")
            logger.info(f"🔑 API Key (primeiros 10 chars): {self.api_key[:10] if self.api_key else 'VAZIA'}")
            
            params = {
                'team': team_id,
                'from': today.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'status': 'NS'  # Not started
            }
            
            logger.info(f"📋 Parâmetros da requisição: {params}")
            
            response = requests.get(
                f'{self.base_url}/fixtures',
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            logger.info(f"📡 Status da API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Log da resposta completa (primeiros 1000 chars)
                logger.info(f"📊 Response JSON (preview): {str(data)[:1000]}")
                
                fixtures = data.get('response', [])
                logger.info(f"✅ API retornou {len(fixtures)} jogos")
                
                if fixtures:
                    logger.info(f"🎯 Primeiro jogo: {fixtures[0]}")
                
                return [self._parse_fixture(f, team_id) for f in fixtures]
            else:
                logger.error(f"❌ Erro da API: Status {response.status_code}")
                logger.error(f"❌ Response: {response.text[:500]}")
                
        except Exception as e:
            logger.error(f"❌ Exceção ao buscar fixtures: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        return []

        
    def get_live_matches(self, team_id: int) -> List[Dict]:
        """Get currently live matches for team"""
        try:
            response = requests.get(
                f'{self.base_url}/fixtures',
                headers=self.headers,
                params={
                    'team': team_id,
                    'live': 'all'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                live = data.get('response', [])
                return [self._parse_live_match(m, team_id) for m in live]
                
        except Exception as e:
            logger.error(f"Error fetching live matches: {e}")
            
        return []
        
    def _parse_match(self, match_data: Dict, team_id: int) -> Dict:
        """Parse historical match data"""
        fixture = match_data['fixture']
        teams = match_data['teams']
        goals = match_data['goals']
        score = match_data['score']
        
        is_home = teams['home']['id'] == team_id
        opponent = teams['away']['name'] if is_home else teams['home']['name']
        
        team_goals = goals['home'] if is_home else goals['away']
        opponent_goals = goals['away'] if is_home else goals['home']
        
        # Handle None values for halftime scores
        ht_home = score.get('halftime', {}).get('home') if score.get('halftime') else None
        ht_away = score.get('halftime', {}).get('away') if score.get('halftime') else None
        
        # Default to 0 if halftime data is missing
        ht_team = (ht_home if is_home else ht_away) or 0
        ht_opponent = (ht_away if is_home else ht_home) or 0
        
        return {
            'match_id': fixture['id'],
            'date': fixture['date'],
            'competition': match_data['league']['name'],
            'is_home': is_home,
            'opponent': opponent,
            'team_goals': team_goals or 0,
            'opponent_goals': opponent_goals or 0,
            'total_goals': (team_goals or 0) + (opponent_goals or 0),
            'ht_team_goals': ht_team,
            'ht_opponent_goals': ht_opponent,
            'ht_total': ht_team + ht_opponent,
            'result': 'W' if (team_goals or 0) > (opponent_goals or 0) else ('D' if (team_goals or 0) == (opponent_goals or 0) else 'L'),
            'clean_sheet': (opponent_goals or 0) == 0,
            'btts': (team_goals or 0) > 0 and (opponent_goals or 0) > 0,
            'over_2_5': ((team_goals or 0) + (opponent_goals or 0)) > 2.5,
            'over_1_5_ht': (ht_team + ht_opponent) > 1.5
        }
        
    def _parse_fixture(self, fixture_data: Dict, team_id: int) -> Dict:
        """Parse upcoming fixture"""
        fixture = fixture_data['fixture']
        teams = fixture_data['teams']
        
        is_home = teams['home']['id'] == team_id
        opponent = teams['away']['name'] if is_home else teams['home']['name']
        
        return {
            'match_id': fixture['id'],
            'date': fixture['date'],
            'competition': fixture_data['league']['name'],
            'is_home': is_home,
            'opponent': opponent,
            'opponent_id': teams['away']['id'] if is_home else teams['home']['id'],
            'venue': fixture['venue']['name']
        }
        
    def _parse_live_match(self, match_data: Dict, team_id: int) -> Dict:
        """Parse live match data"""
        fixture = match_data['fixture']
        teams = match_data['teams']
        goals = match_data['goals']
        
        is_home = teams['home']['id'] == team_id
        
        return {
            'match_id': fixture['id'],
            'elapsed_time': fixture['status']['elapsed'],
            'is_home': is_home,
            'opponent': teams['away']['name'] if is_home else teams['home']['name'],
            'current_score': f"{goals['home']}-{goals['away']}",
            'ht_score': match_data['score']['halftime'],
            'team_score': goals['home'] if is_home else goals['away'],
            'opponent_score': goals['away'] if is_home else goals['home']
        }
