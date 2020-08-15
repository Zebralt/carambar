import re
import textwrap
import traceback
from contextlib import contextmanager


"""
Some things can't be tested without a human being there.
A set of tools to run tests with an Oracle (user).

Merely resorts to prompt the user for a test,
describing the test's purpose,
running the behavior,
then asking the user to confirm whether the test has completed succesfully.
"""


def get_default_answer(ans: str) -> str:
    for a in ans:
        if a == a.upper():
            return a


def parse_action(action: str) -> (str, list):

    single_token_rgx = r'!([a-zA-Z0-9_-]+)'
    multi_token_rgx = r'!\{(.*?)\}'

    keywords = []

    keywords.extend((r.group(1), r.span()[0]) for r in re.finditer(single_token_rgx, action))
    keywords.extend((r.group(1), r.span()[0]) for r in re.finditer(multi_token_rgx, action))
    keywords = sorted(keywords, key = lambda pair: pair[1])
    if keywords:
        keywords, _ = zip(*keywords)

    text = action
    text = re.sub(single_token_rgx, r'\1', text)
    text = re.sub(multi_token_rgx, r'\1', text)

    text = textwrap.wrap(text, width=50)
    text = '\n  '.join(text)

    return text, keywords


def prompt(msg: str, ans: str = '') -> str:

    """
    Prints a user prompt. Process the user's answer according to the specified parameters.
    Returns the user answer (string character).
    
    -> Used without options (ans), this is meant to only notify the user of some information
       before continuing on with the rest of the program. (Press Enter to continue)
    -> ans is meant to be a list (or string) of one-letter possible answers; the user must
       provide an answer contained in the list, or they will be prompted again until they do so.
    -> You can set a default answer by having it in uppercase in the `ans` array:
       >>> prompt('Proceed ?', 'Yn')
       The first uppercase answer found in the answer array will be designated as the default answer.
       A default answer allows the user to directly press enter instead of having to input anything.
    """

    user_msg = ' '.join((msg, '(%s)' % ''.join(ans) if bool(ans) else '(Press Enter to continue)')) + ' '
    
    user_ans = input(user_msg).strip()

    if not ans:
        return
        
    default_answer = get_default_answer(ans)

    if default_answer is not None and not user_ans:
        return default_answer

    while len(user_ans) != 1 or user_ans not in ans:
        user_ans = input(user_msg)
        if default_answer is not None and not user_ans:
            return default_answer

    return user_ans


def yesno(msg: str):
    """Ask a yes-no question, and returns whether the answer was 'yes'."""
    return prompt(msg, 'Yn') == 'Y'


@contextmanager
def Test(action: str, question: str = ''):

    """
    Start a human-driven test. First prompt the user with the description of what the test is about,
    run the test,
    then have the user assess whether the test has succeeded through a second prompt.
    Raise an AssertionError otherwise.

    :param action:
        The 'action' that the test will perform and that the user should evaluate. 
        This should be a string describing the action, eg "print yellow text then download data to a given file."
    :param question:
        If only 'action' is provided, both pre-test and post-test prompts will show the same text.
        This parameter allows you to provide a different text for the post-test prompt.
    """
    
    color = '\033[38;2;250;180;40m'
    action, keywords = parse_action(action)
    desc = color + '{ This program will now %s. }\033[m' % action
    
    if not question:
        question = 'Did the program %s ?' % action
    question = color + '{ %s }\033[m' % question
    
    name = ' '.join(keywords)
    
    if not name:
        name = action[:30]
        if len(action) > 30:
            name = name[:29] + '/'
    
    print('\033[95m{ Oracle Test }\033[m')
    prompt(desc)
    
    #
    yield
    #

    try:
        assert yesno(question)
    
    except AssertionError:
        print('\033[91m%s\033[m' % '[ Test { %s } failed. ]' % (name))
        raise

    print('\033[92m%s\033[m' % '[ Test { %s } was a success. ]' % (name))


def test_Test():
    with Test('!{print %s}' % repr('a')):
        print('a')


def run_tests(env):

    """
    Run test functions in a given environment dict not unlike pytest.
    Keep track of successes and failures, including error messages.
    Can be used to run test functions found in a module this way:
    >>> run_tests(globals())
    """

    results = []

    for key, value in env.items():

        if not key.startswith('test_'):
            continue

        try:
            value()
            results += [(key, '.', None)]
        except Exception:
            results += [(key, 'F', traceback.format_exc())]

    print(env['__file__'], '{', len([r for r in results if r[1] == '.']), '/', len(results), '}')

    for name, result, message in results:
        print('- {:30} {}'.format(name, result))
        if message is not None:
            print('\033[97m' + '    ' + message.replace('\n', '\n    ') + '\033[m')
        


if __name__ == "__main__":
    test_Test()