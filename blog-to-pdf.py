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


toc = True  # Toggle for Table of Contents
cover = False  # Toggle for Cover Page
toc_entries = []  # Holds Table of Contents entries


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

    # Function to scrape title and author
def scrape_title_author(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = soup.title.string if soup.title else "Unknown Title"
    # Modify the selector as per the HTML structure of the webpage
    author_tag = soup.find("div", {"class": "author-box"})
    author = author_tag.text if author_tag else "Unknown Author"
    
    return title, author.strip()

def create_filename(url):
    today_date = datetime.now().strftime("%Y%m%d")
    clean_url = re.sub(r'[^\w\s]', '', url.split('//')[-1])[:50]
    return f"{today_date}_{clean_url}.pdf"

def append_to_monthly_report(article_path, monthly_path, title, author):
    global toc_entries  # Make it accessible for modification
    merger = PdfMerger()
    
    if os.path.exists(monthly_path):
        merger.append(monthly_path)

    start_page = merger.getNumPages()  # Page where the article starts
   # Append Cover Page
    if cover:
        cover_flowables = [
            Paragraph(f"Title: {title}", custom_styles['h1']),
            Spacer(1, 12),
            Paragraph(f"Author: {author}", custom_styles['h2'])
        ]
        cover_filename = "temp_cover.pdf"
        generate_pdf(cover_flowables, cover_filename)
        merger.append(cover_filename)
        os.remove(cover_filename)

    # Append Article
    merger.append(article_path)
    end_page = merger.getNumPages()  # Page where the article ends

    # Update ToC
    if toc:
        toc_entries.append({
            'title': title,
            'start_page': start_page,
            'end_page': end_page
        })

    # Generate and insert ToC if it's enabled
    if toc:
        toc_flowables = []
        for entry in toc_entries:
            toc_text = f"{entry['title']} - Page {entry['start_page']}"
            toc_flowables.append(Paragraph(toc_text, custom_styles['body']))
            toc_flowables.append(Spacer(1, 12))

        toc_filename = "temp_toc.pdf"
        generate_pdf(toc_flowables, toc_filename)

        # Reconstruct with ToC
        with open(monthly_path, "rb") as f:
            reader = PdfFileReader(f)
            writer = PdfFileWriter()

            # Add existing pages
            for i in range(reader.getNumPages()):
                writer.addPage(reader.getPage(i))

            # Add ToC
            reader = PdfFileReader(toc_filename)
            for i in range(reader.getNumPages()):
                writer.addPage(reader.getPage(i))

        with open(monthly_path, "wb") as f:
            writer.write(f)

        os.remove(toc_filename)

    # Save changes
    merger.write(monthly_path)
    merger.close()

def main():

    title=""
    author=""
    url = input("Enter the URL of the blog: ")
    html_content = fetch_webpage(url)
    flowables = extract_text(html_content)

    if not os.path.exists('articles'):
        os.mkdir('articles')

    if (toc | cover):
    # Scrape title and author
        title, author = scrape_title_author(html_content)
        # Prompt user for confirmation or modification
        print(f"Scraped Title: {title}")
        print(f"Scraped Author: {author}")
        change_title = input("Would you like to change the title? (y/n): ")
        if change_title.lower() == 'y':
            title = input("Enter the new title: ")
        change_author = input("Would you like to change the author? (y/n): ")
        if change_author.lower() == 'y':
            author = input("Enter the new author: ")

    filename = create_filename(url)
    path = os.path.join('articles', filename)
    
    generate_pdf(flowables, path)

    report_choice = input("Add this to your monthly report? (y/n): ")
    if report_choice.lower() == 'y':
        monthly_filename = f"Monthly_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        monthly_path = os.path.join('articles', monthly_filename)
        append_to_monthly_report(path, monthly_path, title, author)

if __name__ == "__main__":
    main()
