# Add the follow snippet to the end of your Lex Fullfillment Handler

**What it does**

- The close_response method builds and returns the final response object.

- The test code needs to be added just before the return statement in this method.

- The test code checks session attributes, compares expected responses with actual responses, and sets test results.

**How to use it**

1. Modify the close_response method to capture the response object before returning it.
2. Add the test code to check and validate responses if the test-case attribute is present.
3. Return the response object after the test code has run.
