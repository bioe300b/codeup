import os
import subprocess
import json
import inspect
import requests
import google.colab

class AuthenticationError(Exception):
    pass

class APIError(Exception):
    pass

class HTTPError(Exception):
    pass

def getNewGoogleOauthToken():

    global oauth_token

    google.colab.auth.authenticate_user()
    p_gcloud = subprocess.Popen(['gcloud', 'auth', 'print-access-token'], stdout=subprocess.PIPE)
    oauth_token = p_gcloud.stdout.read()[0:-1].decode('utf-8')

def renewTokenIfOld(oauth_token_info):

    # some renewal criteria
    if 'expires_in' not in oauth_token_info or 'email_verified' not in oauth_token_info or int(oauth_token_info['expires_in']) < 300 or oauth_token_info['email_verified'] != 'true':
        getNewGoogleOauthToken()

def submitCode(question, function):
    """submitCode

    Primary handle to submit code for BioE 300B.

    Usage: submitCode(question, function)

      - question : a number (or string) representing the question being answered
      - function : the function being passed on

    Note: function passed should be invokable without any arguments: function()
          This typically involves the use of default values for named parameters.

    Function takes several seconds to execute as it invokes several Google APIs
      and executes provided function locally on Colaboratory.

    Current implementation is only compatible with Colaboratory.
    """

    # testing function to ensure it runs
    try:
        # function()
        assert hasattr(function,'__call__'),'ERROR: Function input is not callable. Please check to make sure that you have submitted a function as your second argument'
    except Exception as e:
        print('Submitted function error. Code was not submitted to server.')
        print(e)
        raise e

    URL_GOOGLE_OAUTH_TOKEN = 'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token='
    URL_CODE = 'https://bioe-300b-lti.stanford.edu/code'

    # get token info
    if 'oauth_token' not in locals():
        getNewGoogleOauthToken()
    oauth_token_info = requests.get( URL_GOOGLE_OAUTH_TOKEN + oauth_token).json()
    renewTokenIfOld(oauth_token_info)

    # check if oauth threw an error
    if 'error_description' in oauth_token_info:
        getNewGoogleOauthToken()
    oauth_token_info = requests.get( URL_GOOGLE_OAUTH_TOKEN + oauth_token).json()

    # validate email is in form <SUNetID>@stanford.edu
    email = oauth_token_info['email']
    email_s_at = email.split('@')
    email_s_dot = email.split('.')

    if len(email_s_at) != 2 or email_s_at[-1] != 'stanford.edu' or len(email_s_at[0]) > 8 or len(email_s_dot) != 2 or email_s_dot[-1] != 'edu':
        raise AuthenticationError('Stanford Google account (<SUNetID>@stanford.edu) not used. Colab notebook is in wrong Google account.')

    # pack function
    f_source = inspect.getsource(function)

    # post code
    reply = requests.post(URL_CODE, data = {'action' : 'submitCode', 'token': oauth_token, 'question': question, 'code' : f_source})

    if reply.status_code != 200:
        raise HTTPError(reply.status_code)

    replyObj = reply.json()

    if replyObj['result'] != 'ok':
        raise APIError(replyObj['error_text'])

    # execute code
    kwargs = replyObj['kwargs']
    retObj = function(**kwargs)
    retObj_json = json.JSONEncoder().encode(retObj)

    renewTokenIfOld(oauth_token_info)

    # post answer
    reply = requests.post(URL_CODE, data = {'action' : 'submitOutput', 'token' : oauth_token, 'question' : question, 'answer' : retObj_json, 'submitID' : replyObj['submitID']})

    if reply.status_code != 200:
        raise HTTPError

    replyObj = reply.json()

    if replyObj['result'] != 'ok':
        raise APIError(replyObj['error_text'])

    print("Answer correct: " + str(replyObj['correct']))
