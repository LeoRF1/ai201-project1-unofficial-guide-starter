# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

I will be using student reviews of truman's computer science courses. This is valuable because the official course descriptions don't reflect the teaching style, exam difficulty, or workload.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessor| File| documents/cs100.txt|
| 2 | RateMyProfessor| File| documents/cs180.txt|
| 3 | RateMyProfessor| File| documents/cs181.txt|
| 4 | RateMyProfessor| File| documents/cs260.txt|
| 5 | RateMyProfessor| File| documents/cs310.txt|
| 6 | RateMyProfessor| File| documents/cs315.txt|
| 7 | RateMyProfessor| File| documents/cs330.txt|
| 8 | RateMyProfessor| File| documents/cs430.txt|
| 9 | RateMyProfessor| File| documents/cs455.txt|
| 10 |RateMyProfessor | File|documents/cs480.txt|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

I will be using a chunk size of 500 characters.

**Overlap:**

I will use an overlap of 50 characters.

**Reasoning:** 

RateMyProfessor reviews are typically 2–5 sentences. A 500-character chunk captures roughly one full review without merging two separate students' opinions together. The 50-character overlap ensures that a sentence split at a chunk boundary doesn't lose its trailing context 

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

I will use the all-MiniLM-L6-v2 model

**Top-k:**

I will be setting top-K = 4.

**Production tradeoff reflection:**

1. Context Window Constraints: The all-MiniLM-L6-v2 model is strictly capped at a 256-token or 512-token context length. While fine for short reviews, it completely chokes if a student writes a massive, multi-paragraph essay detailing a semester-long grievance.

2. Domain Specificity: The model was trained on general-purpose internet corpora. It does not innately understand computer science shorthand or Truman-specific academic vocabulary (e.g., "CS 310", "Math dual-enrollment", "JBA").

3. The Latency vs. Accuracy Balance: Moving to a heavyweight production model like OpenAI’s text-embedding-3-large or Cohere's embed-v4 would significantly increase vector dimensions and query cost/latency. However, it would dramatically boost the system’s ability to parse complex, multi-sentence conceptual nuances and handle localized student slang.



---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about the workload and difficulty of CS 181 compared to CS 180? | CS 181 has lots of homework but students describe it as "small practices rather than time consuming." CS 180 had fewer assignments and no tests — just quizzes. Both courses use C++ and multiple students describe it as hard, but Dr. Yu's detailed slides and lenient grading in CS 181 make it manageable. |
| 2 | What are the common complaints and praises for Dr. Charles Yu in CS 480? | Praises: detailed algorithm explanations, fun final projects, and good coverage of reinforcement learning. Complaints: students note the final exam is "a bit scary" and that some basic math/stats prerequisites are expected but not clearly stated upfront. |
| 3 | Does Dr. Charles Yu allow makeup exams in CS 181, and how is grading handled? | Yes — students specifically mention he provides chances for makeup exams, grading on exams is lenient, and there is a bonus homework at the end of the semester. |
| 4 | What do students say about the final project and assignments in CS 480? | Students say there are 4–5 assignments based on classic problems with answers available online. The final project is described as fun and creative — one team built a hexapod for obstacle detection. The final exam is worth 20% and is the only "slightly challenging" part. |
| 5 | What are the main criticisms students have about Dr. Charles Yu in CS 180? | One student gave a strongly negative review: they claimed Dr. Yu deducted points even for perfectly running code over minor issues, gave vague answers to questions, and spoke negatively about the student to the TA. Other reviews are more positive, noting it was his first semester teaching and that he was sweet and approachable. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. A user asking a question that is not related to any of the courses will result in the system returning no relevant information. Vector databases like ChromaDB must return the mathematical "closest match" ($K=4$) even if the text is completely irrelevant to the user's intent. If a user asks about dining halls, ChromaDB might still pull a review that casually mentions a professor "eating lunch." If you pass these irrelevant chunks blindly to the LLM, it might try to force an answer or hallucinate.

2. A user asking a question that is related to multiple courses may result in the system returning irrelevant information. Because we are using a global top_k = 4 retrieval strategy, a single query might return two chunks for CS 181 and two chunks for CS 425. If the chunks don't directly address workload, or if the vector search heavily favors one class over the other due to keyword matching, the retrieved context will be unbalanced. The LLM will then generate a highly biased or incomplete comparison

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->


+-----------------------+      +-------------------+      +-------------------------+   
|   Document Ingestion  | ---> | Chunking Pipeline | ---> |  Embedding Generation   |
| (10 .txt Files Loaded)│      | (500 char / 50 ov)│      | (all-MiniLM-L6-v2 Local)│
+-----------------------+      +-------------------+      +-------------------------+
                                                                       |
+-----------------------+      +-------------------+                   v
|   Grounded LLM Gen    | <--- |  Semantic Search  | <--- +-------------------------+
| (Groq Llama-3.3-70b)  |      |   (ChromaDB K=4)  |      |   Vector Database Store |
+-----------------------+      +-------------------+      |  (ChromaDB Local Disk)  |
           |                                              +-------------------------+
           v
+-----------------------+
|  Gradio UI Interface  |
|   (Answer + Sources)  |
+-----------------------+

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

tool: Claude
input: My 10 .txt files in documents/, my Chunking Strategy section 
       (500 char chunks, 50 char overlap, split on double newline first),
       and my Documents table showing the source filenames.
output: ingest.py that loads all 10 files, cleans whitespace and artifacts,
        splits on double newlines first then applies 500-char sliding window
        with 50-char overlap, and returns a list of dicts with "text" and 
        "source" keys.
verification: I will run ingest.py and print 5 random chunks to the terminal.
              Each chunk must: (1) be readable as a standalone student opinion,
              (2) show the correct source filename in its metadata, (3) contain
              no leftover whitespace artifacts or empty strings, and (4) be 
              between 50 and 500 characters long. I will also print the total
              chunk count — if it's below 50 or above 500, I'll revisit my 
              chunk size. I will not move to Milestone 4 until all four 
              criteria pass.

**Milestone 4 — Embedding and retrieval:**
tool: Claude
input: My Retrieval Approach section (model name: all-MiniLM-L6-v2, top-k: 4),
       my Architecture diagram, and the chunk output format from ingest.py
       (list of dicts with "text" and "source" keys).
output: embed.py that loads chunks, embeds them with SentenceTransformer, 
        stores them in a local ChromaDB collection with source metadata.
        retrieve.py with a retrieve(query, k=4) function that returns 
        top-k chunks with their text, source, and distance score.
verification: I'll run test_retrieval.py on 3 of my 5 eval questions and 
              confirm returned chunks visibly relate to each query and 
              distance scores are below 0.5.

**Milestone 5 — Generation and interface:**
tool: Claude
input: My grounding requirement (answer only from retrieved context, 
       refuse if documents don't cover it), my Architecture diagram 
       showing Groq as the LLM stage, and the retrieve() function signature.
output: query.py with an ask(question) function that calls retrieve(), 
        builds a grounded prompt, calls Groq llama-3.3-70b-versatile, 
        and returns {"answer": ..., "sources": [...]}.
        app.py with a Gradio UI showing two output fields: Answer and Sources.
verification: I'll test one in-scope and one out-of-scope question. 
              The out-of-scope question should return the refusal message, 
              not a hallucinated answer.