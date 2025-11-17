"""
Telegram Notifier - Send alerts and reports
"""

import logging
import os
import requests
from typing import Dict

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f'https://api.telegram.org/bot{self.bot_token}'
        
    def send_report(self, pdf_path: str):
        """Send PDF report via Telegram"""
        try:
            with open(pdf_path, 'rb') as pdf_file:
                response = requests.post(
                    f'{self.base_url}/sendDocument',
                    data={'chat_id': self.chat_id},
                    files={'document': pdf_file}
                )
                
            if response.status_code == 200:
                logger.info("PDF report sent to Telegram")
            else:
                logger.error(f"Failed to send PDF: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending PDF: {e}")
            
    def send_match_alert(self, team_name: str, match: Dict, trading_plan: Dict):
        """Send pre-match trading alert"""
        message = f"""
🎯 <b>TEAM SPECIALIST ALERT</b>

<b>{team_name}</b> vs {match['opponent']}
📅 {match['date']}
🏟 {'Home' if match['is_home'] else 'Away'}

<b>Active Triggers:</b>
{self._format_triggers(match.get('active_triggers', []))}

<b>Trading Plan:</b>
💰 Kelly Stake: {trading_plan['recommended_stake']}
📊 Confidence: {trading_plan['confidence_level']}
🎲 Primary: {trading_plan['primary_bet']['market']}

<b>Entry Phases:</b>
{self._format_phases(trading_plan['entry_phases'])}
        """
        
        self._send_message(message)
        
    def send_live_alert(self, team_name: str, match: Dict, live_plan: Dict):
        """Send live HT trigger alert"""
        message = f"""
🔴 <b>LIVE HT TRIGGER!</b>

<b>{team_name}</b> vs {match['opponent']}
⏱ {match['elapsed_time']}' - HT: {match['ht_score']}

<b>Trigger:</b> {live_plan.get('trigger', 'Unknown')}

<b>Live Recommendation:</b>
💰 Kelly Stake: {live_plan.get('kelly_stake', 'N/A')}
🎲 Bet: {live_plan.get('suggested_bet', 'N/A')}
📊 Probability: {live_plan.get('probability', 'N/A')}

⚡ ACT NOW - 2nd half starting!
        """
        
        self._send_message(message)
        
    def _send_message(self, text: str):
        """Send text message"""
        try:
            response = requests.post(
                f'{self.base_url}/sendMessage',
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'HTML'
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to send message: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    def _format_triggers(self, triggers: list) -> str:
        """Format triggers list"""
        if not triggers:
            return 'No specific triggers'
        return '\n'.join([f'• {t}' for t in triggers])
        
    def _format_phases(self, phases: list) -> str:
        """Format entry phases"""
        return '\n'.join([
            f"{p['phase']}: {p['stake']} @ {p['timing']}"
            for p in phases
        ])
