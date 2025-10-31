QUERY_RELEVANCE_CONTEXT_PROMPT = """
Here's the summary of the file `{filename}`

```
{summary_text}
```
"""

QUERY_RELEVANCE_INSTRUCTIONS_PROMPT = """
Return your response as a valid JSON with the following keys
1. 'relevance_flag':
1.1. If the file appears relevant for answering the user query, this should 'yes, looks relevant' (in lowercase) and nothing else.
1.2. If the file does not appear relevant for answering the user query, simply return a blank string ''
2. 'search_query':
2.1. If the file appears relevant for answering the user query, describe the exact information you want to query from this file. This can either be same as the original user query or a logical subset of the user query, incase there are other files that would be required as well
2.2. If the file does not appear relevant for answering the user query, simply return a blank string ''

While writing the search query, you should carefully review the original query and the file details closely to determine what part of the information sought is available, and in what form
However be very careful so as not to end up introducing a new term/concept/keyword/name/location in the search query, that's not a part of the original query, just because it maybe present in this file's details
"""
