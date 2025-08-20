"""
Automated Reporting System - Système de reporting automatique
Génère et envoie des rapports daily/weekly/monthly pour clients et admin
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
from pathlib import Path

import pandas as pd
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

from ..models.base import Base
from ..models.notifications import NotificationService
from ..payments.models import Payment, Payout
from ..storage import StorageService

logger = logging.getLogger(__name__)

class ReportType(Enum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_PERFORMANCE = "weekly_performance"
    MONTHLY_STATEMENT = "monthly_statement"
    QUARTERLY_REVIEW = "quarterly_review"
    ANNUAL_REPORT = "annual_report"
    CUSTOM_ANALYTICS = "custom_analytics"

class ReportSchedule(Base):
    """Planification des rapports automatiques."""
    __tablename__ = "report_schedules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # None = rapport admin
    report_type = Column(String, nullable=False)
    frequency = Column(String, nullable=False)  # daily, weekly, monthly, quarterly
    enabled = Column(Boolean, default=True)
    
    # Configuration
    recipients = Column(JSON, default=[])
    filters = Column(JSON, default={})
    format = Column(String, default="pdf")  # pdf, excel, html
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sent = Column(DateTime, nullable=True)
    next_send = Column(DateTime, nullable=True)

class GeneratedReport(Base):
    """Rapports générés et stockés."""
    __tablename__ = "generated_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    report_type = Column(String, nullable=False)
    
    # Contenu
    title = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    file_path = Column(String, nullable=True)
    
    # Métadonnées
    data_summary = Column(JSON, default={})
    generation_time_seconds = Column(Float, nullable=True)
    
    # Statut
    status = Column(String, default="generated")  # generated, sent, failed
    sent_to = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AutomatedReportingService:
    """Service de génération et envoi automatique de rapports."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService(db)
        self.storage = StorageService()
        
        # Configuration
        self.reports_dir = Path(os.getenv("REPORTS_STORAGE_PATH", "storage/reports"))
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Templates
        self.template_dir = Path("templates/reports")
        
    async def generate_daily_summary(self, target_date: datetime = None) -> Dict[str, Any]:
        """Génère le rapport quotidien."""
        if target_date is None:
            target_date = datetime.utcnow().date()
        
        logger.info(f"📊 Generating daily summary for {target_date}")
        
        start_time = datetime.now()
        
        # Période du rapport
        period_start = datetime.combine(target_date, datetime.min.time())
        period_end = period_start + timedelta(days=1)
        
        # Collecter les données
        data = await self._collect_daily_data(period_start, period_end)
        
        # Générer le rapport
        report = GeneratedReport(
            report_type=ReportType.DAILY_SUMMARY.value,
            title=f"Rapport Quotidien - {target_date.strftime('%d/%m/%Y')}",
            period_start=period_start,
            period_end=period_end,
            data_summary=data["summary"]
        )
        
        self.db.add(report)
        self.db.flush()
        
        # Créer le PDF
        pdf_path = await self._generate_daily_pdf(report, data)
        report.file_path = pdf_path
        
        # Calculer le temps de génération
        generation_time = (datetime.now() - start_time).total_seconds()
        report.generation_time_seconds = generation_time
        
        self.db.commit()
        
        # Envoyer aux destinataires
        await self._send_daily_report(report, data)
        
        logger.info(f"✅ Daily summary generated in {generation_time:.2f}s")
        
        return {
            "report_id": report.id,
            "file_path": pdf_path,
            "data_summary": data["summary"],
            "generation_time": generation_time
        }
    
    async def _collect_daily_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collecte les données pour le rapport quotidien."""
        
        # Paiements du jour
        payments = self.db.query(Payment).filter(
            Payment.created_at >= start_date,
            Payment.created_at < end_date
        ).all()
        
        # Payouts du jour
        payouts = self.db.query(Payout).filter(
            Payout.created_at >= start_date,
            Payout.created_at < end_date
        ).all()
        
        # Calculs
        total_payments = len(payments)
        total_revenue = sum(p.amount for p in payments if p.status == 'captured')
        total_payouts = len(payouts)
        total_payout_amount = sum(p.amount for p in payouts if p.status in ['completed', 'processing'])
        
        failed_payments = len([p for p in payments if p.status == 'failed'])
        failed_payouts = len([p for p in payouts if p.status == 'failed'])
        
        # Statistiques par provider
        payment_by_provider = {}
        for payment in payments:
            provider = payment.provider
            if provider not in payment_by_provider:
                payment_by_provider[provider] = {"count": 0, "amount": 0, "failed": 0}
            
            payment_by_provider[provider]["count"] += 1
            if payment.status == 'captured':
                payment_by_provider[provider]["amount"] += payment.amount
            elif payment.status == 'failed':
                payment_by_provider[provider]["failed"] += 1
        
        # Nouveaux utilisateurs (approximation)
        new_users_count = len(set(p.user_id for p in payments if p.user_id))
        
        summary = {
            "date": start_date.date().isoformat(),
            "total_payments": total_payments,
            "total_revenue": total_revenue,
            "total_payouts": total_payouts,
            "total_payout_amount": total_payout_amount,
            "failed_payments": failed_payments,
            "failed_payouts": failed_payouts,
            "failure_rate": (failed_payments / total_payments * 100) if total_payments > 0 else 0,
            "net_revenue": total_revenue - total_payout_amount,
            "new_users": new_users_count,
            "avg_payment_amount": (total_revenue / total_payments) if total_payments > 0 else 0
        }
        
        return {
            "summary": summary,
            "payments": payments,
            "payouts": payouts,
            "payment_by_provider": payment_by_provider,
            "charts_data": await self._prepare_charts_data(payments, payouts)
        }
    
    async def _prepare_charts_data(self, payments: List[Payment], payouts: List[Payout]) -> Dict[str, str]:
        """Prépare les graphiques pour le rapport."""
        charts = {}
        
        # Graphique des paiements par heure
        if payments:
            payment_hours = [p.created_at.hour for p in payments]
            hourly_counts = pd.Series(payment_hours).value_counts().sort_index()
            
            plt.figure(figsize=(10, 6))
            hourly_counts.plot(kind='bar', color='#3b82f6')
            plt.title('Paiements par Heure')
            plt.xlabel('Heure')
            plt.ylabel('Nombre de Paiements')
            plt.xticks(rotation=0)
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            charts['hourly_payments'] = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
        
        # Graphique des statuts de paiement
        if payments:
            status_counts = pd.Series([p.status for p in payments]).value_counts()
            
            plt.figure(figsize=(8, 8))
            colors = {'captured': '#10b981', 'failed': '#ef4444', 'pending': '#f59e0b'}
            status_counts.plot(kind='pie', autopct='%1.1f%%', 
                             colors=[colors.get(status, '#6b7280') for status in status_counts.index])
            plt.title('Répartition des Statuts de Paiement')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            charts['payment_status'] = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
        
        return charts
    
    async def _generate_daily_pdf(self, report: GeneratedReport, data: Dict[str, Any]) -> str:
        """Génère le PDF du rapport quotidien."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        filename = f"daily_report_{report.period_start.strftime('%Y%m%d')}.pdf"
        filepath = self.reports_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Titre
        title = Paragraph(f"<b>{report.title}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Résumé exécutif
        summary = data["summary"]
        
        summary_data = [
            ["Métrique", "Valeur"],
            ["Total Paiements", f"{summary['total_payments']:,}"],
            ["Revenus Total", f"{summary['total_revenue']/100:,.2f} €"],
            ["Payouts Total", f"{summary['total_payouts']:,}"],
            ["Montant Payouts", f"{summary['total_payout_amount']/100:,.2f} €"],
            ["Revenus Net", f"{summary['net_revenue']/100:,.2f} €"],
            ["Taux d'Échec", f"{summary['failure_rate']:.1f}%"],
            ["Nouveaux Utilisateurs", f"{summary['new_users']:,}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("<b>Résumé Exécutif</b>", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Graphiques
        if data.get("charts_data"):
            story.append(Paragraph("<b>Analyses Graphiques</b>", styles['Heading2']))
            
            for chart_name, chart_data in data["charts_data"].items():
                # Décoder et sauvegarder temporairement l'image
                chart_bytes = base64.b64decode(chart_data)
                temp_chart_path = self.reports_dir / f"temp_{chart_name}.png"
                
                with open(temp_chart_path, 'wb') as f:
                    f.write(chart_bytes)
                
                # Ajouter au PDF
                img = Image(str(temp_chart_path), width=15*cm, height=9*cm)
                story.append(img)
                story.append(Spacer(1, 10))
                
                # Nettoyer le fichier temporaire
                temp_chart_path.unlink()
        
        # Détails par provider
        if data.get("payment_by_provider"):
            story.append(Paragraph("<b>Détails par Provider</b>", styles['Heading2']))
            
            provider_data = [["Provider", "Paiements", "Montant", "Échecs", "Taux d'Échec"]]
            
            for provider, stats in data["payment_by_provider"].items():
                failure_rate = (stats["failed"] / stats["count"] * 100) if stats["count"] > 0 else 0
                provider_data.append([
                    provider.title(),
                    f"{stats['count']:,}",
                    f"{stats['amount']/100:,.2f} €",
                    f"{stats['failed']:,}",
                    f"{failure_rate:.1f}%"
                ])
            
            provider_table = Table(provider_data, colWidths=[3*cm, 2*cm, 3*cm, 2*cm, 2*cm])
            provider_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(provider_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        story.append(Paragraph(f"<i>{footer_text}</i>", styles['Normal']))
        
        doc.build(story)
        
        # Stocker dans le système de stockage
        storage_path = await self.storage.store_file(
            str(filepath),
            f"reports/daily/{filename}",
            content_type="application/pdf"
        )
        
        return storage_path
    
    async def _send_daily_report(self, report: GeneratedReport, data: Dict[str, Any]):
        """Envoie le rapport quotidien aux destinataires."""
        
        # Destinataires par défaut (admins)
        admin_emails = os.getenv("ADMIN_REPORT_EMAILS", "admin@smartlinks.com").split(",")
        
        # Lire le fichier PDF
        with open(report.file_path, 'rb') as f:
            pdf_content = base64.b64encode(f.read()).decode()
        
        summary = data["summary"]
        
        for email in admin_emails:
            await self.notifications.send_email(
                to=email.strip(),
                subject=f"📊 Rapport Quotidien SmartLinks - {report.period_start.strftime('%d/%m/%Y')}",
                template="daily_report",
                data={
                    "report_title": report.title,
                    "date": report.period_start.strftime('%d/%m/%Y'),
                    "total_payments": summary["total_payments"],
                    "total_revenue": summary["total_revenue"] / 100,
                    "net_revenue": summary["net_revenue"] / 100,
                    "failure_rate": summary["failure_rate"],
                    "new_users": summary["new_users"]
                },
                attachments=[{
                    "filename": f"Rapport_Quotidien_{report.period_start.strftime('%Y%m%d')}.pdf",
                    "content": pdf_content,
                    "content_type": "application/pdf"
                }]
            )
        
        report.status = "sent"
        report.sent_to = admin_emails
        self.db.commit()
    
    async def generate_weekly_performance(self, week_start: datetime = None) -> Dict[str, Any]:
        """Génère le rapport hebdomadaire de performance."""
        if week_start is None:
            # Lundi de la semaine dernière
            today = datetime.utcnow().date()
            days_since_monday = today.weekday()
            week_start = datetime.combine(today - timedelta(days=days_since_monday + 7), datetime.min.time())
        
        week_end = week_start + timedelta(days=7)
        
        logger.info(f"📈 Generating weekly performance report for {week_start.date()} - {week_end.date()}")
        
        # Collecter les données hebdomadaires
        weekly_data = await self._collect_weekly_data(week_start, week_end)
        
        # Créer le rapport
        report = GeneratedReport(
            report_type=ReportType.WEEKLY_PERFORMANCE.value,
            title=f"Performance Hebdomadaire - Semaine du {week_start.strftime('%d/%m/%Y')}",
            period_start=week_start,
            period_end=week_end,
            data_summary=weekly_data["summary"]
        )
        
        self.db.add(report)
        self.db.flush()
        
        # Générer le rapport Excel
        excel_path = await self._generate_weekly_excel(report, weekly_data)
        report.file_path = excel_path
        
        self.db.commit()
        
        # Envoyer le rapport
        await self._send_weekly_report(report, weekly_data)
        
        return {
            "report_id": report.id,
            "file_path": excel_path,
            "data_summary": weekly_data["summary"]
        }
    
    async def _collect_weekly_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collecte les données pour le rapport hebdomadaire."""
        
        # Données jour par jour
        daily_data = []
        current_date = start_date
        
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            
            day_payments = self.db.query(Payment).filter(
                Payment.created_at >= current_date,
                Payment.created_at < next_date
            ).all()
            
            day_revenue = sum(p.amount for p in day_payments if p.status == 'captured')
            day_count = len(day_payments)
            day_failures = len([p for p in day_payments if p.status == 'failed'])
            
            daily_data.append({
                "date": current_date.date(),
                "payments_count": day_count,
                "revenue": day_revenue,
                "failures": day_failures,
                "failure_rate": (day_failures / day_count * 100) if day_count > 0 else 0
            })
            
            current_date = next_date
        
        # Totaux de la semaine
        total_payments = sum(d["payments_count"] for d in daily_data)
        total_revenue = sum(d["revenue"] for d in daily_data)
        total_failures = sum(d["failures"] for d in daily_data)
        
        # Comparaison avec la semaine précédente
        prev_week_start = start_date - timedelta(days=7)
        prev_week_end = start_date
        
        prev_payments = self.db.query(Payment).filter(
            Payment.created_at >= prev_week_start,
            Payment.created_at < prev_week_end
        ).all()
        
        prev_revenue = sum(p.amount for p in prev_payments if p.status == 'captured')
        prev_count = len(prev_payments)
        
        # Calculs de croissance
        revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        volume_growth = ((total_payments - prev_count) / prev_count * 100) if prev_count > 0 else 0
        
        summary = {
            "week_start": start_date.date().isoformat(),
            "week_end": end_date.date().isoformat(),
            "total_payments": total_payments,
            "total_revenue": total_revenue,
            "total_failures": total_failures,
            "avg_daily_revenue": total_revenue / 7,
            "avg_daily_payments": total_payments / 7,
            "revenue_growth": revenue_growth,
            "volume_growth": volume_growth,
            "best_day": max(daily_data, key=lambda x: x["revenue"])["date"].isoformat() if daily_data else None,
            "worst_day": min(daily_data, key=lambda x: x["revenue"])["date"].isoformat() if daily_data else None
        }
        
        return {
            "summary": summary,
            "daily_data": daily_data,
            "comparison": {
                "prev_revenue": prev_revenue,
                "prev_count": prev_count,
                "revenue_growth": revenue_growth,
                "volume_growth": volume_growth
            }
        }
    
    async def _generate_weekly_excel(self, report: GeneratedReport, data: Dict[str, Any]) -> str:
        """Génère le rapport Excel hebdomadaire."""
        filename = f"weekly_report_{report.period_start.strftime('%Y%m%d')}.xlsx"
        filepath = self.reports_dir / filename
        
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            # Feuille de résumé
            summary_df = pd.DataFrame([data["summary"]])
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
            
            # Feuille des données quotidiennes
            daily_df = pd.DataFrame(data["daily_data"])
            daily_df.to_excel(writer, sheet_name='Données Quotidiennes', index=False)
            
            # Feuille de comparaison
            comparison_df = pd.DataFrame([data["comparison"]])
            comparison_df.to_excel(writer, sheet_name='Comparaison', index=False)
        
        # Stocker dans le système de stockage
        storage_path = await self.storage.store_file(
            str(filepath),
            f"reports/weekly/{filename}",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        return storage_path
    
    async def _send_weekly_report(self, report: GeneratedReport, data: Dict[str, Any]):
        """Envoie le rapport hebdomadaire."""
        admin_emails = os.getenv("ADMIN_REPORT_EMAILS", "admin@smartlinks.com").split(",")
        
        with open(report.file_path, 'rb') as f:
            excel_content = base64.b64encode(f.read()).decode()
        
        summary = data["summary"]
        
        for email in admin_emails:
            await self.notifications.send_email(
                to=email.strip(),
                subject=f"📈 Rapport Hebdomadaire SmartLinks - Semaine du {report.period_start.strftime('%d/%m/%Y')}",
                template="weekly_report",
                data={
                    "report_title": report.title,
                    "week_start": report.period_start.strftime('%d/%m/%Y'),
                    "week_end": report.period_end.strftime('%d/%m/%Y'),
                    "total_revenue": summary["total_revenue"] / 100,
                    "revenue_growth": summary["revenue_growth"],
                    "volume_growth": summary["volume_growth"],
                    "best_day": summary["best_day"],
                    "avg_daily_revenue": summary["avg_daily_revenue"] / 100
                },
                attachments=[{
                    "filename": f"Rapport_Hebdomadaire_{report.period_start.strftime('%Y%m%d')}.xlsx",
                    "content": excel_content,
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }]
            )
        
        report.status = "sent"
        report.sent_to = admin_emails
        self.db.commit()
    
    async def schedule_report(self, report_type: ReportType, frequency: str, 
                            recipients: List[str], user_id: str = None,
                            filters: Dict[str, Any] = None) -> ReportSchedule:
        """Programme un rapport automatique."""
        
        schedule = ReportSchedule(
            user_id=user_id,
            report_type=report_type.value,
            frequency=frequency,
            recipients=recipients,
            filters=filters or {}
        )
        
        # Calculer la prochaine exécution
        schedule.next_send = self._calculate_next_send(frequency)
        
        self.db.add(schedule)
        self.db.commit()
        
        logger.info(f"📅 Scheduled {report_type.value} report ({frequency}) for {len(recipients)} recipients")
        
        return schedule
    
    def _calculate_next_send(self, frequency: str) -> datetime:
        """Calcule la prochaine date d'envoi."""
        now = datetime.utcnow()
        
        if frequency == "daily":
            return now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif frequency == "weekly":
            # Lundi à 8h
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            return (now + timedelta(days=days_until_monday)).replace(hour=8, minute=0, second=0, microsecond=0)
        elif frequency == "monthly":
            # Premier du mois suivant à 8h
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
            else:
                next_month = now.replace(month=now.month + 1, day=1, hour=8, minute=0, second=0, microsecond=0)
            return next_month
        
        return now + timedelta(days=1)

# Tâches automatiques
async def process_scheduled_reports():
    """Traite les rapports programmés."""
    from ..db import get_db
    
    db = next(get_db())
    try:
        service = AutomatedReportingService(db)
        now = datetime.utcnow()
        
        # Trouver les rapports à envoyer
        due_schedules = db.query(ReportSchedule).filter(
            ReportSchedule.enabled == True,
            ReportSchedule.next_send <= now
        ).all()
        
        for schedule in due_schedules:
            try:
                if schedule.report_type == ReportType.DAILY_SUMMARY.value:
                    await service.generate_daily_summary()
                elif schedule.report_type == ReportType.WEEKLY_PERFORMANCE.value:
                    await service.generate_weekly_performance()
                
                # Programmer la prochaine exécution
                schedule.last_sent = now
                schedule.next_send = service._calculate_next_send(schedule.frequency)
                
            except Exception as e:
                logger.error(f"Error processing scheduled report {schedule.id}: {e}")
        
        db.commit()
        logger.info(f"Processed {len(due_schedules)} scheduled reports")
        
    finally:
        db.close()

# Configuration par défaut
async def setup_default_report_schedules(db: Session):
    """Configure les rapports par défaut."""
    service = AutomatedReportingService(db)
    
    admin_emails = os.getenv("ADMIN_REPORT_EMAILS", "admin@smartlinks.com").split(",")
    
    # Rapport quotidien
    await service.schedule_report(
        ReportType.DAILY_SUMMARY,
        "daily",
        admin_emails
    )
    
    # Rapport hebdomadaire
    await service.schedule_report(
        ReportType.WEEKLY_PERFORMANCE,
        "weekly", 
        admin_emails
    )
    
    logger.info("✅ Default report schedules configured")
