Pamphlet Request

Connect Block: Get User Input => Invoke lex bot => Initiate Slot
P1201:
Okay, pamphlets. One moment. There are several pamphlet topics to choose from. I will take you through the list and you can select the ones you want. To skip ahead to the next topic, just say, skip topic. To hear it again, say, repeat that. And at any time, you can say, I am done. Now, to get started.

**Slot 1**
P1202:
Do you want the pamphlet on {Understanding Social Security}?

- **Options - Repeatable slots:**
  P1203:
  Before I get your mailing address, would you like to hear more choices?
  _options_
  yes > offer next pamphlet
  no > get address

  **Repeat**
  P1202 {slot name/pamphlet}

  **Agent**
  P1068:
  You'd like to talk to an agent, right?
  P1068a: Let's try again. You'd like to talk to an agent, right?
  P1068b: Sorry. TO talk to an agent, press 1, otherwise press 2.
  _Options_
  yes > send to agent
  no > offer pamphlet again, P1202

  **I'm done**
  Done with pamphlet choices, set session attributes

**Slot 2**
P1202: Do you want the pamphlet on {Retirement Benefits}?

- same options

**Slot 3**
P1202:
Do you want the pamphlet on {Disability Benefits}?

- same options

**Slot 4**
P1202:
Do you want the pamphlet on {Survivor Benefits}?

- same options

**Slot 5**
P1202:
Do you want the pamphlet on {How Work Affects Benefits}?

- same options

**Slot 6**
P1202:
Do you want the pamphlet on {Benefits for Children with Disabilities}?

- same options

**Slot 7**
P1202:
Do you want the pamphlet on {What Every Woman Should Know About Social Security}?

- same options

---

**[Pamphlet Counter]** Count > 0 and < 7
P1204: Count = 0
That was the last one. Would you like to hear those choices again?

_repeat_
P1204a
Let's try again. Would you like to hear those choices again?
Pl1204b
Sorry. Would you like to hear those choices again? Say yes or press 1. Otherwise say no or press 2.
_options_
yes > offer pamphlet again, P1202
no > return to menu, P1069

---

**Slot 8**
P1205: Count = > 0 and < 7
Thanks. Now let's get your address.

or

P1206: Count = 7
That's all the pamphlets I have to offer. Thanks. Now let's get your address.

P1207:
Got it.

Request Successful?

_Options_
no >
P9011: (In-Hour)
I'm having trouble processing your request. Hold on while I get someone to help you.
P9011: (Out-Hour)
I'm sorry, I'm having trouble processing your request. Normally I'd get an agent to help you, but I'm out of hours. Please try again later.
yes >
P9012:
All set. I've put your order through, and you should receive the pamphlets, {list_pamphlets}, in the mail within two weeks.
P1021:
Alright. If you're finished, feel free to hang up. Otherwise, just hang on and I'll take you back to the Main Menu.

-
-
-
- **_Global Behavior_**

Intent: Finished
Closing response, set session attributes

Intent: More Choices
**Slot**
P1203a:
Let's try again, would you like to hear mroe choices?
P1203b:
Sorry, would you like to hear more choices say yes or press 1. Otherwise say no or press 2.

_Options_
yes > what other choices ?? Global?
no > offer pamphlet again, P1202

Intent: MainMenu
**Slot**
P1069:
You'd like to go back to the main menu, right?
P1069a:
Let's try again. You'd like to go back to the main menu, right?
P1069b:
Sorry. To go back to the main menu, press 1, otherwise press 2.

_Options_
yes > return to menu
no > offer pamphlet again, P1202
