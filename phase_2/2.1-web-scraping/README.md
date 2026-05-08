# Phase 2.1: Web Scraping Infrastructure

## Overview
This module provides the web scraping infrastructure for the Mutual Fund FAQ Assistant project. It includes components for HTTP requests, HTML parsing, PDF extraction, error handling, URL validation, logging, and caching.

## Components

### 1. HTTP Client (`http_client.py`)
Handles HTTP requests with rate limiting, retry logic, and proper headers.

### 2. HTML Parser (`html_parser.py`)
Extracts and cleans content from HTML pages using BeautifulSoup.

### 3. PDF Extractor (`pdf_extractor.py`)
Extracts text and tables from PDF files using PyPDF2 and pdfplumber.

### 4. Error Handler (`error_handler.py`)
Provides error handling and retry logic with exponential backoff.

### 5. URL Validator (`url_validator.py`)
Validates URL format and checks accessibility.

### 6. Logger Configuration (`logger_config.py`)
Configures logging for scraping operations.

### 7. Cache Manager (`cache_manager.py`)
Manages caching of scraped content to avoid redundant requests.

## Installation

Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

See individual module files for usage examples. Each module can be tested independently by running:
```bash
python src/<module_name>.py
```

## Configuration

Default configurations are provided in each module. These can be customized as needed for specific use cases.

## Testing

Each module includes a `__main__` block for basic testing:
```bash
python src/http_client.py
python src/html_parser.py
python src/pdf_extractor.py
python src/error_handler.py
python src/url_validator.py
python src/logger_config.py
python src/cache_manager.py
```

## Deliverables

- All source modules in `src/` directory
- `requirements.txt` for dependencies
- `phase-2.1-deliverables.md` with complete documentation
- This README file
