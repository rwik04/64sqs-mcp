# 64SQS MCP Server

A powerful Model Context Protocol (MCP) server that provides advanced AI-powered tools for document analysis, data interpretation, and content generation. Built with FastMCP and designed for seamless integration with LLM applications and workflows.

## 🌟 Features

### Core Tools

1. **Docs Analyzer** - Unstructured Data Analysis
   - Search and analyze PDFs, TXTs, DOCs, PPTs, webpages, and other unstructured data sources
   - Extract information relevant to specific queries with source references
   - Multi-query parallel processing for efficiency
   - Automatic summarization across all queries and files

2. **Data Interpreter** - Structured Data Analysis
   - Query and analyze structured datasets (SQL databases, CSV files, tables)
   - Multi-step data transformation and aggregation workflows
   - Intelligent annotation of text-heavy columns to create quantifiable metrics
   - Support for complex SQL operations across multiple tables

3. **Content Writer** - Document Generation
   - Generate structured documents from notes and specifications
   - Export to Word documents (.docx) or HTML pages
   - Two-step process: outline generation → detailed content creation
   - Maintains consistent formatting and structure

4. **Researcher Agent** - Autonomous Research Workflows
   - AI agent that orchestrates multi-step research tasks
   - Automatic tool selection and chaining
   - Context-aware decision making
   - Token usage tracking and optimization

## 🏗️ Architecture

```
64sqs-mcp/
├── src/
│   ├── server.py                 # Main MCP server with tool definitions
│   ├── agents/                   # AI agent framework
│   │   ├── researcher.py         # Main research agent
│   │   ├── context_provider.py   # Context management
│   │   ├── tool_manager.py       # Tool orchestration
│   │   └── prompts.py            # System prompts
│   ├── tools/
│   │   ├── docs_analyser/        # Document analysis tool
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   ├── services/         # Query analysis, search, response generation
│   │   │   └── prompts/          # LLM prompts for analysis
│   │   ├── data_interpreter/     # Structured data analysis tool
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   └── services/         # SQL generation, annotation, summarization
│   │   └── content_writer/       # Document generation tool
│   │       ├── main.py
│   │       ├── config.py
│   │       └── services/         # Outline and section generation
│   └── resources/                # Additional resources
├── temp/                         # Temporary output files
├── pyproject.toml                # Poetry dependencies
└── start_server.sh               # Server startup script
```

## 📋 Prerequisites

- Python 3.12 or higher
- Poetry (Python dependency manager)
- OpenAI API key or compatible LLM API
- AWS credentials (for S3 storage, optional)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd 64sqs-mcp
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# LLM Configuration
LLM_API_KEY="your-openai-api-key"
EMBEDDING_API_KEY="your-embedding-api-key"

# AWS Configuration (Optional)
AWS_ACCESS_KEY="your-aws-access-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
AWS_BUCKET_NAME="your-bucket-name"
AWS_CLIENT_ID="your-client-id"
AWS_PROJECT_ID=your-project-id
```

### 4. Start the Server

#### Using the Startup Script (Recommended)

```bash
./start_server.sh
```

The script will:
- Check for running instances and stop them
- Start the server on port 8000
- Set appropriate timeout configurations
- Provide instructions for exposing the server

#### Manual Start

```bash
poetry run python src/server.py
```

## 📖 Usage

### MCP Server Endpoint

Once started, the server is available at:
```
http://localhost:8000/mcp
```

### Tool Examples

#### 1. Docs Analyzer

Analyze unstructured documents to answer specific queries:

```python
{
    "name": "docs_analysis",
    "arguments": {
        "query": [
            "What are the main findings?",
            "What methodology was used?",
            "What are the limitations?"
        ],
        "filenames": [
            "research_paper.pdf",
            "supplementary_materials.docx"
        ],
        "save_outputs": true
    }
}
```

**Output:**
- Structured responses for each query
- Source references with page numbers and citations
- Aggregated summary across all queries
- Temp files (JSON/CSV) for downstream processing

#### 2. Data Interpreter

Analyze structured data with SQL and annotations:

```python
{
    "name": "data_interpreter",
    "arguments": {
        "query": "What percentage of users prefer each mobile carrier? Break down by age group.",
        "filenames": [
            {
                "displayname": "User Survey Results",
                "filename": "temp/survey_responses.csv",
                "filetype": "temp"
            }
        ],
        "save_outputs": true
    }
}
```

**Output:**
- Annotated datasets with quantifiable metrics
- SQL query results with aggregations
- Statistical insights and inferences
- Temp files for further analysis

#### 3. Content Writer

Generate structured documents from analysis results:

```python
{
    "name": "content_writer",
    "arguments": {
        "filenames": [
            "temp/analysis_results.json",
            "temp/survey_data.csv"
        ],
        "target_document_type": "doc",
        "target_document_length": "1500 words",
        "target_document_brief": "Create a comprehensive report comparing healthcare responses across countries, focusing on preparedness, technology adoption, and lessons learned. Use a professional tone suitable for healthcare administrators.",
        "save_outputs": true
    }
}
```

**Output:**
- Generated Word document or HTML page
- Structured sections with headings
- File path to the saved document
- Token usage statistics

### Using the Researcher Agent

The Researcher agent can autonomously orchestrate multi-step workflows:

```python
from src.agents.researcher import Researcher

