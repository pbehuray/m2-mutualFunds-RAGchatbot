# Phase-Wise Architecture: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
This document outlines the detailed phase-wise architecture for building a Retrieval-Augmented Generation (RAG)-based FAQ assistant for mutual fund schemes. The system will answer objective, verifiable queries using information exclusively from official public sources.

---

## Phase 1: Corpus Definition and Data Collection

### 1.1 AMC Selection
- **Objective**: Select one Asset Management Company (AMC) as the primary data source
- **Activities**:
  - Research and evaluate major AMCs (HDFC, ICICI, SBI, Axis, Kotak, etc.)
  - Assess data availability and quality of online documentation
  - Select AMC with comprehensive, accessible documentation
- **Deliverable**: Selected AMC with justification

### 1.2 Mutual Fund Scheme Selection
- **Objective**: Choose 3-5 mutual fund schemes ensuring category diversity
- **Scheme Categories**:
  - Large-cap funds
  - Flexi-cap funds
  - ELSS (Equity Linked Savings Scheme)
  - Debt funds
  - Index funds
- **Activities**:
  - Analyze scheme performance and popularity
  - Ensure representation across different risk profiles
  - Verify availability of official documentation
- **Deliverable**: List of 3-5 selected schemes with categories

### 1.3 URL Collection and Curation
- **Objective**: Use the selected URLs as the corpus for the project
- **Selected AMC**: HDFC Mutual Fund
- **Selected Schemes and URLs**:
  1. **HDFC Mid-Cap Fund (Direct Growth)**
     - URL: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
     - Category: Mid-cap equity fund
  2. **HDFC Equity Fund (Direct Growth)**
     - URL: https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
     - Category: Large-cap equity fund
  3. **HDFC Focused Fund (Direct Growth)**
     - URL: https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth
     - Category: Focused equity fund
  4. **HDFC ELSS Tax Saver Fund (Direct Plan Growth)**
     - URL: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
     - Category: ELSS (Equity Linked Savings Scheme)
  5. **HDFC Large-Cap Fund (Direct Growth)**
     - URL: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
     - Category: Large-cap equity fund
- **Note**: These 5 URLs are the complete corpus for this project. No additional URLs will be collected.
- **Activities**:
  - Validate URLs for accessibility and stability
  - Categorize content by scheme and fund type
- **Deliverable**: Validated corpus of 5 URLs

---

## Phase 2: Data Ingestion and Processing Pipeline

**Automated Refresh Strategy (GitHub Actions)**:
- **Schedule**: Cron-based trigger (e.g., `0 0 * * 0` for weekly Sunday midnight UTC)
- **Workflow**: Sequential execution of Phase 2.1 → 2.2 → 2.3 → 3.3 pipelines
- **Condition**: Compare content checksums to avoid unnecessary re-processing if data unchanged
- **Storage**: Store generated artifacts (raw_html, extracted_json, chunked_json, vector_db) as workflow artifacts or push to dedicated data branch
- **Failure Handling**: Email/Slack notification on pipeline failure; preserve last known good artifacts
- **Manual Trigger**: Support `workflow_dispatch` for on-demand data refresh

### 2.1 Web Scraping Infrastructure
- **Objective**: Build infrastructure to fetch and extract content from official sources
- **Subphase Activities**:
  - Set up HTTP client with proper headers and rate limiting
  - Implement HTML parser (BeautifulSoup / lxml)
  - Implement PDF extractor (PyPDF2 / pdfplumber) for downloadable documents
  - Add error handling and retry mechanism
  - Implement URL validation and accessibility checker
  - Add logging for failed fetches
  - Implement caching to avoid redundant requests
- **Components**:
  - HTTP client module
  - HTML parser module
  - PDF extractor module
  - Error handler
  - URL validator
  - Logger
  - Cache manager
- **Deliverables**:
  - Functional web scraping module
  - HTTP client configuration
  - HTML parser implementation
  - PDF extractor implementation
  - Error handling and retry logic
  - URL validation utility
  - Logging configuration
  - Caching implementation

