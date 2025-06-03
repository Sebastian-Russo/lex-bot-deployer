**Single Intent** => officeLocator

**Slot** => zipCode
P1110: Initial zipcode collection
Okay, office information. One moment. Go ahead and say or enter the five digit zip code for your area or the area where you want to find an office.

P1110c: Invalid Zip Code
That is an invalid Zip Code. Let's try again. Please say the five digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.

P1110d: Request reenter zip code
My mistake. Let's try again. Please say the five digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.

P1110e: (In-Hour)
Sounds like you don't know the zip code. Let me connect you to an agent.

P1110e: (Off-Hour)
Sounds like you don't know the zip code. Normally I'd get an agent to help you, but unfortunately we're closed.

**Slot** => zipCodeConfirmation
P1118: Zipcode confirmation (conditional)
That zip code is {zip_code}. Right?

**API Call** => officeLocator
**Logic Check** => check if card center in this zip code?
(maybe combine these two steps)
**Error** => Transfer to agent
P9011: (In-Hour)
Sorry, I'm having trouble processing this request. Hold on while I get someone to help you.

P9011: (Off-Hour)
Sorry, I'm having trouble processing this request. Normally I'd get an agent to help you, but unfortunately we're closed.

**Branch 2**
**Slot/New Intent?** => newZipCode (restart)
P1123: New zip code collection
Alright, let us look somewhere else. What is the zip code?

P1123: New zip code collection
Alright, let us look somewhere else. What is the zip code?

P1110c: Invalid Zip Code
That is an invalid Zip Code. Let's try again. Please say the five digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.

P1110d: Request reenter zip code
My mistake. Let's try again. Please say the five digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.

P1110e: (In-Hour)
That is an invalid Zip Code. Let me connect you to an agent.

P1110e: (Off-Hour)
That is an invalid Zip Code. Normally I'd get an agent to help you, but unfortunately we're closed.

P9011: (In-Hour)
Sorry, I'm having trouble processing this request. Hold on while I get someone to help you.

P9011: (Off-Hour)
Sorry, I'm having trouble processing this request. Normally I'd get an agent to help you, but unfortunately we're closed.

**Branch 1**
**Slot** => newSSNCard
P1121: Card center question (conditional)
Thanks. Do you need to get a Social Security card?

**Response to newSSNCard**

**yes**
P1122
All right. To apply for a new or replacement Social Security card, you will need to visit the card center in your area which is located at {address}. The hours of operation are, {hours}. And the phone number is {phone}.

**Slot** => repeat
P1123: To hear that again, say repeat that. For information about the local Social Security office, say local office. To search in a different zip code, say change zip code.Or if you're finished, just say, I'm finished.

**no**
P1112
Okay, here's information for the servicing office in the zip code {zip_code}. The address is {address}. The hours of operation are {hours}. And the phone number is {phone}.

**Slot** => finished
End of conversation.

**Slot** => repeat
P1113a:
Let's try again. You can say Repeat That, Change Zip Code, or Finished.

<!-- P1113b:
Sorry. If you'd like to hear that information again, press 1. Otherwise, to search for a local office using a different zip code, press 2. Or, if you're finished, press 3. -->

**Slot** => More information
P0000 (not real)
You've reached more information. To hear that again, say repeat that. For information about the local Social Security office, say local office. To search in a different zip code, say change zip code.Or if you're finished, just say, I'm finished.

**Branch 2**
**Slot/New Intent?**
P1117: New zip code collection
All right, let's look somewhere else. What is the zip code?