researcher = Researcher(
    instructions="Analyze interview transcripts to identify key themes and generate a comparative report",
    mcp_url="http://localhost:8000/mcp"
)

result = await researcher.run(user_prompt="""
    I have 10 doctor interviews about pandemic response.
    Please analyze them to find:
    1. Common challenges faced
    2. Successful strategies by country
    3. Recommendations for future preparedness
    
    Then generate a professional report suitable for healthcare policy makers.
""")
```

The agent will:
1. Automatically select appropriate tools
2. Chain multiple tool calls if needed
3. Build context across tool executions
4. Generate the final deliverable

## 🔧 Configuration

### Server Configuration

Edit `start_server.sh` to customize:

```bash
# Timeout settings (in seconds)
export UVICORN_TIMEOUT_KEEP_ALIVE=300      # Keep-alive timeout
export UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=30 # Graceful shutdown timeout
```

### Tool-Specific Configuration

Each tool has its own `config.py` file:

- `src/tools/docs_analyser/config.py`
- `src/tools/data_interpreter/config.py`
- `src/tools/content_writer/config.py`

Configure API keys, model settings, and other parameters as needed.

## 🌐 Exposing the Server

### Using ngrok (Quick Setup)

```bash
ngrok http 8000
```

This will provide a public URL that you can use to access the MCP server.

### Using nginx (Production)

1. Create nginx configuration:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/mcp-server
sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/
```

2. Test and reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 📊 Output Files

All tools support `save_outputs` parameter which saves results to the `temp/` directory:

- **JSON files**: Structured results with full metadata
- **CSV files**: Flattened data for easy analysis
- **DOCX files**: Generated documents (Content Writer)

Temp files are designed for:
- Chaining tools in multi-step workflows
- Preserving intermediate results
- Easy data exploration and validation

## 🛠️ Development

### Running in Development Mode

```bash
# Activate poetry shell
poetry shell

# Run server with auto-reload
uvicorn src.server:mcp.app --reload --port 8000
```

### Adding New Tools

1. Create a new directory under `src/tools/`
2. Implement the tool logic in `main.py`
3. Add configuration in `config.py`
4. Register the tool in `src/server.py` using the `@mcp.tool` decorator

### Testing Tools

```python
# Example: Test docs analyzer locally
from tools.docs_analyser.main import DocsAnalyzer
from tools.docs_analyser.models import FileInfo

analyzer = DocsAnalyzer(
    filenames=[FileInfo(filename="test.pdf", displayname="Test Document", filetype="pdf", id="test1")],
    query="What is the main topic?"
)
result = analyzer.analyze_files()
```

## 📦 Dependencies

Key dependencies (see `pyproject.toml` for complete list):

- **FastMCP**: MCP server framework
- **LangChain**: LLM orchestration and agents
- **OpenAI**: LLM API client
- **LlamaIndex**: Document indexing and retrieval
- **Boto3**: AWS S3 integration
- **python-docx**: Word document generation
- **Uvicorn**: ASGI server

## ⚠️ Important Notes

### Resource Intensive Operations

- **Docs Analyzer**: Process multiple queries in a single call rather than making repeated calls
- **Data Interpreter**: Consolidate requirements—this tool is designed for large, comprehensive queries
- Both tools are resource-intensive; plan your workflow to minimize redundant calls

### Best Practices

1. **Use temp files for chaining**: Always set `save_outputs=true` when results will be used in subsequent steps
2. **Provide detailed briefs**: The more specific your instructions, the better the output quality
3. **Batch queries**: Group related questions together for efficiency
4. **Monitor token usage**: Check `token_tracker` in responses to manage costs

### Limitations

- **Docs Analyzer**: Not suitable for pure summarization tasks or data analytics
- **Data Interpreter**: Cannot identify broad themes in text data; requires quantifiable fields
- **Content Writer**: Quality depends on the richness of input source material

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Submit a pull request

## 📄 License

[Add your license information here]

## 👥 Authors

- **rwik04** - rwik04@kgpian.iitkgp.ac.in

## 🆘 Support

For issues, questions, or feature requests, please [open an issue](https://github.com/your-repo/issues) on GitHub.

---

**Server Status**: Once started, check server health at `http://localhost:8000/health`

**MCP Endpoint**: `http://localhost:8000/mcp`

**Version**: 0.1.0