### 2.2 Content Extraction and Cleaning
- **Objective**: Extract clean, structured text from scraped documents
- **Subphase Activities**:
  - Implement text extraction from HTML (removing navigation, ads, footers)
  - Implement text extraction from PDF files
  - Implement noise removal (special characters, extra whitespace)
  - Implement header/footer identification and removal
  - Implement table extraction and formatting
  - Implement text cleaning utilities
  - Handle different document formats consistently
  - Preserve document structure (headings, lists, tables)
  - Remove boilerplate content
- **Components**:
  - HTML text extractor
  - PDF text extractor
  - Noise remover
  - Header/footer detector
  - Table extractor
  - Text cleaner
  - Document structure preserver
  - Boilerplate remover
- **Deliverables**:
  - Clean text extraction pipeline
  - HTML extraction module
  - PDF extraction module
  - Text cleaning utilities
  - Table extraction module
  - Boilerplate removal implementation

### 2.3 Document Chunking Strategy
- **Objective**: Split documents into manageable chunks for embedding and retrieval
- **Subphase Activities**:
  - Implement semantic chunking algorithm based on sections and headers
  - Configure chunk size: 500-1000 tokens (optimized for embedding models) - *adjusted for actual data*
  - Configure overlap: 50-100 tokens between chunks to maintain context
  - Implement metadata preservation (source URL, scheme name, document type, timestamp)
  - Add metadata tagging to each chunk
  - Validate chunk quality and coherence
  - Test chunking with sample documents
- **Components**:
  - Semantic chunker
  - Chunk size configurator
  - Overlap manager
  - Metadata tagger
  - Chunk validator
  - Chunk quality checker
- **Implementation Reality**:
  - Processed 5 extracted JSON files from Phase 2.2
  - Limited extracted content: ~18,295 characters total (avg 3,659 per document)
  - Generated 20 chunks total (3-5 chunks per document) - much fewer than original strategy
  - Chunk configuration: 800 tokens target, 100 tokens overlap, 100 tokens minimum
  - Actual chunk sizes are smaller than 500-1000 tokens due to limited source content
  - Metadata includes: chunk_id, scheme_name, source_file, chunk_index, total_chunks, chunk_length, word_count, created_at, source_url, document_type, section_header, has_numbers, has_currency, has_percentage, sentence_count, avg_sentence_length, validation status, quality_score
  - Validation rules: min 50 chars, max 2000 chars, min 10 words, max 500 words
  - Quality scores: 0.80-0.85 average (good despite strict validation)
  - Output: chunked JSON files in `scraped-data/chunked_json/`
  - **Note**: Original 500-1000 token strategy not achievable with current extracted content volume; chunking adapts to available content
- **Deliverables**:
  - Document chunker with metadata preservation
  - Chunking algorithm implementation
  - Metadata tagging system
  - Chunk validation utilities
  - Chunk quality metrics
  - 20 chunked JSON files with metadata

---

## Phase 3: Vector Database and Embedding Layer

### 3.1 Embedding Model Selection
- **Objective**: Select appropriate embedding model for semantic search
- **Options**:
  - OpenAI text-embedding-3-small/large
  - HuggingFace sentence-transformers (all-MiniLM-L6-v2, all-mpnet-base-v2)
  - Local models for cost efficiency
- **Selection Criteria**:
  - Performance on financial domain
  - Inference latency
  - Cost considerations
  - Model size and deployment constraints
- **Deliverable**: Selected embedding model with justification

