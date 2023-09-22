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
from urllib.parse import urlparse



toc = False  # Toggle for Table of Contents
cover = False  # Toggle for Cover Page
add_monthly_def = True

def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        if all([parsed_url.scheme, parsed_url.netloc]):
            if parsed_url.scheme in ['http', 'https']:
                return True
        return False
    except ValueError:
        return False

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
        clean_url = f"{author} {title}"
    else:
        clean_url = re.sub(r'[^\w\s]', '', url.split('//')[-1])[:50]
        new_clean_url = input(f"The current filename is '{clean_url}'. Would you like to change it? (y/n): ")
        if new_clean_url.lower() == 'y':
            clean_url = input("Enter the new title: ")

    today_date = datetime.now().strftime("%Y%m%d")
    return f"{today_date} {clean_url}.pdf"

def append_to_monthly_report(article_path, monthly_path, title, author):
    merger = PdfMerger()
    
    if os.path.exists(monthly_path):
        merger.append(monthly_path)

    if cover:
        # Generate cover page for the article
        cover_flowables = [Paragraph(f"Title: {title}", custom_styles['h1']),
                        Spacer(1, 12),
                        Paragraph(f"Author: {author}", custom_styles['h2'])]
        cover_filename = "temp_cover.pdf"
        generate_pdf(cover_flowables, cover_filename)
        
        # Append the cover page and the article to the monthly report
        merger.append(cover_filename)
        merger.append(article_path)
        
        # Save changes
        merger.write(monthly_path)
        merger.close()
        os.remove(cover_filename)  # Remove temp cover file
    else:
        merger.append(article_path)
        merger.write(monthly_path)
        merger.close()

def download_pdf(url, monthly_path):
    if not os.path.exists('articles'):
        os.mkdir('articles')

    response = requests.get(url)
    filename =  create_filename(url) #url.split('/')[-1]
    path = os.path.join('articles', filename)

    with open(path, 'wb') as f:
        f.write(response.content)

    if not (add_monthly_def):
        # Ask if the user wants to add this PDF to the monthly report
        report_choice = input("Add this to your monthly report? (y/n): ")
        if report_choice.lower() == 'y':
            append_to_monthly_report(path, monthly_path, title, author)
    if (add_monthly_def):
        title = filename  # You can also prompt the user to enter a title here
        author = "Unknown"  # And similarly for the author
        append_to_monthly_report(path, monthly_path, title, author)



def main():

    while True:  # Starts the loop

        title=""
        author=""
        monthly_filename = f"Monthly_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        monthly_path = os.path.join('articles', monthly_filename)
        url = input("Enter the URL of the blog: ").strip()

        if not is_valid_url(url):
            print("Invalid URL. Please try again.")
            continue

        if url.lower().endswith('.pdf'):
            download_pdf(url, monthly_path)
        else:

            html_content = fetch_webpage(url)
            flowables = extract_text(html_content)

            if not os.path.exists('articles'):
                os.mkdir('articles')

            filename = create_filename(url)
            path = os.path.join('articles', filename)
            
            generate_pdf(flowables, path)
            if not (add_monthly_def):
                report_choice = input("Add this to your monthly report? (y/n): ")
                if report_choice.lower() == 'y':
                    append_to_monthly_report(path, monthly_path, title, author)
            if add_monthly_def:
                append_to_monthly_report(path, monthly_path, title, author)


        # Ask if the user wants to continue
        continue_choice = input("Do you want to add another file? (y/n): ")
        if continue_choice.lower() != 'y':
            break  # Exits the loop if the user types anything other than 'y'

if __name__ == "__main__":
    main()
