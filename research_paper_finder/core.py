"""
Core functionality for the Research Paper Finder.
"""

from typing import List, Dict, Set, Optional, Any, TypedDict, Union, cast
from dataclasses import dataclass
import os
import re
import time
import requests
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from datetime import datetime
import xml.etree.ElementTree as ET

# Load environment variables from .env file
load_dotenv()

class ResearchPaperFinderError(Exception):
    """Base exception for ResearchPaperFinder."""
    pass

class APIError(ResearchPaperFinderError):
    """Raised when there's an error with the PubMed API."""
    pass

class ParseError(ResearchPaperFinderError):
    """Raised when there's an error parsing API response."""
    pass

class ValidationError(ResearchPaperFinderError):
    """Raised when input validation fails."""
    pass

# Type definitions
class PaperInfo(TypedDict):
    """Type definition for paper information."""
    PubmedID: str
    Title: str
    Publication_Date: str
    Non_academic_Authors: str
    Company_Affiliations: str
    Corresponding_Author_Email: str
    All_Authors: str
    All_Affiliations: str

PMID = str

@dataclass
class APIResponse:
    """Type-safe container for API responses."""
    status_code: int
    content: Union[str, bytes]
    url: str

# Constants
MAX_BATCH_SIZE: int = 100
API_RATE_LIMIT_DELAY: float = 0.5

# Pharmaceutical and biotech company keywords for affiliation matching
PHARMA_BIOTECH_KEYWORDS: List[str] = [
    'pharma', 'biotech', 'therapeutics', 'bioscience', 'biopharm',
    'laboratories', 'biopharma', 'pharmaceutical', 'biotechnology',
    'pfizer', 'novartis', 'roche', 'merck', 'johnson & johnson', 'j&j',
    'astrazeneca', 'glaxosmithkline', 'gsk', 'sanofi', 'abbvie',
    'gilead', 'amgen', 'biogen', 'regeneron', 'moderna', 'biontech',
    'vertex', 'alexion', 'genentech', 'boehringer', 'takeda', 'bayer',
    'bristol myers squibb', 'eli lilly', 'novo nordisk', 'inc', 'corp',
    'ltd', 'llc', 'co', 'company', 'corporation'
]

# Academic institution keywords to exclude
ACADEMIC_KEYWORDS: List[str] = [
    'university', 'college', 'school', 'institute of technology',
    'polytechnic', 'academy', 'faculty', 'department of', 'hospital',
    'medical center', 'clinic', 'foundation', 'research institute',
    'national institute', 'laboratory of', 'center for'
]

