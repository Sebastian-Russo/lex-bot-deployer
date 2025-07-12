# TODO

## Testing/Comparing Code

**Add test code to each lambda bot**

- [] Add test code to each lambda bot (test code in /tests/lambdas/index.py)
- [] Figure out how it works

**Create test data**

- [x] headers
  - test_case,step,utterance,session_attributes,expected_reponse,expected_intent,expected_state,bot_id,alias_id,locale_id,notes
  - main_route_1,2,blank,,"blank",LocateOffice,InProgress,S7IGLOYNUF,IXB6AXISGB,en_US,
    - test alias: TSTALIASID, live alias: IXB6AXISGB
- [x] Use testbot in console to create “test cases” dialog, create csv
- [] Upload csv to S3 bucket /input

**Set up test locally**

## Building Lexbots

- [x] SSA Menu bot
- [x] Office Locator bot
- [x] Medicare Card Replacement bot
- [x] Pamphlet bot
- [] Change of Address bot
- [] Benefit Payment bot
- [] Reprint 1099 bot

# Currently Building:

- [] Medicare Enrollment bot
