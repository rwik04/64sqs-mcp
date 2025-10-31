RESPONSE_GENERATION_CONTEXT_PROMPT = """
You will now be provided with reference texts from file `{filename}`, that has been found relevant
Use ONLY these references to draft a potential answer as per this file
"""

RESPONSE_GENERATION_REFERENCE_PROMPT = """
Here is reference text #{reference_index}
```
{reference}
```
"""

RESPONSE_GENERATION_FINAL_INSTRUCTIONS = """
The original user query you must answer is:
```
{original_query}
```
To find the reference texts, we used the following simplified search query/queries:
```
{queries}
```

---
## 1. General Analysis Guidelines
---
Before you formulate your answer, keep these points in mind:
* Scan for Details: The query might be about minor facts or figures. Scan the reference texts carefully for every detail before answering.
* Synthesize Information: You may need to connect information across multiple reference text snippets to create a complete answer.

---
## 2. Critical Instructions on Response Format
---

FIRST, analyze the **ORIGINAL user query's** intent. The output format depends ENTIRELY on this analysis.

### CASE 1: The user wants a direct, short-form answer.
This applies if the **original query** contains phrases like "answer strictly with Y or N", "answer with a single letter", "provide only the name".

* Your Task: Your response MUST strictly follow the user's format.
* JSON 'response' field: MUST contain ONLY the single letter or word requested. For example: "Y", or "N", or "Red". It MUST NOT contain any other explanatory text.
* JSON 'pointers' field: Should contain the text snippets that justify your direct answer.

### ---- EXAMPLE START ----
* Query: "Does the document mention the color blue? Answer Y/N"
* Reference Text: "The sky is a brilliant shade of blue, and the car is red."
* Correct JSON output: {{"response": "Y", "pointers": ["The sky is a brilliant shade of blue..."]}}
* Incorrect JSON output: {{"response": "Yes, the document mentions the color blue.", "pointers": [...]}}
### ---- EXAMPLE END ----

### CASE 2: The user wants an open-ended, narrative answer.
This applies to all other queries.

* Your Task: Provide a helpful, narrative summary.
* JSON 'response' field: A normal, consolidated summary based on the reference texts.
* JSON 'pointers' field: The key text blocks used to create the summary.

---
## 3. Rules for ALL Answers
---
* No Source Citing: Do not mention the reference texts using phrases like 'Based on the provided context' or 'According to the references'.
* Do Not Mention Filename: Your response must not include the filename.
* Failure Condition: If the query absolutely cannot be answered with the given references (because they are irrelevant or the query is ambiguous), the 'response' value MUST start ONLY with the phrase 'NOT ANSWERABLE.' followed by a brief reason.

---
## 4. Final JSON Output Structure
---
Return your answer as a valid JSON object with the following keys ONLY:
1.  'response': The final answer, in plain text without quotes, following all the formatting rules above.
2.  'pointers': An array (i.e., `[]`) of the key text blocks you used from the references. Quote these blocks verbatim, preserving the exact case, spaces, punctuation, and newline characters.
"""