class ResearchPaperFinder:
    """Class to find research papers with pharmaceutical/biotech company affiliations."""
    
    def __init__(self, api_key: Optional[str] = None, debug: bool = False) -> None:
        """
        Initialize the ResearchPaperFinder.
        
        Args:
            api_key: NCBI API key. If not provided, will look for NCBI_API_KEY environment variable.
            debug: Whether to print debug information
            
        Raises:
            ValidationError: If API key is required but not provided
        """
        self.api_key: Optional[str] = api_key or os.getenv('NCBI_API_KEY')
        self.debug: bool = debug
        
        # Make API key optional
        if not self.api_key:
            if self.debug:
                print("Warning: No API key provided. Requests will be rate-limited.")
        
        if self.debug:
            print(f"Debug mode: ON")
            print(f"API key present: {bool(self.api_key)}")
        
        # PubMed API endpoints
        self.esearch_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.efetch_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        
        # Set up API parameters
        self.base_params: Dict[str, str] = {'api_key': self.api_key} if self.api_key else {}

    def _make_api_request(self, url: str, params: Dict[str, Any]) -> APIResponse:
        """
        Make an API request with error handling, rate limiting, and retries.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            APIResponse object containing response data
            
        Raises:
            APIError: If the API request fails after all retries
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                if self.debug:
                    print(f"API request successful on attempt {attempt + 1}")
                
                return APIResponse(
                    status_code=response.status_code,
                    content=response.content,
                    url=response.url
                )
            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed on attempt {attempt + 1}: {str(e)}"
                if hasattr(e, 'response') and e.response is not None:
                    error_msg += f"\nStatus code: {e.response.status_code}"
                    error_msg += f"\nResponse text: {e.response.text}"
                
                if attempt == max_retries - 1:
                    raise APIError(f"Failed after {max_retries} attempts: {error_msg}") from e
                
                if self.debug:
                    print(f"Retrying in {2 ** attempt} seconds...")
                
                time.sleep(2 ** attempt)  # Exponential backoff

    def validate_query(self, query: str) -> None:
        """
        Validate the search query.
        
        Args:
            query: Search query string
            
        Raises:
            ValidationError: If the query is invalid
        """
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")
        if len(query) > 1000:
            raise ValidationError("Search query is too long (max 1000 characters)")

    def search_papers(self, query: str, max_results: int = 100) -> List[PMID]:
        """
        Search for papers based on the query using PubMed API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to fetch
            
        Returns:
            List of PubMed IDs
            
        Raises:
            ValidationError: If the query is invalid
            APIError: If the API request fails
        """
        self.validate_query(query)
        
        if max_results < 1:
            raise ValidationError("max_results must be greater than 0")
        
        print(f"Searching for papers with query: '{query}'")
        
        search_params: Dict[str, Union[str, int]] = {
            **self.base_params,
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        if self.debug:
            print(f"Search parameters: {search_params}")
        
        response = self._make_api_request(self.esearch_url, search_params)
        
        try:
            search_data = requests.get(response.url).json()
            pmids = cast(List[str], search_data.get('esearchresult', {}).get('idlist', []))
            
            if not pmids:
                print("No results found for the query.")
                return []
            
            print(f"Found {len(pmids)} papers matching the query.")
            
            if self.debug and pmids:
                print(f"First few PMIDs: {pmids[:5]}")
            
            return pmids
            
        except (ValueError, KeyError) as e:
            raise ParseError(f"Failed to parse search results: {str(e)}") from e
    
    def fetch_paper_details(self, pmids: List[PMID]) -> List[PaperInfo]:
        """
        Fetch detailed information for a list of PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of paper details
        """
        if not pmids:
            return []
        
        print(f"Fetching details for {len(pmids)} papers...")
        
        # Split into batches of 100 to avoid API limitations
        batch_size = 100
        all_papers = []
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i+batch_size]
            
            if self.debug:
                print(f"Processing batch {i//batch_size + 1} with {len(batch_pmids)} PMIDs")
            
            fetch_params = {
                **self.base_params,
                'db': 'pubmed',
                'id': ','.join(batch_pmids),
                'retmode': 'xml'
            }
            
            try:
                response = requests.get(self.efetch_url, params=fetch_params)
                response.raise_for_status()
                
                if self.debug:
                    print(f"Fetch response status code: {response.status_code}")
                    print(f"Fetch URL: {response.url}")
                
                # Parse XML response
                root = ET.fromstring(response.content)
                
                # Process each PubmedArticle
                for article in root.findall('.//PubmedArticle'):
                    paper_info = self.parse_pubmed_article(article)
                    if paper_info:
                        all_papers.append(paper_info)
                
                # Respect API rate limits
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching paper details: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response status code: {e.response.status_code}")
                    print(f"Response text: {e.response.text}")
            except ET.ParseError as e:
                print(f"Error parsing XML response: {e}")
        
        print(f"Successfully fetched details for {len(all_papers)} papers.")
        return all_papers
    
    def parse_pubmed_article(self, article: ET.Element) -> Optional[PaperInfo]:
        """
        Parse a PubmedArticle XML element to extract relevant information.
        
        Args:
            article: PubmedArticle XML element
            
        Returns:
            Extracted paper information or None if parsing fails
        """
        try:
            # Extract PubMed ID
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else "N/A"
            
            if self.debug:
                print(f"Processing article with PMID: {pmid}")
            
            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "N/A"
            
            # Extract publication date
            pub_date = "N/A"
            pub_date_elem = article.find('.//PubDate')
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                month_elem = pub_date_elem.find('Month')
                day_elem = pub_date_elem.find('Day')
                
                year = year_elem.text if year_elem is not None else ""
                month = month_elem.text if month_elem is not None else "01"
                day = day_elem.text if day_elem is not None else "01"
                
                # Handle month names
                try:
                    if month.isalpha():
                        month = datetime.strptime(month, '%b').month
                    pub_date = f"{year}-{int(month):02d}-{int(day):02d}" if year else "N/A"
                except (ValueError, AttributeError):
                    pub_date = year if year else "N/A"
            
            # Extract authors and affiliations
            authors = []
            affiliations = []
            non_academic_authors = []
            company_affiliations = set()
            corresponding_email = "N/A"
            
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author_elem in author_list.findall('Author'):
                    # Extract author name
                    last_name = author_elem.find('LastName')
                    fore_name = author_elem.find('ForeName')
                    initials = author_elem.find('Initials')
                    
                    author_name = ""
                    if last_name is not None:
                        author_name = last_name.text
                        if fore_name is not None:
                            author_name = f"{fore_name.text} {author_name}"
                        elif initials is not None:
                            author_name = f"{initials.text} {author_name}"
                    
                    if not author_name:
                        continue
                    
                    authors.append(author_name)
                    
                    # Extract affiliations
                    author_affiliations = []
                    
                    # Check AffiliationInfo elements
                    affiliation_info = author_elem.findall('.//AffiliationInfo')
                    for affil in affiliation_info:
                        affil_text = affil.find('Affiliation')
                        if affil_text is not None and affil_text.text:
                            author_affiliations.append(affil_text.text)
                    
                    # If no AffiliationInfo, check direct Affiliation element
                    if not author_affiliations:
                        affil_elem = author_elem.find('Affiliation')
                        if affil_elem is not None and affil_elem.text:
                            author_affiliations.append(affil_elem.text)
                    
                    # Process affiliations
                    is_non_academic = False
                    author_company_affiliations = []
                    
                    for affiliation in author_affiliations:
                        affiliations.append(affiliation)
                        
                        # Check if affiliation is non-academic
                        if self.is_non_academic_affiliation(affiliation):
                            is_non_academic = True
                            
                            # Extract company name
                            company_name = self.extract_company_name(affiliation)
                            if company_name:
                                author_company_affiliations.append(company_name)
                                company_affiliations.add(company_name)
                    
                    if is_non_academic:
                        non_academic_authors.append(author_name)
                    
                    # Check for corresponding author email
                    if corresponding_email == "N/A":
                        for affil in author_affiliations:
                            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', affil)
                            if email_match:
                                corresponding_email = email_match.group(0)
                                break
            
            # Extract corresponding author email from other locations if not found
            if corresponding_email == "N/A":
                # Check in the article's metadata
                for elem in article.findall('.//*'):
                    if elem.text and '@' in elem.text:
                        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', elem.text)
                        if email_match:
                            corresponding_email = email_match.group(0)
                            break
            
            paper_info = {
                'PubmedID': pmid,
                'Title': title,
                'Publication Date': pub_date,
                'Non-academic Author(s)': '; '.join(non_academic_authors) if non_academic_authors else "N/A",
                'Company Affiliation(s)': '; '.join(company_affiliations) if company_affiliations else "N/A",
                'Corresponding Author Email': corresponding_email,
                'All Authors': '; '.join(authors),
                'All Affiliations': '; '.join(affiliations)
            }
            
            if self.debug:
                if non_academic_authors:
                    print(f"Found non-academic authors for PMID {pmid}: {', '.join(non_academic_authors)}")
                if company_affiliations:
                    print(f"Found company affiliations for PMID {pmid}: {', '.join(company_affiliations)}")
            
            return paper_info
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
    
    def is_non_academic_affiliation(self, affiliation: str) -> bool:
        """
        Check if an affiliation is non-academic.
        
        Args:
            affiliation: Affiliation string to check
            
        Returns:
            True if affiliation is non-academic, False otherwise
        """
        if not affiliation:
            return False
        
        affiliation_lower = affiliation.lower()
        
        # Check if it contains academic keywords
        for keyword in ACADEMIC_KEYWORDS:
            if keyword in affiliation_lower:
                return False
        
        # Check if it contains pharma/biotech keywords
        for keyword in PHARMA_BIOTECH_KEYWORDS:
            if keyword in affiliation_lower:
                return True
        
        return False
    
    def extract_company_name(self, affiliation: str) -> Optional[str]:
        """
        Extract company name from affiliation string.
        
        Args:
            affiliation: Affiliation string
            
        Returns:
            Extracted company name or None if no company name found
        """
        if not affiliation:
            return None
        
        # Common patterns for company names
        patterns = [
            r'([A-Z][A-Za-z0-9\-\s]+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation|Company|Co\.|GmbH|S\.A\.|B\.V\.|N\.V\.))',
            r'([A-Z][A-Za-z0-9\-\s]+(?:Pharma(?:ceuticals)?|Biotech(?:nology)?|Therapeutics|Biosciences?))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, affiliation)
            if match:
                return match.group(1).strip()
        
        # If no match with patterns, try to extract based on keywords
        affiliation_parts = affiliation.split(',')
        for part in affiliation_parts:
            part = part.strip()
            part_lower = part.lower()
            
            for keyword in PHARMA_BIOTECH_KEYWORDS:
                if keyword in part_lower and len(part) < 50:  # Avoid long text blocks
                    return part
        
        return None
    
    def filter_papers_with_pharma_biotech_affiliations(self, papers: List[PaperInfo]) -> List[PaperInfo]:
        """
        Filter papers to include only those with pharmaceutical/biotech affiliations.
        
        Args:
            papers: List of paper information dictionaries
            
        Returns:
            Filtered list of papers
        """
        filtered_papers = []
        
        print("Filtering papers with pharmaceutical/biotech affiliations...")
        for paper in papers:
            if paper['Company Affiliation(s)'] != "N/A":
                filtered_papers.append(paper)
                if self.debug:
                    print(f"Including paper {paper['PubmedID']}: {paper['Title'][:50]}...")
        
        print(f"Found {len(filtered_papers)} papers with pharmaceutical/biotech affiliations")
        return filtered_papers
    
    def save_to_csv(self, papers: List[PaperInfo], output_file: Optional[str] = None) -> None:
        """
        Save paper information to a CSV file or print to console.
        
        Args:
            papers: List of paper information dictionaries
            output_file: Output file path (optional)
            
        Raises:
            ValidationError: If there are issues saving the file
        """
        if not papers:
            print("No papers to save or display.")
            return
        
        # Select only the required columns for output
        columns = [
            'PubmedID', 
            'Title', 
            'Publication Date', 
            'Non-academic Author(s)', 
            'Company Affiliation(s)', 
            'Corresponding Author Email'
        ]
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(papers)
            df = df[columns]  # Select only the required columns
            
            if output_file:
                # Validate file path
                output_dir = os.path.dirname(output_file) or '.'
                if not os.path.exists(output_dir):
                    raise ValidationError(f"Directory does not exist: {output_dir}")
                
                if os.path.exists(output_file):
                    print(f"Warning: File {output_file} already exists and will be overwritten.")
                
                # Save to CSV file
                print(f"Saving {len(papers)} papers to {output_file}...")
                try:
                    df.to_csv(output_file, index=False)
                    print(f"Successfully saved to {output_file}")
                except (IOError, PermissionError) as e:
                    raise ValidationError(f"Failed to save file {output_file}: {str(e)}")
            else:
                # Print to console
                print("\nResults:")
                print("=" * 80)
                print(df.to_string())
                print("=" * 80)
                
        except pd.errors.EmptyDataError:
            raise ValidationError("No data to save")
        except Exception as e:
            raise ValidationError(f"Unexpected error while saving data: {str(e)}")
    
    def run(self, query: str, max_results: int = 100, output_file: Optional[str] = None) -> List[PaperInfo]:
        """
        Run the complete paper finding process.
        
        Args:
            query: Search query
            max_results: Maximum number of results to fetch
            output_file: Output file path (optional)
            
        Returns:
            List of papers with pharmaceutical/biotech affiliations
        """
        if self.debug:
            print(f"Starting search with query: '{query}'")
            print(f"Max results: {max_results}")
            print(f"Output file: {output_file if output_file else 'console'}")
        
        pmids = self.search_papers(query, max_results)
        if not pmids:
            print("No papers found matching the query.")
            return []
        
        papers = self.fetch_paper_details(pmids)
        print("Filtering papers to include only pharmaceutical/biotech affiliations...")
        filtered_papers = self.filter_papers_with_pharma_biotech_affiliations(papers)
        if filtered_papers:
            print(f"Found {len(filtered_papers)} papers with pharmaceutical/biotech affiliations")
            self.save_to_csv(filtered_papers, output_file)
        else:
            print("No papers found with pharmaceutical/biotech affiliations.")
        return filtered_papers 