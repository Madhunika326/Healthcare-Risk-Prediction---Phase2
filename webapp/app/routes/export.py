"""
Export Routes
PDF and CSV export functionality
"""

from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from io import BytesIO
import csv
from datetime import datetime

export_bp = Blueprint('export', __name__)


@export_bp.route('/predictions/csv')
@login_required
def export_predictions_csv():
    """Export predictions to CSV"""
    predictions = current_user.predictions.all()
    
    # Create CSV
    output = BytesIO()
    writer = csv.writer(output.write)
    
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
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'predictions_{datetime.now().strftime("%Y%m%d")}.csv'
    )


@export_bp.route('/prediction/<int:prediction_id>/pdf')
@login_required
def export_prediction_pdf(prediction_id):
    """Export prediction report to PDF"""
    from app.models.prediction import Prediction
    
    prediction = Prediction.query.filter_by(
        id=prediction_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph('Healthcare Risk Assessment Report', title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # User info
        elements.append(Paragraph(f'<b>Patient:</b> {current_user.get_full_name()}', styles['Normal']))
        elements.append(Paragraph(f'<b>Report Date:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Risk Score
        risk_color = '#28a745' if prediction.risk_category == 'Low' else '#ffc107' if prediction.risk_category == 'Medium' else '#dc3545'
        elements.append(Paragraph(f'<b>Health Risk Score:</b> {prediction.health_risk_score:.2f}', styles['Heading2']))
        elements.append(Paragraph(f'<b>Risk Category:</b> <font color="{risk_color}"><b>{prediction.risk_category}</b></font>', styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Input Features
        elements.append(Paragraph('<b>Assessment Inputs</b>', styles['Heading3']))
        
        data = [
            ['Feature', 'Value'],
            ['Age', f"{prediction.age} years"],
            ['Health Awareness Score', f"{prediction.health_awareness_score}/5"],
            ['Symptom Severity', f"{prediction.symptom_severity}/5"],
            ['Distance to Healthcare', f"{prediction.distance_to_healthcare_km} km"],
            ['Fear of Cost', f"{prediction.fear_of_cost}/1"],
            ['Fear of Hospital', f"{prediction.fear_of_hospital}/1"],
            ['Delay in Seeking Care', f"{prediction.delay_in_seeking_care_days} days"],
            ['Gender', prediction.gender],
            ['Residence', prediction.residence],
            ['Education Level', prediction.education_level],
            ['Income Level', prediction.income_level],
            ['Insurance Status', prediction.insurance_status],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Risk Factors
        elements.append(Paragraph('<b>Key Risk Factors</b>', styles['Heading3']))
        risk_factors = prediction.get_risk_factors()
        
        if risk_factors:
            for factor in risk_factors:
                elements.append(Paragraph(f"• {factor['description']}", styles['Normal']))
        else:
            elements.append(Paragraph('No significant risk factors identified', styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        elements.append(Paragraph('<b>Recommendations</b>', styles['Heading3']))
        recommendations = prediction.get_recommendations()
        
        for rec in recommendations:
            elements.append(Paragraph(f"• {rec}", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'prediction_report_{prediction_id}.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
