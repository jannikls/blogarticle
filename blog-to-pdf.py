import requests
import re
import os
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from datetime import datetime

import shutil

# Fetch webpage content
def fetch_webpage(url):
    response = requests.get(url)
    return response.text

# Custom styles
custom_styles = {
    'body': ParagraphStyle('body', parent=getSampleStyleSheet()['BodyText'], fontName='Times-Roman', fontSize=12, leading=18, textColor=colors.black),
    'h1': ParagraphStyle('h1', parent=getSampleStyleSheet()['Heading1'], fontName='Times-Roman', fontSize=24, leading=28, textColor=colors.grey),
    'h2': ParagraphStyle('h2', parent=getSampleStyleSheet()['Heading2'], fontName='Times-Roman', fontSize=18, leading=22, textColor=colors.grey),
    'h3': ParagraphStyle('h3', parent=getSampleStyleSheet()['Heading3'], fontName='Times-Roman', fontSize=16, leading=20, textColor=colors.grey),
    'h4': ParagraphStyle('h4', parent=getSampleStyleSheet()['Heading4'], fontName='Times-Roman', fontSize=14, leading=18, textColor=colors.grey),
    'h5': ParagraphStyle('h5', parent=getSampleStyleSheet()['Heading5'], fontName='Times-Roman', fontSize=12, leading=16, textColor=colors.grey),
    'h6': ParagraphStyle('h6', parent=getSampleStyleSheet()['Heading6'], fontName='Times-Roman', fontSize=10, leading=14, textColor=colors.grey)
}

# Unwanted phrases
unwanted_phrases = [
    "Please log in using one of these methods",
    "You are commenting using your",
    "Connecting to %s",
    "Notify me of new comments via email",
    "Notify me of new posts via email",
    "This site uses Akismet to reduce spam"
]

def extract_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for elem in soup.find_all(['script', 'style', 'aside']):
        elem.extract()
    
    # Capture the headline
    headline = soup.find('h1') if soup.find('h1') else soup.find('h2')
    if headline:
        headline_text = headline.get_text()
        flowables = [Paragraph(headline_text, custom_styles['body']), Spacer(1, 24)]
    else:
        flowables = []
    
    main_content = soup.find('main') if soup.find('main') else soup
    for p in main_content.find_all('p'):
        cleaned_text = re.sub(r'[■∆]', '', p.get_text())  # Remove unwanted symbols

        if any(phrase in cleaned_text for phrase in unwanted_phrases):
            continue  # Skip this paragraph

        flowables.append(Paragraph(cleaned_text, custom_styles['body']))
        flowables.append(Spacer(1, 6))
    return flowables


# Generate PDF using ReportLab
def generate_pdf(flowables, filename, folder='articles'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    path = os.path.join(folder, filename)
    doc = SimpleDocTemplate(path, pagesize=letter)
    doc.build(flowables)
    
    return path  # Return path for later use

# Create PDF filename
def create_filename(url):
    today_date = datetime.now().strftime("%Y%m%d")
    clean_url = re.sub(r'[^\w\s]', '', url.split('//')[-1])[:50]
    return f"{today_date}_{clean_url}.pdf"

# Main function
def main():
    url = input("Enter the URL of the blog: ")
    html_content = fetch_webpage(url)
    flowables = extract_text(html_content)
    filename = create_filename(url)
    path = generate_pdf(flowables, filename)

    # Monthly report feature
    report_choice = input("Add this to your monthly report? (y/n): ")
    if report_choice.lower() == 'y':
        monthly_filename = f"Monthly_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        monthly_path = os.path.join('articles', monthly_filename)
        
        if os.path.exists(monthly_path):
            with open(monthly_path, "ab") as f:
                with open(path, "rb") as article_file:
                    f.write(article_file.read())
        else:
            generate_pdf(flowables, monthly_filename)
if __name__ == "__main__":
    main()
