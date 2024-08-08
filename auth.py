from smart_cdss_api.conf.conf import secret_token

def generatePolicy(principalId, effect, methodArn):
    authResponse = {}
    authResponse['principalId'] = principalId
 
    if effect and methodArn:
        policyDocument = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': 'FirstStatement',
                    'Action': 'lambda:InvokeFunction',
                    'Effect': effect,
                    'Resource': methodArn
                }
            ]
        }
 
        authResponse['policyDocument'] = policyDocument
 
    return authResponse
 
def lambda_handler(event, context):
    try:
        #token = event['authorizationToken']
        #if token == secret_token:
        return generatePolicy('user', 'Allow', event['methodArn'])
 
        return generatePolicy(None, 'Deny', event['methodArn'])
 
    except ValueError as err:
        # Deny access if the token is invalid
        return generatePolicy(None, 'Deny', event['methodArn'])
