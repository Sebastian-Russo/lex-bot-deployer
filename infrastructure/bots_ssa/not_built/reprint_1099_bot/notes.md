P1004: Do you have a foregin Address?
-yes > (On-Hour) P9032: In-Hour: Our autmated system cannot process a 10 99 or 10 42 for you. You can either hang up and use your online my s s a account or hold on and I will get someone to help you. #queue transfer to agent
-yes > (Off-Hour) P9032: Off-Hour: Our autmated system cannot process a 10 99 or 10 42 for you. You can either hang up and use your online my s s a account or call back during office hours. #queue transfer to agent
-no > (move on to next question)

Are you calling to get a replacement 10 99 for the {20yy} tax year?
--no > Are you calling to get a replacement 10 99 for any of the prior 5 years?
------no > #flow transfer to main menu
------yes (or answers with one of the last five years) move on to next questions
--yes > moves on to next question

P1009: Alright. Before I can access your records, I'll need to ask a question or two to verify who you are. Social Security is allowed to cllect this information under the Social Security Act, and the collection meets the requirements of the Paperwork Reduction Act under OMB numbers 09600596 and 09600583. The whole process should take about six minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say, continue.
-more information > (place holder)
-continue > (place holder)
