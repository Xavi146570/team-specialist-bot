1	"""
     2	PDF Generator - Create consolidated report for 3 teams
     3	Professional layout with charts and analysis
     4	"""
     5	
     6	import logging
     7	from reportlab.lib.pagesizes import A4
     8	from reportlab.lib import colors
     9	from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    10	from reportlab.lib.units import cm
    11	from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    12	from reportlab.lib.enums import TA_CENTER, TA_LEFT
    13	from datetime import datetime
    14	from typing import List
    15	import os
    16	
    17	logger = logging.getLogger(__name__)
    18	
    19	class PDFGenerator:
    20	    def __init__(self):
    21	        self.styles = getSampleStyleSheet()
    22	        self._setup_styles()
    23	        
    24	    def _setup_styles(self):
    25	        """Setup custom styles"""
    26	        self.styles.add(ParagraphStyle(
    27	            name='CustomTitle',
    28	            parent=self.styles['Heading1'],
    29	            fontSize=24,
    30	            textColor=colors.HexColor('#1a1a1a'),
    31	            spaceAfter=30,
    32	            alignment=TA_CENTER
    33	        ))
    34	        
    35	        self.styles.add(ParagraphStyle(
    36	            name='TeamHeader',
    37	            parent=self.styles['Heading2'],
    38	            fontSize=18,
    39	            textColor=colors.HexColor('#2563eb'),
    40	            spaceAfter=12,
    41	            spaceBefore=12
    42	        ))
    43	        
    44	    def create_full_report(self, teams: List[str]) -> str:
    45	        """
    46	        Create comprehensive PDF report for all 3 teams
    47	        Returns path to generated PDF
    48	        """
    49	        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    50	        filename = f'/tmp/team_specialist_report_{timestamp}.pdf'
    51	        
    52	        doc = SimpleDocTemplate(
    53	            filename,
    54	            pagesize=A4,
    55	            rightMargin=2*cm,
    56	            leftMargin=2*cm,
    57	            topMargin=2*cm,
    58	            bottomMargin=2*cm
    59	        )
    60	        
    61	        story = []
    62	        
    63	        # Title page
    64	        story.append(Paragraph('Team Specialist Report', self.styles['CustomTitle']))
    65	        story.append(Paragraph(f'Portugal - 3 Grandes Analysis', self.styles['Heading2']))
    66	        story.append(Paragraph(f'Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}', self.styles['Normal']))
    67	        story.append(Spacer(1, 1*cm))
    68	        
    69	        # Summary section
    70	        story.append(Paragraph('Methodology', self.styles['Heading2']))
    71	        story.append(Paragraph(
    72	            '• Analysis based on MINIMUM values (not averages)<br/>'
    73	            '• 5-year historical data (2019-2024)<br/>'
    74	            '• Kelly Criterion for stake sizing<br/>'
    75	            '• 70%, 80%, 90% confidence levels<br/>'
    76	            '• Pre-match + Live HT triggers',
    77	            self.styles['Normal']
    78	        ))
    79	        story.append(Spacer(1, 1*cm))
    80	        
    81	        # Team sections
    82	        from modules.supabase_client import SupabaseClient
    83	        supabase = SupabaseClient()
    84	        
    85	        for team_name in teams:
    86	            analysis = supabase.get_team_analysis(team_name)
    87	            
    88	            if not analysis:
    89	                logger.warning(f"No analysis data for {team_name}")
    90	                continue
    91	                
    92	            story.append(PageBreak())
    93	            story.extend(self._create_team_section(team_name, analysis))
    94	            
    95	        # Build PDF
    96	        doc.build(story)
    97	        logger.info(f"PDF generated: {filename}")
    98	        
    99	        return filename
   100	        
   101	    def _create_team_section(self, team_name: str, analysis: Dict) -> List:
   102	        """Create detailed section for one team"""
   103	        elements = []
   104	        
   105	        # Team header
   106	        elements.append(Paragraph(f'📊 {team_name}', self.styles['TeamHeader']))
   107	        elements.append(Spacer(1, 0.5*cm))
   108	        
   109	        # Key stats table
   110	        elements.append(Paragraph('Minimum Values Analysis', self.styles['Heading3']))
   111	        
   112	        home_stats = analysis.get('home_stats', {})
   113	        away_stats = analysis.get('away_stats', {})
   114	        
   115	        stats_data = [
   116	            ['Metric', 'Home', 'Away'],
   117	            ['Total Matches', 
   118	             home_stats.get('total_matches', 0),
   119	             away_stats.get('total_matches', 0)],
   120	            ['Win Rate',
   121	             f"{home_stats.get('results', {}).get('win_rate', 0):.1f}%",
   122	             f"{away_stats.get('results', {}).get('win_rate', 0):.1f}%"],
   123	            ['90% Min Goals',
   124	             f"{analysis.get('min_90_confidence', {}).get('minimum_team_goals', 0):.1f}",
   125	             f"{analysis.get('min_90_confidence', {}).get('minimum_team_goals', 0):.1f}"],
   126	            ['80% Min Goals',
   127	             f"{analysis.get('min_80_confidence', {}).get('minimum_team_goals', 0):.1f}",
   128	             f"{analysis.get('min_80_confidence', {}).get('minimum_team_goals', 0):.1f}"],
   129	            ['BTTS Rate',
   130	             f"{home_stats.get('results', {}).get('btts_rate', 0):.1f}%",
   131	             f"{away_stats.get('results', {}).get('btts_rate', 0):.1f}%"],
   132	        ]
   133	        
   134	        stats_table = Table(stats_data, colWidths=[7*cm, 4*cm, 4*cm])
   135	        stats_table.setStyle(TableStyle([
   136	            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
   137	            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
   138	            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
   139	            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
   140	            ('FONTSIZE', (0, 0), (-1, 0), 12),
   141	            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
   142	            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
   143	            ('GRID', (0, 0), (-1, -1), 1, colors.black)
   144	        ]))
   145	        
   146	        elements.append(stats_table)
   147	        elements.append(Spacer(1, 1*cm))
   148	        
   149	        # Triggers section
   150	        elements.append(Paragraph('Active Triggers', self.styles['Heading3']))
   151	        
   152	        triggers = analysis.get('special_triggers', {})
   153	        
   154	        trigger_text = ''
   155	        for trigger_name, trigger_data in triggers.items():
   156	            if trigger_data.get('total_matches', 0) > 5:
   157	                trigger_text += f"<b>{trigger_name}</b>: {trigger_data.get('total_matches', 0)} occurrences<br/>"
   158	                
   159	        elements.append(Paragraph(trigger_text or 'No significant triggers detected', self.styles['Normal']))
   160	        elements.append(Spacer(1, 0.5*cm))
   161	        
   162	        return elements
