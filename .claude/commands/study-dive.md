# Deep Dive into a Topic

Do a deep interactive learning session on: $ARGUMENTS

## Steps

1. Search the study CLI data files for relevant content:
   - `data/guides/phase*.json` for key_points and flashcards on this topic
   - `data/resources.json` for curated materials
   - `data/quizzes.json` for related quiz questions

2. Read actual source code or documentation:
   - If a GitHub repo is mentioned, use WebFetch to read key source files
   - If documentation URLs exist, fetch and extract the most relevant sections
   - For MACA topics, check https://developer.metax-tech.com/softwaredoc/

3. Create a structured deep-dive session (~30-45 min):

   ### a. Concept Foundation (5 min)
   - Explain the core concept with a concrete example
   - Draw parallels to something the user already knows (usually CUDA/PyTorch)

   ### b. Source Code Walkthrough (10-15 min)
   - Walk through key code line by line
   - Highlight the "aha moment" - the key insight that makes it click
   - Point out common pitfalls

   ### c. Hands-on Exercise (10 min)
   - Give a small coding challenge related to the topic
   - The user should write code, not just read
   - Review their solution and suggest improvements

   ### d. Verification Quiz (5 min)
   - Ask 3 questions to verify understanding
   - For any wrong answer, do a mini-lesson on that sub-topic
   - Suggest creating a flashcard: `study note flashcard "topic: question → answer"`

4. After the session, suggest related topics to explore next.

## Teaching Style
- Go deep, not wide. One concept fully understood > five concepts partially grasped.
- Use the Socratic method: ask guiding questions before giving answers.
- Connect to MetaX/MACA context when relevant.
- Chinese is OK for explanations, but keep code and technical terms in English.