### 3.2 Vector Database Setup
- **Objective**: Implement vector storage for efficient similarity search
- **Options**:
  - Pinecone (managed service)
  - Weaviate (open-source/self-hosted)
  - ChromaDB (lightweight, local)
  - FAISS (Meta's library)
- **Architecture**:
  - Collection/namespace per mutual fund scheme
  - Index configuration (HNSW for approximate nearest neighbor)
  - Metadata filtering capabilities
  - Backup and recovery strategy
- **Activities**:
  - Set up vector database instance
  - Configure indexes and collections
  - Implement connection pool
  - Add monitoring and logging
- **Deliverable**: Configured vector database with schema

### 3.3 Embedding Generation and Indexing
- **Objective**: Generate embeddings for all document chunks and index them
- **Pipeline**:
  - Batch processing of chunks
  - Embedding generation with error handling
  - Indexing with metadata
  - Progress tracking and logging
- **Activities**:
  - Implement embedding generation pipeline
  - Handle rate limits and API quotas
  - Implement batch processing
  - Validate embedding quality
- **Deliverable**: Fully indexed vector database with all document chunks

---

## Phase 4: Retrieval System

### 4.1 Query Processing
- **Objective**: Process user queries for effective retrieval
- **Components**:
  - Query normalization (lowercase, remove special characters)
  - Query embedding generation (using same model as documents)
- **Implementation Reality** (Small Corpus - 20 chunks):
  - **Skip**: Query expansion (unnecessary for small corpus)
  - **Skip**: Spell-check (simple normalization sufficient)
  - **Skip**: Intent detection (all queries are factual for this use case)
- **Activities**:
  - Implement query preprocessing pipeline (basic normalization)
  - Embed query using BAAI/bge-small-en-v1.5
- **Deliverable**: Query processing module

### 4.2 Similarity Search
- **Objective**: Retrieve relevant document chunks based on query
- **Algorithm**:
  - Vector similarity search (cosine similarity) using ChromaDB HNSW
  - Top-k retrieval (k=5-10, increased from 5 due to small corpus)
- **Implementation Reality** (Small Corpus - 20 chunks):
  - **Skip**: Hybrid search (keyword matching unnecessary with 20 chunks)
  - **Skip**: Re-ranking (overkill for 20 chunks)
  - **Include**: Metadata filtering by scheme_name for fund-specific queries
  - **Include**: Metadata filtering by content type (has_numbers, has_percentage)
- **Activities**:
  - Implement similarity search with ChromaDB
  - Add metadata filtering (by scheme name)
  - Return similarity scores for transparency
  - Return top 5-10 results
- **Deliverable**: Optimized retrieval system

### 4.3 Source Attribution
- **Objective**: Ensure every response has a single, clear source link
- **Strategy**:
  - Track source URL for each retrieved chunk
  - Return source_file and chunk_id from metadata
  - Format source citation consistently
- **Implementation Reality** (Small Corpus - 20 chunks):
  - Source is always the corpus HTML file (tracked in metadata)
  - No need for source URL validation (static corpus)
  - Simple citation format: "Source: {source_file}"
- **Activities**:
  - Implement source tracking in retrieval pipeline
  - Create citation formatting utility
- **Deliverable**: Source attribution module

---

## Phase 5: Reasoning & Guardrails (Orchestrator)

**Purpose**: Turn query + retrieved chunks into a compliant, ≤ 3-sentence answer with URL policy enforced before anything is returned.

### 5.1 PII Detection
- **Objective**: Detect personally identifiable information in user messages
- **PII Types to Detect**:
  - PAN (Permanent Account Number)
  - Aadhaar number
  - Email addresses
  - Phone numbers
  - OTP (One-Time Passwords)
  - Other sensitive personal identifiers
- **Components**:
  - Regex-based PII detectors
  - PII blocking logic
- **Behavior**:
  - If PII detected → use `pii_block` template (NO URL)
  - Block processing and refuse immediately
- **Deliverable**: PII detection module with blocking logic

### 5.2 Intent Classification
- **Objective**: Classify user query intent to determine response strategy
- **Intent Categories**:
  - **Factual**: Objective questions about fund facts (expense ratio, returns, holdings)
  - **Advisory**: Requests for investment advice, recommendations
  - **Comparison**: Comparing funds (which is better)
  - **Prediction**: Future performance questions
- **Components**:
  - Intent classifier (keyword-based or lightweight model)
  - Refusal composer for non-factual intents
- **Behavior**:
  - Factual → Proceed to retrieval
  - Advisory/Comparison/Prediction → Use refusal template with ONE whitelisted Groww URL
- **Deliverable**: Intent classification module with refusal handling

### 5.3 Confidence Thresholding
- **Objective**: Ensure sufficient evidence before answering
- **Metrics**:
  - Similarity score threshold (τ)
  - Non-empty retrieval check
- **Behavior**:
  - If confidence < τ or empty retrieval → use `dont_know_without_link` template (NO URL)
  - Ask user to name a specific scheme
- **Deliverable**: Confidence evaluation module

### 5.4 Answer Generation (Groq + Extractive)
- **Objective**: Generate compliant answers from retrieved chunks
- **Generation Stack**:
  - **Primary**: Groq via OpenAI-compatible API (if GROQ_API_KEY set)
  - **Fallback**: Extractive synthesis (build from top chunk, ≤ 3 sentences)
- **Groq Mode** (Primary):
  - Low temperature for deterministic output
  - Returns answer body only (Source/Last updated appended in code)
  - On API failure or empty body → extractive fallback
- **Extractive Mode** (Fallback):
  - Build body from top reranked chunk only
  - First ≤ 3 sentences
  - Strip any embedded URLs from chunk text
  - Append `Source: <citation_url>` line
  - Append `Last updated from sources: <date>` line
- **Deliverable**: Answer generation module with Groq/extractive modes

### 5.5 URL Policy Enforcement
- **Objective**: Ensure exactly one whitelisted URL in responses (or zero per policy)
- **URL Policy Rules**:
  - **PII block**: ZERO URLs (no URL for queries with personal information)
  - **Don't know / low confidence**: ZERO URLs (no URL when answer not known)
  - **Non-factual intent refusal**: ONE whitelisted Groww URL from sources.yaml
  - **Successful factual answer**: ONE citation source_url from top chunk (must be whitelisted)
- **Components**:
  - URL whitelist (sources.yaml)
  - URL count validator
  - URL whitelist validator
- **Deliverable**: URL policy enforcement module

### 5.6 Post-Processing Checks
- **Objective**: Hard deterministic checks before returning response
- **Checks**:
  - Route-aware URL count (PII/don't-know = 0, factual = 1)
  - Sentence count ≤ 3 (before Source line)
  - No banned tokens (recommend, should invest, better than, will outperform)
  - Footer present on factual path: `Last updated from sources: <YYYY-MM-DD>`
- **Fallback**:
  - If post-checks fail → use `safe_template` with one whitelisted link
- **Deliverable**: Post-processing validation module

### 5.7 Decision Flow
```
User Query
    ↓
PII Detected? → YES → pii_block template (NO URL)
    ↓ NO
Intent Classification
    ↓
Factual? → NO → Refusal with ONE whitelisted URL
    ↓ YES
Retrieval (Phase 4)
    ↓
Confidence ≥ τ & non-empty? → NO → dont_know_without_link (NO URL)
    ↓ YES
Generate Answer (Groq or Extractive)
    ↓
Post-Processing Checks → FAIL → safe_template
    ↓ PASS
Return Answer
```

---

## Phase 6: API Layer

### 6.1 API Design
- **Objective**: Design RESTful API for the FAQ assistant
- **Endpoints**:
  - `POST /api/query` - Submit a query and get response
  - `GET /api/schemes` - List available mutual fund schemes
  - `GET /api/health` - Health check endpoint
  - `POST /api/feedback` - Submit feedback on responses
- **Request/Response Format**:
  ```json
  // Request
  {
    "query": "What is the expense ratio of HDFC Large Cap Fund?",
    "scheme": "HDFC Large Cap Fund"  // optional
  }
  
  // Response
  {
    "answer": "The expense ratio of HDFC Large Cap Fund is 1.05% as of March 2024.",
    "source": "https://www.hdfcfund.com/scheme-details/hdfc-large-cap-fund",
    "scheme": "HDFC Large Cap Fund",
    "confidence": 0.85
  }
  ```
- **Deliverable**: API specification document

### 6.2 API Implementation
- **Framework**: FastAPI / Flask / Django REST Framework
- **Components**:
  - Request validation (Pydantic models)
  - Rate limiting
  - Authentication (if required)
  - Error handling
  - Logging and monitoring
- **Activities**:
  - Implement API endpoints
  - Add input validation
  - Implement rate limiting
  - Add comprehensive error handling
  - Set up logging
- **Deliverable**: Functional API with documentation

### 6.3 Caching Layer
- **Objective**: Cache responses for common queries to reduce latency and cost
- **Strategy**:
  - Redis for in-memory caching
  - Cache key: hash of normalized query
  - TTL: 24-48 hours
  - Cache invalidation on corpus updates
- **Activities**:
  - Set up Redis instance
  - Implement caching logic
  - Add cache hit/miss metrics
- **Deliverable**: Configured caching layer

---

## Phase 7: User Interface

### 7.1 Web Interface Design
- **Objective**: Create simple, intuitive web interface for querying
- **Components**:
  - Search bar for queries
  - Scheme selector dropdown
  - Response display area
  - Source link display
  - Feedback mechanism
- **Design Principles**:
  - Clean, minimal interface
  - Mobile-responsive
  - Fast loading
  - Clear source attribution
- **Deliverable**: UI mockups and design document

### 7.2 Frontend Implementation
- **Framework**: React / Vue.js / Next.js
- **Features**:
  - Real-time query submission
  - Loading states
  - Error handling
  - Source link validation
  - Query history (session-based)
- **Activities**:
  - Implement frontend components
  - Integrate with API
  - Add loading and error states
  - Implement responsive design
- **Deliverable**: Functional web interface

### 7.3 Optional: Chat Interface
- **Objective**: Provide conversational interface for multi-turn queries
- **Features**:
  - Chat history
  - Context retention across turns
  - Suggested follow-up questions
- **Activities**:
  - Design conversation flow
  - Implement chat UI
  - Add context management
- **Deliverable**: Chat interface (optional)

---

## Phase 8: Testing and Quality Assurance

### 8.1 Unit Testing
- **Objective**: Test individual components in isolation
- **Test Coverage**:
  - Web scraping module
  - Text extraction and cleaning
  - Chunking logic
  - Embedding generation
  - Retrieval system
  - Response generation
  - API endpoints
- **Framework**: pytest / unittest
- **Deliverable**: Unit test suite with >80% coverage

### 8.2 Integration Testing
- **Objective**: Test end-to-end pipeline
- **Test Scenarios**:
  - Query → Retrieval → Generation → Response
  - Source attribution validation
  - Constraint enforcement
  - Error handling
  - Cache functionality
- **Activities**:
  - Create integration test suite
  - Test with real queries
  - Validate source links
  - Test edge cases
- **Deliverable**: Integration test suite

### 8.3 Quality Evaluation
- **Objective**: Evaluate response quality and accuracy
- **Metrics**:
  - Factual accuracy (manual verification)
  - Source relevance
  - Response conciseness
  - Constraint compliance (no advice)
  - Source link accessibility
- **Activities**:
  - Create evaluation dataset (50-100 test queries)
  - Manual evaluation by domain experts
  - Automated constraint checking
  - Source link validation
- **Deliverable**: Quality evaluation report

---

## Phase 9: Deployment and Infrastructure

### 9.1 Infrastructure Setup
- **Objective**: Set up production infrastructure
- **Components**:
  - Cloud provider (AWS / GCP / Azure)
  - Container orchestration (Docker / Kubernetes)
  - Load balancing
  - Monitoring (Prometheus / Grafana)
  - Logging (ELK stack / CloudWatch)
- **Activities**:
  - Set up cloud infrastructure
  - Configure containers
  - Set up monitoring and alerting
  - Configure auto-scaling
- **Deliverable**: Production infrastructure

### 9.2 CI/CD Pipeline
- **Objective**: Automate build, test, deployment, and data pipeline updates
- **Tools**: GitHub Actions / GitLab CI / Jenkins
- **Pipeline Stages**:
  - Code linting
  - Unit tests
  - Integration tests
  - Build Docker image
  - Deploy to staging
  - Deploy to production
- **Data Pipeline Scheduling (GitHub Actions)**:
  - **Schedule**: Cron job (e.g., daily/weekly) to trigger data refresh
  - **Workflow Steps**:
    1. Run Phase 2.1 scraper to fetch latest HTML from corpus URLs
    2. Run Phase 2.2 content extraction and cleaning pipeline
    3. Run Phase 2.3 chunking pipeline
    4. Run Phase 3.3 embedding generation and indexing pipeline
    5. Regenerate vector database with fresh data
  - **Artifacts**: Store extracted JSON, chunked JSON, and updated vector DB as workflow artifacts or commit to data branch
  - **Notifications**: Alert on pipeline failure (email/Slack)
  - **Conditional Logic**: Only update if content changed (compare checksums)
- **Activities**:
  - Set up CI/CD pipeline
  - Configure automated testing
  - Set up deployment automation
  - Create scheduled GitHub Actions workflow for data refresh
  - Configure artifact storage for generated embeddings/vector DB
- **Deliverable**: Functional CI/CD pipeline with automated data refresh scheduling

### 9.3 Deployment Strategy
- **Objective**: Deploy system to production with minimal downtime
- **Strategy**:
  - Blue-green deployment
  - Canary testing
  - Rollback capability
- **Activities**:
  - Deploy to staging environment
  - Perform smoke tests
  - Deploy to production
  - Monitor for issues
- **Deliverable**: Production deployment

---

## Phase 10: Monitoring and Maintenance

### 10.1 Monitoring Setup
- **Objective**: Monitor system health and performance
- **Metrics**:
  - API response time
  - Error rates
  - Cache hit/miss ratio
  - LLM API costs
  - Query volume
  - Source link failures
- **Activities**:
  - Set up dashboards
  - Configure alerts
  - Set up log aggregation
- **Deliverable**: Monitoring dashboards and alerts

### 10.2 Maintenance Procedures
- **Objective**: Establish procedures for ongoing maintenance
- **Activities**:
  - Regular corpus updates (monthly/quarterly)
  - Source link validation and refresh
  - Prompt refinement based on feedback
  - Model evaluation and updates
  - Dependency updates
- **Deliverable**: Maintenance documentation

### 10.3 Feedback Loop
- **Objective**: Collect and incorporate user feedback
- **Mechanisms**:
  - Feedback form in UI
  - Response rating (thumbs up/down)
  - Query analysis for gaps
- **Activities**:
  - Implement feedback collection
  - Analyze feedback trends
  - Identify improvement areas
  - Update corpus based on gaps
- **Deliverable**: Feedback analysis and improvement process

---

## Technology Stack Summary

### Backend
- **Language**: Python 3.9+
- **Web Framework**: FastAPI
- **Scraping**: BeautifulSoup, requests, pdfplumber
- **Vector DB**: ChrmaDB
- **Embeddings**: transformers (BAAI/bg (BAAI/bge-small-en-v1.5)e-small-en-v1.5)
- **LLM**: Groq (via Groq (Ocompatib-p API)atible API)
- **Cache**: Redis
- **Database**: PostgreSQL (for metadata and logs)

### Frontend
- **Framework**: React / Next.js
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

### DevOps
- **Containerization**: Docker
- **Orchestration**: Kubernetes (optional)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Corpus Definition | 1 week | - |
| Phase 2: Data Ingestion | 2 weeks | Phase 1 |
| Phase 3: Vector Database | 1 week | Phase 2 |
| Phase 4: Retrieval System | 1 week | Phase 3 |
| Phase 5: Reasoning & Guardrails | 2 weeks | Phase 4 |
| Phase 6: API Layer | 1 week | Phase 5 |
| Phase 7: User Interface | 2 weeks | Phase 6 |
| Phase 8: Testing | 2 weeks | Phase 7 |
| Phase 9: Deployment | 1 week | Phase 8 |
| Phase 10: Monitoring | Ongoing | Phase 9 |
**Total Estimated Time**: 14 weeks (3.5 months)

---

## Success Criteria

1. **Accuracy**: >90% factual accuracy on test queries
2. **Source Attribution**: 100% of responses include valid source links
3. **Constraint Compliance**: 0% of responses contain investment advice
4. **Performance**: <3 second response time for 95th percentile
5. **Coverage**: System can answer >80% of factual queries about selected schemes
6. **Reliability**: >99.9% uptime in production
