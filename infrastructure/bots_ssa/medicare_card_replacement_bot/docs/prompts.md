**Single Intent** => ProcessMedicareCardReplacement

**Slot** => privacyAcknowledgment
(Connect Invoke User Input)
P1045 gov website
Ok. Medicare Replacement Card. One moment. Do you know you can requrest a replacement card online by going online and using your My S S A account? Go to w w w dot social security dot g o v and select Sign in.

P1173
Before I can access your records, I will need to ask a question or two to verify who you are. Social Security is allowed to collect this information under the Social Security Act and the collect meets the requirements of the Paperwork Reduction Act under OMB number 0 9 6 0 0 5 9 6. The whole process should take about four minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say continue.

P1009a
Let's try again. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say, more information. Otherwise, say continue.

P1009b
Sorry. If you'd like to hear detailed information about the Privacy Act or Paperwork Reduction Act, say, more information or press 1. Otherwise, say continue or press 2.

**Slot** => termsAgreement
P1010
Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?

P1010a
Let's try again. Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?

P1010b
Sorry. Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. If you DO understand and agree to theses terms, say yes or press1. If you DO NOT understand and agree to theses terms, say no or press 2.

P1022 (In-Hour)
Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.

P1022 (Out-Hour)
Without your agreement, I will not be able to help you with anything that requires access to personal information.

**Slot** => socialSecurityNumber
Ask for SSN

**Slot** => dateOfBirth
Ask for DOB

**Slot** => firstName
Ask for First Name

**Slot** => lastName
Ask for Last Name

**Submit Request - API Request**
P1046: THank you. I've got everything I need. Hold on while I submit this.

**Success**
P1047:
All right. We're all set. You should receive your replacement card in the mail within four weeks. If you're finished, feel free to hang up. Otherwise, just hang on and I'll take you back to the Main Menu.

**Error**
P9011 (In-Hour)
Sorry, I'm having trouble processing this request. Hold on while I get someone to help you.

P9011 (Out-Hour)
Sorry, I'm having trouble processing this request. Normally I'd get an agent to help you, but unfortunately, we're closed.

**Blocked**
P1003: (In-Hour)
According to our records, you asked that this automated system and our website block access to your account, so you'll need to speak to someone. By the way, if you want to unblock your account, the agent can help you do that as well. Hold on while I get someone to help you.

P1003: (Out-Hour)
According to our records, you asked that this automated system and our website block access to your account, so you'll need to speak to someone. By the way, if you want to unblock your account, the agent can help you do that as well. Unfortunately, we're closed.
