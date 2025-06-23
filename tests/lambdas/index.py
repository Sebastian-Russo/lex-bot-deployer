# Add the follow snippet to the end of your Lex Fullfillment Handler
if sessionAttributes.get('test-case'):
    response_string = response.get('message', [{}])[0].get('content', '[no Response>')
    expected_response = sessionAttributes.get('expected_response')
    expected_intent = sessionAttributes.get('expected_intent')

    def is_equal(str1: str, str2: str) -> bool:
        """
        Compares two strings while ignoring case, leading/tailing whitespace, and repeated white spaces.
        """

        def normalize_string(s: str) -> str:
            return ' '.join(s.strip().lower().split())

        return normalize_string(str1) == normalize_string(str2)

    if not is_equal(expected_response, response_string):
        result = 'FAILED'
        sessionAttributes['test-explanation'] = (
            f'Expected response = {expected_response}, got {response_string}'
        )

    elif not is_equal(expected_intent, intent_name):
        result = 'FAILED'
        sessionAttributes['test-explanation'] = (
            f'Expected intent = {expected_intent}, got {intent_name}'
        )

    else:
        result = 'PASSED'
        sessionAttributes['test-explanation'] = (
            'Response and intent match expected values'
        )
        sessionAttributes['test-result'] = result
