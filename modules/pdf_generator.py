"""
PDF Generator - Create consolidated report for 3 teams
Professional layout with charts and analysis
"""

import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from typing import List, Dict
import os

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
    def _setup_styles(self):
        """Setup custom styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='TeamHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
    def create_full_report(self, teams: List[str]) -> str:
        """
        Create comprehensive PDF report for all 3 teams
        Returns path to generated PDF
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/tmp/team_specialist_report_{timestamp}.pdf'
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Title page
        story.append(Paragraph('Team Specialist Report', self.styles['CustomTitle']))
        story.append(Paragraph(f'Portugal - 3 Grandes Analysis', self.styles['Heading2']))
        story.append(Paragraph(f'Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}', self.styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # Summary section
        story.append(Paragraph('Methodology', self.styles['Heading2']))
        story.append(Paragraph(
            '• Analysis based on MINIMUM values (not averages)<br/>'
            '• 5-year historical data (2019-2024)<br/>'
            '• Kelly Criterion for stake sizing<br/>'
            '• 70%, 80%, 90% confidence levels<br/>'
            '• Pre-match + Live HT triggers',
            self.styles['Normal']
        ))
        story.append(Spacer(1, 1*cm))
        
        # Team sections
        from modules.supabase_client import SupabaseClient
        supabase = SupabaseClient()
        
        for team_name in teams:
            analysis = supabase.get_team_analysis(team_name)
            
            if not analysis:
                logger.warning(f"No analysis data for {team_name}")
                continue
                
            story.append(PageBreak())
            story.extend(self._create_team_section(team_name, analysis))
            
        # Build PDF
        doc.build(story)
        logger.info(f"PDF generated: {filename}")
        
        return filename
        
    def _create_team_section(self, team_name: str, analysis: Dict) -> List:
        """Create detailed section for one team"""
        elements = []
        
        # Team header
        elements.append(Paragraph(f'📊 {team_name}', self.styles['TeamHeader']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Key stats table
        elements.append(Paragraph('Minimum Values Analysis', self.styles['Heading3']))
        
        home_stats = analysis.get('home_stats', {})
        away_stats = analysis.get('away_stats', {})
        
        stats_data = [
            ['Metric', 'Home', 'Away'],
            ['Total Matches', 
             home_stats.get('total_matches', 0),
             away_stats.get('total_matches', 0)],
            ['Win Rate',
             f"{home_stats.get('results', {}).get('win_rate', 0):.1f}%",
             f"{away_stats.get('results', {}).get('win_rate', 0):.1f}%"],
            ['90% Min Goals',
             f"{analysis.get('min_90_confidence', {}).get('minimum_team_goals', 0):.1f}",
             f"{analysis.get('min_90_confidence', {}).get('minimum_team_goals', 0):.1f}"],
            ['80% Min Goals',
             f"{analysis.get('min_80_confidence', {}).get('minimum_team_goals', 0):.1f}",
             f"{analysis.get('min_80_confidence', {}).get('minimum_team_goals', 0):.1f}"],
            ['BTTS Rate',
             f"{home_stats.get('results', {}).get('btts_rate', 0):.1f}%",
             f"{away_stats.get('results', {}).get('btts_rate', 0):.1f}%"],
        ]
        
        stats_table = Table(stats_data, colWidths=[7*cm, 4*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 1*cm))
        
        # Triggers section
        elements.append(Paragraph('Active Triggers', self.styles['Heading3']))
        
        triggers = analysis.get('special_triggers', {})
        
        trigger_text = ''
        for trigger_name, trigger_data in triggers.items():
            if trigger_data.get('total_matches', 0) > 5:
                trigger_text += f"<b>{trigger_name}</b>: {trigger_data.get('total_matches', 0)} occurrences<br/>"
                
        elements.append(Paragraph(trigger_text or 'No significant triggers detected', self.styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
