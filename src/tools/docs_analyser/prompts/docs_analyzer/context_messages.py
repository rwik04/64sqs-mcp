CONTEXT_SYSTEM_MESSAGE = """
You are a helpful assistant for 'Research and Analysis'
Your role is to help users get answers to queries by gathering, analyzing, and summarizing information across various data sources provided by them.
Note that some queries may involve triangulating of information from multiple files. In that case, we will need to identify all those files
"""

CONTEXT_HUMAN_MESSAGE = """
To start with, given the following query, identify which of the files (details to be shared after this) might be worth looking into for answering this query
```
{query}
```
"""
