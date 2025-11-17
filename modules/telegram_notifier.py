1	"""
     2	Telegram Notifier - Send alerts and reports
     3	"""
     4	
     5	import logging
     6	import os
     7	import requests
     8	from typing import Dict
     9	
    10	logger = logging.getLogger(__name__)
    11	
    12	class TelegramNotifier:
    13	    def __init__(self):
    14	        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    15	        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
    16	        self.base_url = f'https://api.telegram.org/bot{self.bot_token}'
    17	        
    18	    def send_report(self, pdf_path: str):
    19	        """Send PDF report via Telegram"""
    20	        try:
    21	            with open(pdf_path, 'rb') as pdf_file:
    22	                response = requests.post(
    23	                    f'{self.base_url}/sendDocument',
    24	                    data={'chat_id': self.chat_id},
    25	                    files={'document': pdf_file}
    26	                )
    27	                
    28	            if response.status_code == 200:
    29	                logger.info("PDF report sent to Telegram")
    30	            else:
    31	                logger.error(f"Failed to send PDF: {response.text}")
    32	                
    33	        except Exception as e:
    34	            logger.error(f"Error sending PDF: {e}")
    35	            
    36	    def send_match_alert(self, team_name: str, match: Dict, trading_plan: Dict):
    37	        """Send pre-match trading alert"""
    38	        message = f"""
    39	🎯 <b>TEAM SPECIALIST ALERT</b>
    40	
    41	<b>{team_name}</b> vs {match['opponent']}
    42	📅 {match['date']}
    43	🏟 {'Home' if match['is_home'] else 'Away'}
    44	
    45	<b>Active Triggers:</b>
    46	{self._format_triggers(match.get('active_triggers', []))}
    47	
    48	<b>Trading Plan:</b>
    49	💰 Kelly Stake: {trading_plan['recommended_stake']}
    50	📊 Confidence: {trading_plan['confidence_level']}
    51	🎲 Primary: {trading_plan['primary_bet']['market']}
    52	
    53	<b>Entry Phases:</b>
    54	{self._format_phases(trading_plan['entry_phases'])}
    55	        """
    56	        
    57	        self._send_message(message)
    58	        
    59	    def send_live_alert(self, team_name: str, match: Dict, live_plan: Dict):
    60	        """Send live HT trigger alert"""
    61	        message = f"""
    62	🔴 <b>LIVE HT TRIGGER!</b>
    63	
    64	<b>{team_name}</b> vs {match['opponent']}
    65	⏱ {match['elapsed_time']}' - HT: {match['ht_score']}
    66	
    67	<b>Trigger:</b> {live_plan.get('trigger', 'Unknown')}
    68	
    69	<b>Live Recommendation:</b>
    70	💰 Kelly Stake: {live_plan.get('kelly_stake', 'N/A')}
    71	🎲 Bet: {live_plan.get('suggested_bet', 'N/A')}
    72	📊 Probability: {live_plan.get('probability', 'N/A')}
    73	
    74	⚡ ACT NOW - 2nd half starting!
    75	        """
    76	        
    77	        self._send_message(message)
    78	        
    79	    def _send_message(self, text: str):
    80	        """Send text message"""
    81	        try:
    82	            response = requests.post(
    83	                f'{self.base_url}/sendMessage',
    84	                json={
    85	                    'chat_id': self.chat_id,
    86	                    'text': text,
    87	                    'parse_mode': 'HTML'
    88	                }
    89	            )
    90	            
    91	            if response.status_code != 200:
    92	                logger.error(f"Failed to send message: {response.text}")
    93	                
    94	        except Exception as e:
    95	            logger.error(f"Error sending message: {e}")
    96	            
    97	    def _format_triggers(self, triggers: list) -> str:
    98	        """Format triggers list"""
    99	        if not triggers:
   100	            return 'No specific triggers'
   101	        return '\n'.join([f'• {t}' for t in triggers])
   102	        
   103	    def _format_phases(self, phases: list) -> str:
   104	        """Format entry phases"""
   105	        return '\n'.join([
   106	            f"{p['phase']}: {p['stake']} @ {p['timing']}"
   107	            for p in phases
   108	        ])
