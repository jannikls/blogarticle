import requests
import re
import os
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from PyPDF2 import PdfMerger
from datetime import datetime

def fetch_webpage(url):
    response = requests.get(url)
    return response.text

custom_styles = {
    'body': ParagraphStyle(
        'body',
        parent=getSampleStyleSheet()['BodyText'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        textColor=colors.black
    ),
    'h1': ParagraphStyle(
        'h1',
        parent=getSampleStyleSheet()['Heading1'],
        fontName='Times-Roman',
        fontSize=24,
        leading=30,
        textColor=colors.black
    ),
    'h2': ParagraphStyle(
        'h2',
        parent=getSampleStyleSheet()['Heading2'],
        fontName='Times-Roman',
        fontSize=20,
        leading=24,
        textColor=colors.black
    ),
    # Add more heading styles here
}

unwanted_phrases = [
    "Please log in using one of these methods",
    "You are commenting using your",
    "Connecting to %s",
    "Notify me of new comments via email",
    "Notify me of new posts via email",
    "This site uses Akismet to reduce spam",
    "■", "∆", "Upgrade to paid", "No posts"
]

unwanted_elements = ['author-box', 'author-info', 'author-details']  # Add known classes or ids for author boxes


def extract_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for elem in soup.find_all(['script', 'style', 'aside']):
        elem.extract()
    
    for elem_class in unwanted_elements:
        for elem in soup.find_all(class_=elem_class):
            elem.extract()

        # If Wikipedia, capture references
    is_wikipedia = 'wikipedia.org' in html_content
    references = []
    if is_wikipedia:
        references_div = soup.find('div', {'class': ['references', 'reflist']})
        if references_div:
            references = references_div.find_all('li')
        
    main_content = soup.find('main') if soup.find('main') else soup
    flowables = []
    
    for elem in main_content.find_all(['p', 'h1', 'h2']):  # Add more tags here
        cleaned_text = re.sub(r'[■∆]', '', elem.get_text())
        
        if any(phrase in cleaned_text for phrase in unwanted_phrases):
            continue
        
        style = custom_styles.get(elem.name, custom_styles['body'])
        flowables.append(Paragraph(cleaned_text, style))
        flowables.append(Spacer(1, 6))

    if is_wikipedia and references:
        flowables.append(Paragraph("References", custom_styles['headline']))
        for ref in references:
            cleaned_text = ref.get_text()
            flowables.append(Paragraph(cleaned_text, custom_styles['body']))

        
    return flowables

def generate_pdf(flowables, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    doc.build(flowables)

def create_filename(url):
    today_date = datetime.now().strftime("%Y%m%d")
    clean_url = re.sub(r'[^\w\s]', '', url.split('//')[-1])[:50]
    return f"{today_date}_{clean_url}.pdf"

def append_to_monthly_report(article_path, monthly_path):
    merger = PdfMerger()
    
    if os.path.exists(monthly_path):
        merger.append(monthly_path)

    merger.append(article_path)
    merger.write(monthly_path)
    merger.close()

def main():
    url = input("Enter the URL of the blog: ")
    html_content = fetch_webpage(url)
    flowables = extract_text(html_content)

    if not os.path.exists('articles'):
        os.mkdir('articles')

    filename = create_filename(url)
    path = os.path.join('articles', filename)
    
    generate_pdf(flowables, path)

    report_choice = input("Add this to your monthly report? (y/n): ")
    if report_choice.lower() == 'y':
        monthly_filename = f"Monthly_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        monthly_path = os.path.join('articles', monthly_filename)
        append_to_monthly_report(path, monthly_path)

if __name__ == "__main__":
    main()
