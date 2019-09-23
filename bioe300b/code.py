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

    # testing function to ensure it runs
    try:
        function()
    except Exception as e:
        print('Submitted function error. Code was not submitted to server.')
    print(e)
    raise e

    URL_GOOGLE_OAUTH_TOKEN = 'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token='
    URL_CODE = 'https://web.stanford.edu/group/bil/cgi-bin/300b/codeHandler.py'

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
