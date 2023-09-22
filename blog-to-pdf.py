import requests
import re
import os
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from datetime import datetime

# Fetch webpage content
def fetch_webpage(url):
    response = requests.get(url)
    return response.text

# Custom styles
custom_styles = {
    'body': ParagraphStyle(
        'body',
        parent=getSampleStyleSheet()['BodyText'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        textColor=colors.black
    )
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
def generate_pdf(flowables, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    doc.build(flowables)

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
    generate_pdf(flowables, filename)

    # Monthly report feature
    report_choice = input("Add this to your monthly report? (y/n): ")
    if report_choice.lower() == 'y':
        monthly_filename = f"Monthly_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        if os.path.exists(monthly_filename):
            with open(monthly_filename, "ab") as f:
                f.write(open(filename, "rb").read())
        else:
            generate_pdf(flowables, monthly_filename)

if __name__ == "__main__":
    main()
