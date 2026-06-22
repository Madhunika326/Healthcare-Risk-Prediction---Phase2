"""
Export Routes
PDF and CSV export functionality
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from io import BytesIO, StringIO
import csv
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from app import db
from app.models.prediction import Prediction
from app.models.report import Report

export_bp = Blueprint('export', __name__)


def _risk_band(score):
    if score < 35:
        return 'Low', colors.HexColor('#10B981')
    if score < 65:
        return 'Medium', colors.HexColor('#F59E0B')
    return 'High', colors.HexColor('#EF4444')


def _render_pdf(prediction):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.7 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0F172A'),
        alignment=1,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748B'),
        alignment=1,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=10,
        spaceAfter=8,
    )

    risk_label, risk_color = _risk_band(prediction.health_risk_score)
    created_at = prediction.created_at.strftime('%d %b %Y, %I:%M %p')
    report_date = datetime.utcnow().strftime('%d %b %Y, %I:%M %p UTC')
    risk_factors = prediction.get_risk_factors()
    recommendations = prediction.get_recommendations()

    def draw_header_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#0F172A'))
        canvas.rect(0, letter[1] - 42, letter[0], 42, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawString(40, letter[1] - 26, 'Healthcare Risk Prediction Platform')
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(letter[0] - 40, letter[1] - 26, 'AI-Powered Risk Assessment Report')
        canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
        canvas.line(40, 38, letter[0] - 40, 38)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(40, 24, f'Generated {report_date}')
        canvas.drawRightString(letter[0] - 40, 24, f'Page {canvas.getPageNumber()}')
        canvas.restoreState()

    elements = [
        Spacer(1, 0.45 * inch),
        Paragraph('Clinical Risk Assessment Report', title_style),
        Paragraph('Patient-centered summary for healthcare review and follow-up planning', subtitle_style),
        HRFlowable(width='100%', color=colors.HexColor('#E2E8F0'), thickness=1, spaceBefore=4, spaceAfter=10),
        Paragraph('Patient Summary', section_style),
    ]

    summary_rows = [
        ['Patient', prediction.user.get_full_name() if prediction.user else 'Patient'],
        ['Assessment Date', created_at],
        ['Report Generated', report_date],
        ['Risk Score', f'{prediction.health_risk_score:.2f}'],
        ['Risk Category', risk_label],
    ]
    summary_table = Table(summary_rows, colWidths=[1.7 * inch, 4.4 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEADING', (0, 0), (-1, -1), 14),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (1, 3), (1, 4), colors.whitesmoke),
        ('TEXTCOLOR', (1, 4), (1, 4), risk_color),
        ('FONTNAME', (1, 4), (1, 4), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Paragraph('Key Risk Factors', section_style))

    if risk_factors:
        for factor in risk_factors:
            elements.append(Paragraph(f'• <b>{factor["factor"]}</b>: {factor["description"]}', styles['BodyText']))
    else:
        elements.append(Paragraph('No major risk factors were identified by the model.', styles['BodyText']))

    elements.append(Paragraph('Health Recommendations', section_style))
    for recommendation in recommendations or ['Continue regular monitoring and preventive care.']:
        elements.append(Paragraph(f'• {recommendation}', styles['BodyText']))

    elements.append(Paragraph('Lifestyle Suggestions', section_style))
    elements.append(Paragraph('• Maintain a balanced diet, regular activity, adequate hydration, and consistent sleep habits.', styles['BodyText']))
    elements.append(Paragraph('• Reduce delays in seeking care and keep scheduled preventive visits.', styles['BodyText']))
    elements.append(Paragraph('Future Monitoring Advice', section_style))
    elements.append(Paragraph('• Reassess risk after lifestyle changes or in 30-60 days if risk factors persist.', styles['BodyText']))

    doc.build(elements, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    buffer.seek(0)
    return buffer


def _store_report(prediction, buffer):
    reports_dir = Path(current_app.config['REPORTS_FOLDER'])
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_name = f'health_risk_report_{prediction.id}.pdf'
    file_path = reports_dir / file_name
    file_path.write_bytes(buffer.getvalue())

    report = Report.query.filter_by(prediction_id=prediction.id).first()
    if not report:
        report = Report(
            user_id=prediction.user_id,
            prediction_id=prediction.id,
            report_type='assessment_pdf',
            file_name=file_name,
            file_path=str(file_path),
        )
        db.session.add(report)
    else:
        report.file_name = file_name
        report.file_path = str(file_path)
        report.generated_at = datetime.utcnow()
    db.session.commit()
    return file_path


@export_bp.route('/predictions/csv')
@login_required
def export_predictions_csv():
    """Export predictions to CSV"""
    predictions = current_user.predictions.all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Prediction ID', 'Date', 'Age', 'Health Awareness Score',
        'Symptom Severity', 'Distance to Healthcare (km)',
        'Fear of Cost', 'Fear of Hospital', 'Delay in Seeking Care (days)',
        'Gender', 'Residence', 'Education Level', 'Income Level',
        'Insurance Status', 'Risk Score', 'Risk Category'
    ])
    
    # Data
    for pred in predictions:
        writer.writerow([
            pred.id,
            pred.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            pred.age,
            pred.health_awareness_score,
            pred.symptom_severity,
            pred.distance_to_healthcare_km,
            pred.fear_of_cost,
            pred.fear_of_hospital,
            pred.delay_in_seeking_care_days,
            pred.gender,
            pred.residence,
            pred.education_level,
            pred.income_level,
            pred.insurance_status,
            pred.health_risk_score,
            pred.risk_category
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return send_file(
        BytesIO(csv_content.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'predictions_{datetime.now().strftime("%Y%m%d")}.csv'
    )


@export_bp.route('/prediction/<int:prediction_id>/pdf')
@login_required
def export_prediction_pdf(prediction_id):
    """Export prediction report to PDF"""
    prediction = Prediction.query.filter_by(
        id=prediction_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        buffer = _render_pdf(prediction)
        _store_report(prediction, buffer)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'prediction_report_{prediction_id}.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
