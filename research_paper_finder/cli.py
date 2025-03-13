"""
Command-line interface for the Research Paper Finder.
"""

import sys
from typing import Optional, List, NoReturn, Dict, Set, Any, TypedDict, Union, cast
import argparse
from .core import ResearchPaperFinder
from dataclasses import dataclass

# Custom types for better type safety
PMID = str
PaperInfo = Dict[str, str]

@dataclass
class PaperInfo:
    pubmed_id: str
    title: str
    publication_date: str
    non_academic_authors: List[str]
    company_affiliations: List[str]
    corresponding_email: str
    all_authors: List[str]
    all_affiliations: List[str]

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments. Defaults to None (sys.argv).
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Find research papers with pharmaceutical/biotech company affiliations using PubMed.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('query', help='Search query for research papers (supports PubMed query syntax)')
    parser.add_argument('-a', '--api-key', help='NCBI API key (if not set in .env file)')
    parser.add_argument('-m', '--max-results', type=int, default=100, 
                        help='Maximum number of results to fetch')
    parser.add_argument('-f', '--file', dest='output', 
                        help='Output CSV file path. If not provided, results will be printed to console')
    parser.add_argument('-d', '--debug', action='store_true', 
                        help='Print debug information during execution')
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the command-line interface.
    
    Args:
        args: Command-line arguments. Defaults to None (sys.argv).
        
    Returns:
        Exit code
    """
    try:
        # Get user input
        print("\n=== Research Paper Finder ===")
        query = input("Enter your search query: ")
        max_results = input("Enter maximum number of results (default 100): ").strip()
        max_results = int(max_results) if max_results else 100
        
        output_choice = input("Do you want to save results to a CSV file? (y/n): ").lower().strip()
        output_file = None
        if output_choice == 'y':
            output_file = input("Enter the output file name (e.g., papers.csv): ").strip()
            if not output_file.endswith('.csv'):
                output_file += '.csv'
        
        debug_mode = input("Enable debug mode? (y/n): ").lower().strip() == 'y'
        
        # Create finder instance
        finder = ResearchPaperFinder(debug=debug_mode)
        
        # Run the search
        print("\nSearching for papers...")
        finder.run(query, max_results, output_file)
        
        return 0
    except ValueError as e:
        print(f"Error: Invalid number for maximum results. Please enter a valid number.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if debug_mode:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main()) 

class ResearchPaperFinderError(Exception):
    """Base exception for ResearchPaperFinder."""
    pass

class APIError(ResearchPaperFinderError):
    """Raised when there's an error with the PubMed API."""
    pass

class ParseError(ResearchPaperFinderError):
    """Raised when there's an error parsing API response."""
    pass

class PubMedClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
    def search(self, query: str, max_results: int) -> List[PMID]:
        pass
        
    def fetch_details(self, pmids: List[PMID]) -> List[PaperInfo]:
        pass 