First Intent:

- P1110: Okay, office information. One moment. Go ahead and say or enter the five digit zip code for your area of the area where you want to find an office.

Slots:

- zipCode:
  - necessary: true
    - Valid => Confirmation: That zip code is {zipCode}. Right?
    - Invalid => That is an invalid zip code. Let's try again. Please say the five digit zip code where you'd like me to search. Like this, 1 2 3 0 0. Or enter it on your keypad.

Confirmation Intent:

- P1118: That zip code is {zipCode}. Right?

Slots:

- yes > continue to fulfillment intent
- no > ask for zip code again

Fulfill Intent:
**Get office location** (lambda api lookup with zip?)

- Invalid => That is an invalid zip code. Let's try again. Please say the five digit zip code where you'd like me to search. Like this, 1 2 3 0 0. Or enter it on your keypad.
  - no > P1110C: that is an invalid Zip Code. Let's try again. Please say the five digit zip code where you'd like me to search. Like this, 1 2 3 0 0. Or enter it on your keypad.
  - yes > Check: Is Card Center in the zip? and ask next question/slot elicitation

Next Slot elicitation intents:

- p1121: Thanks. Do you need to get a Social Security card?
  Slots:

- yes > P1122: Alright. To apply for a new or replacement Social Security card, you'll need to visit the card center in your area which is located at {Address}. The hours of operation are, {HoursOfOperation}. And the phone number is {PhoneNumber}.
- no > Check: Is Card Center in the zip? and ask next question/slot elicitation

Next Slot elicitation intents:

- P1123: To hear that again, say repeat that. For information about the local Social Security office, say local office. To search in a different zip code, say change zip code.Or if you're finished, just say, I'm finished.

Slots:

- repeat > P1122: Alright. To apply for a new or replacement Social Security card, you'll need to visit the card center in your area which is located at {Address}. The hours of operation are, {HoursOfOperation}. And the phone number is {PhoneNumber}.
- change zip code > P1117: Alright, let's lok somehwere else. What is the zip code?
- finished > return to main menu
- local office > P1112: Okay, here's information for the servicing office in the zip code {zipCode}. The street address is {Address}. The hours of operation are, {HoursOfOperation}. And the phone number is {PhoneNumber}.

P1113: TO hear that again, say repeat that. Otherwise, to search a different zip code, say change zip code. Or if you're finished, just say, I'm finished.

- finished > return to main menu
- change zip code > P1117: Alright, let's lok somehwere else. What is the zip code?
