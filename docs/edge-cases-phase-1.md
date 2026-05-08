# Edge Cases: Phase 1 - Corpus Definition and Data Collection

## Overview
This document outlines potential edge cases and mitigation strategies for Phase 1: Corpus Definition and Data Collection.

---

## Edge Cases

### 1.1 URL Accessibility Issues

#### Edge Case: URLs Become Inaccessible
- **Scenario**: One or more of the 5 selected URLs become unavailable (404, 403, or server errors)
- **Impact**: Cannot scrape content from affected URLs, reducing corpus size
- **Mitigation**:
  - Implement URL health check before scraping
  - Add retry logic with exponential backoff (3-5 attempts)
  - Archive cached content locally for backup
  - Monitor URLs periodically for availability
  - Have fallback URLs from official AMC website as contingency

#### Edge Case: URLs Redirect to Different Pages
- **Scenario**: URLs redirect to different pages or login-required pages
- **Impact**: Content extraction fails or retrieves incorrect content
- **Mitigation**:
  - Follow redirects with limit (max 5 redirects)
  - Validate final URL matches expected pattern
  - Check for authentication requirements
  - Handle different HTTP status codes appropriately

#### Edge Case: Dynamic Content Loading
- **Scenario**: Content loads dynamically via JavaScript after initial page load
- **Impact**: Basic HTML scraping fails to capture content
- **Mitigation**:
  - Use headless browser (Selenium/Playwright) for dynamic pages
  - Wait for content to load before extraction
  - Identify API endpoints that serve dynamic content
  - Fallback to static HTML if JavaScript fails

### 1.2 Content Quality Issues

#### Edge Case: Inconsistent Data Structure Across URLs
- **Scenario**: Each URL has different HTML structure for presenting fund information
- **Impact**: Scraping logic needs to be URL-specific, increasing complexity
- **Mitigation**:
  - Create URL-specific scraping templates
  - Use CSS selectors that are robust to structural changes
  - Implement fallback extraction strategies
  - Document structure differences for each URL

#### Edge Case: Missing Critical Information
- **Scenario**: Some URLs lack essential information (expense ratio, NAV, holdings)
- **Impact**: System cannot answer queries about missing data
- **Mitigation**:
  - Conduct initial audit of each URL's content
  - Identify gaps early and seek alternative sources
  - Clearly document which information is available per URL
  - Provide graceful responses for unavailable information

#### Edge Case: Outdated Information
- **Scenario**: URLs contain outdated data (old NAV, discontinued schemes)
- **Impact**: System provides incorrect information to users
- **Mitigation**:
  - Implement timestamp tracking for scraped content
  - Schedule regular content refresh (daily/weekly)
  - Add data freshness indicators to responses
  - Validate critical data points against external sources

### 1.3 Data Format Issues

#### Edge Case: Tables with Complex Structures
- **Scenario**: Fund data presented in nested or merged tables
- **Impact**: Table extraction fails or produces incorrect data
- **Mitigation**:
  - Use specialized table extraction libraries (pandas, camelot)
  - Implement manual table parsing for complex structures
  - Validate extracted table data against expected schema
  - Fallback to manual data entry for critical tables

#### Edge Case: Images Containing Data
- **Scenario**: Critical data presented as images (charts, graphs)
- **Impact**: Text extraction cannot capture image-based data
- **Mitigation**:
  - Use OCR (Tesseract) for text extraction from images
  - Prioritize text-based data sources
  - Document data available only in images
  - Consider manual transcription for critical image data

#### Edge Case: PDF Documents Embedded in Pages
- **Scenario**: Key information available only in downloadable PDFs
- **Impact**: HTML scraper misses PDF content
- **Mitigation**:
  - Detect and extract PDF links from pages
  - Implement PDF parsing pipeline
  - Handle scanned PDFs with OCR
  - Combine HTML and PDF content in corpus

### 1.4 Scheme Categorization Issues

#### Edge Case: Scheme Category Ambiguity
- **Scenario**: A scheme fits multiple categories (e.g., flexi-cap vs. large-cap)
- **Impact**: Incorrect categorization affects query routing
- **Mitigation**:
  - Use official AMFI categorization as source of truth
  - Document categorization rationale
  - Allow multiple category tags per scheme
  - Cross-reference with multiple sources

#### Edge Case: Scheme Name Variations
- **Scenario**: Same scheme referred to by different names across sources
- **Impact**: Difficulty in consolidating data for same scheme
- **Mitigation**:
  - Create canonical name mapping
  - Use scheme ISIN for unique identification
  - Implement name normalization logic
  - Maintain alias list for each scheme

### 1.5 Legal and Compliance Issues

#### Edge Case: Copyrighted Content
- **Scenario**: URLs contain copyrighted material with usage restrictions
- **Impact**: Legal risk in using content
- **Mitigation**:
  - Verify terms of use for each source
  - Use only publicly available factual data
  - Add attribution to sources
  - Consult legal team if uncertain

#### Edge Case: Terms of Service Violations
- **Scenario**: Scraping violates website terms of service
- **Impact**: IP blocking or legal action
- **Mitigation**:
  - Review terms of service before scraping
  - Implement rate limiting to respect server load
  - Use appropriate user-agent headers
  - Consider official API if available

### 1.6 Data Volume Issues

#### Edge Case: Insufficient Content for Meaningful Retrieval
- **Scenario**: 5 URLs provide very limited content (few hundred words total)
- **Impact**: RAG system cannot provide comprehensive answers
- **Mitigation**:
  - Conduct content audit before finalizing corpus
  - Estimate content volume per URL
  - Set minimum content threshold (e.g., 5000 words per scheme)
  - Expand corpus if content is insufficient

#### Edge Case: Content Overlap Between URLs
- **Scenario**: Multiple URLs contain redundant or duplicate information
- **Impact**: Redundant embeddings, wasted storage, potential confusion
- **Mitigation**:
  - Implement deduplication logic
  - Use similarity scores to identify duplicates
  - Keep most authoritative source for duplicate content
  - Track content overlap metrics

### 1.7 Source Attribution Issues

#### Edge Case: URLs Change Over Time
- **Scenario**: URL structure changes, breaking source links
- **Impact**: Source citations become invalid
- **Mitigation**:
  - Use permanent URLs when available
  - Implement URL redirect handling
  - Archive original URLs and content
  - Update source links when changes detected

#### Edge Case: Multiple Sources for Same Information
- **Scenario**: Same fact appears in multiple URLs
- **Impact**: Unclear which source to cite
- **Mitigation**:
  - Define source priority hierarchy
  - Prefer official AMC website over aggregators
  - Track all sources for each fact
  - Allow source selection based on recency/authority

---

## Testing Strategy

### Pre-Scraping Validation
- Test URL accessibility
- Verify content structure
- Check for authentication requirements
- Estimate content volume

### Scraping Monitoring
- Log failed scrapes with error details
- Track content extraction success rate
- Monitor response times
- Alert on repeated failures

### Content Validation
- Validate extracted data schema
- Check for missing critical fields
- Verify data format consistency
- Sample manual verification

---

## Contingency Plans

### If URL Becomes Permanently Unavailable
1. Use cached/archived content if available
2. Seek alternative official source for same scheme
3. Document unavailability in system
4. Update user-facing content to reflect gap

### If Content Quality is Insufficient
1. Expand corpus with additional URLs
2. Seek alternative data sources
3. Reduce scope of queries to available content
4. Clearly communicate limitations to users

### If Legal Issues Arise
1. Immediately stop scraping from affected source
2. Consult legal team
3. Seek alternative data sources
4. Remove affected content from corpus
