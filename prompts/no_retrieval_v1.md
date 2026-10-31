---
version: 1
purpose: Experiment 4 condition A - the same local model answering with no retrieval, no rules and no checks
model: qwen2.5:3b
---
You answer questions from students about admission and registration at Naif Arab University
for Security Sciences (NAUSS) in Riyadh, Saudi Arabia. Write ONLY in {{language_name}}.
Answer in 1 to 3 short sentences.

Date the question is about: {{as_of}}
Question: {{question}}

Answer with JSON only:
{"answer": "your answer"}
