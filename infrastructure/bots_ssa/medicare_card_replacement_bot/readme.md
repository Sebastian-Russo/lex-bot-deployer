Entry
MEDICARE_CARD_REPLACEMENT selected in ssa menu

Connect Invoke Lex bot
customer prompt / bot initialization
P1045: Okay. Medicare Replacement Card. One moment. Did you know you can request a Replacement Medicare Card by going online and using your My S S A account? Go to w w w dot social security dot g o v and select Sign in.
P1173: Before I can access your records, I will need to ask a question or two to verify who you are. Social Security is allowed to collect this information under the Social Security Act and the collect meets the requirements of the Paperwork Reduction Act under OMB number 0 9 6 0 0 5 9 6. The whole process should take about four minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say continue.

Bot invocation
more information > Privacy and Paperowrk Reduction Act #todo make a prompt for this
continue > next step

P1010: Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?

no > P1022: (In-Hour) Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.
no > (Out-Hour) P1022: Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.
yes > next step

Module SSN: Please provide your Social Security number.
success > next step
failure > retry SSN intent/slot

Module DOB: Please provide your Day of Birth.
success > next step
failure > retry DOB intent/slot

Module Name: Please provide your First Name. Last Name.
success > next step
failure > retry Name intent/slot

P1046: THank you. I've got everything I need. Hold on while I submit this.

Submit Request
Error > (In-Hour) P9011: Sorry, I'm having trouble processing this request. Hold on while I get someone to help you.
Error > (Out-Hour) P9011: Sorry, I'm having trouble processing this request. Normally I'd get an agent to help you, but you can either hang up and use your online my s s a account or call back during office hours.
Block > (In-Hour) P1003: According to our records, you asked that this automated system and our website block access to your account, so you'll need to speak to someone. By the way, if you want to unblock your account, the agent can help you do that as well. Hold on while I get someone to help you.
Block > (Out-Hour) P1003: According to our records, you asked that this automated system and our website block access to your account, so you'll need to speak to someone. By the way, if you want to unblock your account, the agent can help you do that as well. You can either hang up and use your online my s s a account or call back during office hours.
Success > P1047: Alright. We're all set. You should receive your replacement Medicare card in the mail within four weeks. If you're finished, feel free to hang up. Otherwise, just ahng on and I'll take you back to the Main Menu.
