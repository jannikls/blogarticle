import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# Fetch webpage content
def fetch_webpage(url):
    response = requests.get(url)
    return response.text

# Custom styles
custom_styles = {
    'title': ParagraphStyle(
        'title',
        parent=getSampleStyleSheet()['Heading1'],
        fontName='Times-Roman',
        fontSize=24,
        spaceAfter=12,
        textColor=colors.black
    ),
    'heading': ParagraphStyle(
        'heading',
        parent=getSampleStyleSheet()['Heading2'],
        fontName='Times-Roman',
        fontSize=18,
        spaceAfter=12,
        textColor=colors.grey
    ),
    'body': ParagraphStyle(
        'body',
        parent=getSampleStyleSheet()['BodyText'],
        fontName='Times-Roman',
        fontSize=12,
        spaceAfter=18,
        leading=18,  # 1.5 line spacing
        textColor=colors.black
    ),
}

# Extract text using BeautifulSoup
def extract_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted elements
    for elem in soup.find_all(['script', 'style', 'aside']):
        elem.extract()

    # You might want to be more selective here depending on the structure of the blogs you are scraping.
    main_content = soup.find('main') if soup.find('main') else soup

    # Create flowables list
    flowables = []

    # Add title and headings
    for h in main_content.find_all(['h1', 'h2']):
        flowables.append(Paragraph(h.get_text(), custom_styles['heading']))
        flowables.append(Spacer(1, 12))

    # Add paragraphs
    for p in main_content.find_all('p'):
        text = p.get_text().replace('\u200b', '')  # Remove zero-width spaces
        flowables.append(Paragraph(text, custom_styles['body']))
        flowables.append(Spacer(1, 12))

    return flowables

# Generate PDF using ReportLab
def generate_pdf(flowables):
    doc = SimpleDocTemplate("article.pdf", pagesize=letter)
    doc.build(flowables)

# Main function
def main():
    url = input("Enter the URL of the blog: ")
    html_content = fetch_webpage(url)
    flowables = extract_text(html_content)
    generate_pdf(flowables)

if __name__ == "__main__":
    main()
