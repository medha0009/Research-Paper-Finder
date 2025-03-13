# Research Paper Finder

A Python tool to find research papers with pharmaceutical/biotech company affiliations using the PubMed API. This tool helps researchers identify papers authored by researchers affiliated with pharmaceutical or biotech companies.

## Code Organization

The project follows a modular structure:

```
research_paper_finder/
├── __init__.py           # Package initialization
├── __main__.py          # Entry point
├── core.py              # Core functionality and ResearchPaperFinder class
├── cli.py               # Command-line interface
├── models/              # Data models and type definitions
├── api/                 # API client for PubMed interactions
└── config/             # Configuration and constants
```

### Key Components:

- **Core Module**: Contains the main `ResearchPaperFinder` class that orchestrates the paper finding process
- **CLI Module**: Provides a user-friendly command-line interface
- **Models**: Defines data structures and type hints
- **API Client**: Handles PubMed API interactions
- **Config**: Stores constants and configuration settings

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (dependency management)
- NCBI API Key (get it from [NCBI](https://www.ncbi.nlm.nih.gov/account/settings/))

### From Test PyPI

```bash
pip install -i https://test.pypi.org/simple/ research-paper-finder
```

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/research-paper-finder
   cd research-paper-finder
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Set up your NCBI API key:
   - Create a `.env` file in the project root
   - Add your API key: `NCBI_API_KEY=your-key-here`

## Usage

### Command-Line Interface

1. Basic search:
   ```bash
   get-papers-list "cancer immunotherapy"
   ```

2. Save results to CSV:
   ```bash
   get-papers-list "cancer therapy" -f results.csv
   ```

3. Limit results and enable debug mode:
   ```bash
   get-papers-list "covid-19 vaccine" -m 50 -d
   ```

### Python Module

```python
from research_paper_finder import ResearchPaperFinder

# Initialize the finder
finder = ResearchPaperFinder(debug=True)

# Search for papers
papers = finder.run(
    query="cancer immunotherapy",
    max_results=100,
    output_file="results.csv"
)
```

## Tools and Libraries Used

### Development Tools

- [Poetry](https://python-poetry.org/) - Dependency management and packaging
- [Black](https://black.readthedocs.io/) - Code formatting
- [mypy](https://mypy.readthedocs.io/) - Static type checking
- [flake8](https://flake8.pycqa.org/) - Code linting
- [isort](https://pycqa.github.io/isort/) - Import sorting

### Key Libraries

- [requests](https://requests.readthedocs.io/) - HTTP library for API calls
- [pandas](https://pandas.pydata.org/) - Data manipulation and CSV handling
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management
- [tqdm](https://tqdm.github.io/) - Progress bar functionality

### APIs

- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) - PubMed API for paper searches

### Development Assistance

This project was developed with the assistance of:
- [Claude](https://www.anthropic.com/claude) - AI language model for code review and documentation
- [Cursor](https://cursor.sh/) - AI-powered IDE

## Features

- Search PubMed for research papers using flexible queries
- Filter papers based on pharmaceutical/biotech company affiliations
- Extract author information and company affiliations
- Save results to CSV or display in console
- Fully typed Python implementation
- Efficient API calls with rate limiting and batch processing
- Robust error handling and input validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality:
   ```bash
   poetry run pytest
   poetry run black .
   poetry run mypy .
   poetry run flake8
   ```
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 