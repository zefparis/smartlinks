"""
Invoice Generator - Génération automatique de factures PDF avec envoi email
Gère la création, stockage et envoi automatique des factures et justificatifs
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import qrcode
from io import BytesIO
import base64

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import Payment, Invoice, User, Company
from ..models.notifications import NotificationService
from ..storage import StorageService

logger = logging.getLogger(__name__)

class InvoiceGenerator:
    """Générateur automatique de factures PDF avec stockage et envoi."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService(db)
        self.storage = StorageService()
        
        # Configuration entreprise
        self.company_info = {
            "name": os.getenv("COMPANY_NAME", "SmartLinks SAS"),
            "address": os.getenv("COMPANY_ADDRESS", "123 Rue de la Tech\n75001 Paris, France"),
            "siret": os.getenv("COMPANY_SIRET", "12345678901234"),
            "vat_number": os.getenv("COMPANY_VAT", "FR12345678901"),
            "email": os.getenv("COMPANY_EMAIL", "billing@smartlinks.com"),
            "phone": os.getenv("COMPANY_PHONE", "+33 1 23 45 67 89"),
            "website": os.getenv("COMPANY_WEBSITE", "https://smartlinks.com"),
            "logo_path": os.getenv("COMPANY_LOGO_PATH", "assets/logo.png")
        }
        
        # Répertoires
        self.invoice_dir = Path(os.getenv("INVOICE_STORAGE_PATH", "storage/invoices"))
        self.invoice_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_payment_invoice(self, payment_id: str) -> Dict[str, Any]:
        """Génère une facture pour un paiement."""
        logger.info(f"🧾 Generating invoice for payment {payment_id}")
        
        try:
            # Récupérer le paiement
            payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")
            
            # Vérifier si facture existe déjà
            existing_invoice = self.db.query(Invoice).filter(Invoice.payment_id == payment_id).first()
            if existing_invoice:
                logger.info(f"Invoice already exists for payment {payment_id}")
                return {"invoice_id": existing_invoice.id, "status": "exists"}
            
            # Créer l'enregistrement facture
            invoice = Invoice(
                id=str(uuid.uuid4()),
                payment_id=payment_id,
                user_id=payment.user_id,
                invoice_number=await self._generate_invoice_number(),
                amount=payment.amount,
                currency=payment.currency,
                status="draft",
                created_at=datetime.utcnow()
            )
            self.db.add(invoice)
            self.db.flush()
            
            # Générer le PDF
            pdf_path = await self._generate_pdf(invoice, payment)
            
            # Stocker le fichier
            storage_path = await self.storage.store_file(
                pdf_path,
                f"invoices/{invoice.invoice_number}.pdf",
                content_type="application/pdf"
            )
            
            # Mettre à jour l'invoice
            invoice.pdf_path = storage_path
            invoice.status = "generated"
            invoice.generated_at = datetime.utcnow()
            self.db.commit()
            
            # Envoyer par email
            if payment.user and payment.user.email:
                await self._send_invoice_email(invoice, payment)
                invoice.status = "sent"
                invoice.sent_at = datetime.utcnow()
                self.db.commit()
            
            logger.info(f"✅ Invoice {invoice.invoice_number} generated successfully")
            return {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "pdf_path": storage_path,
                "status": "sent" if invoice.sent_at else "generated"
            }
            
        except Exception as e:
            logger.error(f"Error generating invoice for payment {payment_id}: {e}")
            raise
    
    async def _generate_invoice_number(self) -> str:
        """Génère un numéro de facture unique."""
        year = datetime.now().year
        month = datetime.now().month
        
        # Compter les factures du mois
        count = self.db.query(Invoice).filter(
            Invoice.created_at >= datetime(year, month, 1)
        ).count()
        
        return f"INV-{year}{month:02d}-{count + 1:04d}"
    
    async def _generate_pdf(self, invoice: Invoice, payment: Payment) -> str:
        """Génère le PDF de la facture."""
        filename = f"{invoice.invoice_number}.pdf"
        filepath = self.invoice_dir / filename
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1f2937')
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#374151')
        )
        
        # Contenu du PDF
        story = []
        
        # En-tête avec logo et infos entreprise
        story.append(Paragraph(f"<b>{self.company_info['name']}</b>", title_style))
        story.append(Paragraph(self.company_info['address'].replace('\n', '<br/>'), header_style))
        story.append(Paragraph(f"SIRET: {self.company_info['siret']}", header_style))
        story.append(Paragraph(f"TVA: {self.company_info['vat_number']}", header_style))
        story.append(Spacer(1, 20))
        
        # Titre facture
        story.append(Paragraph(f"<b>FACTURE N° {invoice.invoice_number}</b>", title_style))
        story.append(Spacer(1, 20))
        
        # Informations client
        if payment.user:
            client_info = [
                ["<b>Facturé à:</b>", ""],
                [payment.user.email, ""],
                [f"ID Client: {payment.user.id}", ""],
            ]
            
            if hasattr(payment.user, 'company_name') and payment.user.company_name:
                client_info.insert(1, [payment.user.company_name, ""])
        else:
            client_info = [
                ["<b>Facturé à:</b>", ""],
                ["Client anonyme", ""],
            ]
        
        # Informations facture
        invoice_info = [
            ["<b>Date de facture:</b>", invoice.created_at.strftime("%d/%m/%Y")],
            ["<b>Date de paiement:</b>", payment.created_at.strftime("%d/%m/%Y")],
            ["<b>Méthode de paiement:</b>", payment.provider.replace('_', ' ').title()],
            ["<b>ID Transaction:</b>", payment.provider_payment_id or payment.id],
        ]
        
        # Table avec infos client et facture
        info_table = Table([
            [Table(client_info, colWidths=[4*cm, 4*cm]), Table(invoice_info, colWidths=[4*cm, 4*cm])]
        ], colWidths=[8*cm, 8*cm])
        
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Détails de la facture
        details_data = [
            ["<b>Description</b>", "<b>Quantité</b>", "<b>Prix unitaire</b>", "<b>Total</b>"],
            [
                "Service SmartLinks - Commission sur revenus",
                "1",
                f"{payment.amount / 100:.2f} {payment.currency}",
                f"{payment.amount / 100:.2f} {payment.currency}"
            ]
        ]
        
        details_table = Table(details_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        # Total
        total_data = [
            ["", "", "<b>Sous-total:</b>", f"<b>{payment.amount / 100:.2f} {payment.currency}</b>"],
            ["", "", "<b>TVA (20%):</b>", f"<b>{payment.amount * 0.2 / 100:.2f} {payment.currency}</b>"],
            ["", "", "<b>TOTAL TTC:</b>", f"<b>{payment.amount * 1.2 / 100:.2f} {payment.currency}</b>"],
        ]
        
        total_table = Table(total_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        total_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (-1, -1), 10),
            ('LINEBELOW', (2, -1), (-1, -1), 2, colors.HexColor('#1f2937')),
        ]))
        
        story.append(total_table)
        story.append(Spacer(1, 30))
        
        # QR Code pour vérification
        qr_data = f"https://smartlinks.com/invoice/{invoice.invoice_number}/verify"
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Pied de page
        footer_text = f"""
        <b>Conditions de paiement:</b> Paiement comptant<br/>
        <b>Contact:</b> {self.company_info['email']} - {self.company_info['phone']}<br/>
        <b>Site web:</b> {self.company_info['website']}<br/><br/>
        <i>Facture générée automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>
        """
        
        story.append(Paragraph(footer_text, header_style))
        
        # Construire le PDF
        doc.build(story)
        
        logger.info(f"📄 PDF generated: {filepath}")
        return str(filepath)
    
    async def _send_invoice_email(self, invoice: Invoice, payment: Payment):
        """Envoie la facture par email."""
        try:
            # Lire le fichier PDF
            with open(invoice.pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Encoder en base64 pour l'attachement
            pdf_base64 = base64.b64encode(pdf_content).decode()
            
            await self.notifications.send_email(
                to=payment.user.email,
                subject=f"📧 Facture {invoice.invoice_number} - SmartLinks",
                template="invoice_email",
                data={
                    "invoice_number": invoice.invoice_number,
                    "amount": payment.amount / 100,
                    "currency": payment.currency,
                    "payment_date": payment.created_at.strftime("%d/%m/%Y"),
                    "user_name": getattr(payment.user, 'name', payment.user.email),
                },
                attachments=[{
                    "filename": f"Facture_{invoice.invoice_number}.pdf",
                    "content": pdf_base64,
                    "content_type": "application/pdf"
                }]
            )
            
            logger.info(f"📧 Invoice email sent to {payment.user.email}")
            
        except Exception as e:
            logger.error(f"Error sending invoice email: {e}")
            raise
    
    async def generate_monthly_statement(self, user_id: str, year: int, month: int) -> Dict[str, Any]:
        """Génère un relevé mensuel pour un utilisateur."""
        logger.info(f"📊 Generating monthly statement for user {user_id} - {year}/{month}")
        
        try:
            # Récupérer tous les paiements du mois
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            payments = self.db.query(Payment).filter(
                and_(
                    Payment.user_id == user_id,
                    Payment.created_at >= start_date,
                    Payment.created_at < end_date,
                    Payment.status == 'captured'
                )
            ).all()
            
            if not payments:
                return {"status": "no_data", "message": "No payments found for this period"}
            
            # Créer le relevé
            statement_id = str(uuid.uuid4())
            statement_number = f"REL-{year}{month:02d}-{user_id[:8]}"
            
            # Générer le PDF du relevé
            pdf_path = await self._generate_statement_pdf(
                statement_number, payments, start_date, end_date
            )
            
            # Stocker et envoyer
            storage_path = await self.storage.store_file(
                pdf_path,
                f"statements/{statement_number}.pdf",
                content_type="application/pdf"
            )
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.email:
                await self._send_statement_email(user, statement_number, storage_path, payments)
            
            return {
                "statement_id": statement_id,
                "statement_number": statement_number,
                "pdf_path": storage_path,
                "total_amount": sum(p.amount for p in payments),
                "payment_count": len(payments),
                "status": "sent"
            }
            
        except Exception as e:
            logger.error(f"Error generating monthly statement: {e}")
            raise
    
    async def _generate_statement_pdf(self, statement_number: str, payments: List[Payment], 
                                    start_date: datetime, end_date: datetime) -> str:
        """Génère le PDF du relevé mensuel."""
        filename = f"{statement_number}.pdf"
        filepath = self.invoice_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Titre
        title = Paragraph(f"<b>RELEVÉ MENSUEL - {statement_number}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Période
        period_text = f"Période: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        story.append(Paragraph(period_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tableau des paiements
        data = [["Date", "ID Transaction", "Montant", "Statut"]]
        total_amount = 0
        
        for payment in payments:
            data.append([
                payment.created_at.strftime("%d/%m/%Y"),
                payment.provider_payment_id or payment.id[:8],
                f"{payment.amount / 100:.2f} {payment.currency}",
                payment.status.title()
            ])
            total_amount += payment.amount
        
        # Ligne de total
        data.append(["", "", f"<b>TOTAL: {total_amount / 100:.2f} EUR</b>", ""])
        
        table = Table(data, colWidths=[3*cm, 5*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        doc.build(story)
        
        return str(filepath)
    
    async def _send_statement_email(self, user: User, statement_number: str, 
                                  pdf_path: str, payments: List[Payment]):
        """Envoie le relevé par email."""
        with open(pdf_path, 'rb') as f:
            pdf_content = base64.b64encode(f.read()).decode()
        
        await self.notifications.send_email(
            to=user.email,
            subject=f"📊 Relevé mensuel {statement_number} - SmartLinks",
            template="monthly_statement",
            data={
                "statement_number": statement_number,
                "payment_count": len(payments),
                "total_amount": sum(p.amount for p in payments) / 100,
                "user_name": getattr(user, 'name', user.email)
            },
            attachments=[{
                "filename": f"Releve_{statement_number}.pdf",
                "content": pdf_content,
                "content_type": "application/pdf"
            }]
        )

# Tâche automatique pour génération des factures
async def auto_generate_invoices():
    """Génère automatiquement les factures pour les nouveaux paiements."""
    from ..db import get_db
    
    db = next(get_db())
    try:
        generator = InvoiceGenerator(db)
        
        # Trouver les paiements sans facture
        payments_without_invoice = db.query(Payment).filter(
            and_(
                Payment.status == 'captured',
                ~Payment.id.in_(
                    db.query(Invoice.payment_id).filter(Invoice.payment_id.isnot(None))
                )
            )
        ).all()
        
        results = []
        for payment in payments_without_invoice:
            try:
                result = await generator.generate_payment_invoice(payment.id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate invoice for payment {payment.id}: {e}")
        
        logger.info(f"Auto-generated {len(results)} invoices")
        return results
        
    finally:
        db.close()
