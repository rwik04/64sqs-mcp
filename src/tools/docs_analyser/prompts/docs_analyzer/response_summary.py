RESPONSE_SUMMARY_SYSTEM_PROMPT = """
Following is a query raised by the user
```
{query}
```

And next, you will be shown a set of 'possible' responses found by scanning through one or more data sources
You are required to go through the responses and create a consolidated summary

While creating the consolidated summary, you may do one or more of the following, depending upon the intent of the original user query
1. Simply consolidate information from the different responses
2. Compare and contrast information from the different responses
3. Create some aggregated stats from the different responses
"""

RESPONSE_SUMMARY_REFERENCE_PROMPT = """
Here is response #{response_index} found by scanning through the file `{displayname}`
```
{response}
```
The guidelines for creating the consolidated summary are as follows:
- When writing the consolidated summary, organize the information into clear themes or topics, rather than listing individual responses.
- Focus on identifying patterns, similarities, and differences across the responses.
- Use neutral and factual language, and avoid unnecessary details or repetition.
- Summarize key points using simple, direct sentences that are easy for both technical and non-technical readers to understand.
- Where appropriate, use qualitative terms such as "most," "several," or "a few" to describe trends, instead of providing exact numbers.
- Include representative examples only when they help clarify a theme or insight.
- Structure the summary logically, for example by moving from general observations to specific details, or by grouping related topics together.
- Conclude with a brief overall impression or summary of the main findings.
"""
