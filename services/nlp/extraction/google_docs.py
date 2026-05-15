import re
import os

# To be implemented when auth tokens are set up
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials

def extract_from_google_doc(url: str) -> str:
    """
    Extracts text from a Google Doc URL.
    For the MVP, this raises a configuration error if Google API is not configured.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise ValueError("Google Docs integration is not configured. Missing GOOGLE_CLIENT_ID.")

    # Match standard Google Doc URL format to extract the document ID
    match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError("Invalid Google Doc URL format.")
    
    doc_id = match.group(1)
    
    # Placeholder for actual API call
    # creds = Credentials(token="...") 
    # service = build('docs', 'v1', credentials=creds)
    # document = service.documents().get(documentId=doc_id).execute()
    # return _read_structural_elements(document.get('body').get('content'))
    
    raise NotImplementedError("Google Docs API extraction logic requires a valid OAuth token which is not provided in this context.")

def _read_structural_elements(elements):
    """
    Recursively reads structural elements from Google Docs API response.
    """
    text_content = []
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                if 'textRun' in elem:
                    text_content.append(elem.get('textRun').get('content'))
    return "".join(text_content)
