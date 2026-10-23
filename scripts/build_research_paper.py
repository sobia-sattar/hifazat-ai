"""Render the checked-in manuscript; no claims or metrics generated here."""
from pathlib import Path
from html import escape
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'output/pdf/BullyLens_X_Research_Paper.pdf'
output.parent.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyPaper', fontName='Times-Roman', fontSize=10.5, leading=14,
                          spaceAfter=8, alignment=4))
styles.add(ParagraphStyle(name='PaperTitle', fontName='Helvetica-Bold', fontSize=21, leading=25,
                          textColor=colors.HexColor('#123859'), spaceAfter=14))
styles.add(ParagraphStyle(name='PaperH2', fontName='Helvetica-Bold', fontSize=12, leading=16,
                          textColor=colors.HexColor('#123859'), spaceBefore=13, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name='PaperH3', fontName='Helvetica-Bold', fontSize=10.5, leading=14,
                          spaceBefore=8, spaceAfter=6, keepWithNext=True))
styles.add(ParagraphStyle(name='CellPaper', fontName='Helvetica', fontSize=8.5, leading=11))
styles.add(ParagraphStyle(name='FigureCaption', fontName='Helvetica', fontSize=9, leading=12, spaceAfter=12))


def footer(canvas, doc):
    canvas.saveState()
    w,h = A4
    canvas.setStrokeColor(colors.HexColor('#bfccd8'))
    canvas.line(48, 40, w-48, 40)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#466078'))
    canvas.drawString(48, 27, 'BullyLens-X | Research Paper')
    canvas.drawRightString(w-48, 27, str(doc.page))
    canvas.restoreState()


lines = (ROOT / 'research/paper/BullyLens_X_Research_Paper.md').read_text(encoding='utf-8-sig').splitlines()
story=[]
i=0
while i < len(lines):
    line=lines[i].strip()
    if not line:
        i+=1
        continue
    figure = re.fullmatch(r'!\[(.*?)\]\((.*?)\)', line)
    if figure:
        caption, relative = figure.groups()
        path = ROOT / 'research/paper' / relative
        width,height = ImageReader(str(path)).getSize()
        image = Image(str(path),width=499,height=499*height/width)
        story.append(KeepTogether([Spacer(1,8),image,Spacer(1,6),Paragraph(escape(caption),styles['FigureCaption'])]))
        i+=1
        continue
    if line.startswith('|'):
        rows=[]
        while i < len(lines) and lines[i].startswith('|'):
            cells=[s.strip() for s in lines[i].strip('|').split('|')]
            if not all(set(c) <= set('-: ') for c in cells):
                rows.append([Paragraph(escape(c),styles['CellPaper']) for c in cells])
            i+=1
        widths=[220,139,140] if len(rows[0])==3 else None
        table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f0f6')),
                                  ('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),
                                  ('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#8099ad')),
                                  ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dce4eb'))]))
        story.extend([table,Spacer(1,12)])
        continue
    if line.startswith('### '):
        style,text='PaperH3',line[4:]
    elif line.startswith('## '):
        style,text='PaperH2',line[3:]
    elif line.startswith('# '):
        style,text='PaperTitle',line[2:]
    else:
        style,text='BodyPaper',line
    story.append(Paragraph(escape(text),styles[style]))
    i+=1
doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=46,bottomMargin=54,
                      title='BullyLens-X: Human-Supervised Harmful-Comment Detection',author='BullyLens-X project report')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(output)
