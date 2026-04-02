# Interactive Flashcard Review

Run an interactive flashcard review session with the user.

## Steps

1. Run `python study.py flash` to get today's due flashcards.

2. If there are no due cards, run `python study.py refresh` to regenerate the flashcard deck, then try again.

3. For each flashcard, run an interactive review:

   ### a. Show the Front
   Present the question. Do NOT show the answer yet.

   ### b. Wait for the User's Answer
   Let the user try to answer in their own words. Encourage them to be thorough.

   ### c. Evaluate and Teach
   - Run `python study.py flash-answer <card_id>` to show the official answer
   - Compare the user's answer with the official answer
   - If the user missed key points, explain them interactively
   - For cards the user got wrong, do a 2-3 minute mini-lesson on that topic

   ### d. Record Result
   - If the user understood well: `python study.py flash-ok <card_id>`
   - If the user struggled: `python study.py flash-fail <card_id>`
   - Explain: failed cards will come back sooner (Leitner system)

4. After all cards are reviewed:
   - Run `python study.py flash-stats` to show overall statistics
   - Suggest topics where the user should review more
   - Recommend running `python study.py quiz` for deeper testing

## Principles
- This is NOT passive review. The user must actively recall.
- If a card is about MACA/CUDA/HIP, draw explicit parallels.
- For "fuzzy" answers, provide the specific detail they're missing.
- Keep sessions to 10-15 cards max to avoid fatigue.
