import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
t=json.loads((root/'infra/template-backend-auth.json').read_text())
t['Description']='Nubixia escolar - web HTTPS y API con Cognito, sin CloudFront'
t['Parameters']['UserPoolId']={'Type':'String','Description':'Pool Cognito conservado del despliegue web'}
t['Resources']['WebClient']=json.loads((root/'infra/template-web-auth.json').read_text())['Resources']['WebClient']
t['Resources']['WebClient']['Properties']['UserPoolId']={'Ref':'UserPoolId'}
api=t['Resources']['Api']['Properties']
t['Resources']['ApiFunction']['Properties']['Code']['S3Key']='comprobantes-serverless-2.0.1-lambda.jar'
api['BinaryMediaTypes']=['*/*']
api['MinimumCompressionSize']=1024
body=api['Body']
for path in ['/comprobantes','/comprobantes/{id}','/comprobantes/{id}/archivos/{extension}']:
 for method,definition in body['paths'][path].items():
  if method!='options' and isinstance(definition,dict):
   definition['security']=[{'UserAccounts':[]}]
for path in ['/','/{asset}']:
 body['paths'][path]={'get':{'security':[],'responses':{'200':{'description':'Frontend asset'}},'x-amazon-apigateway-integration':{'type':'aws_proxy','httpMethod':'POST','uri':{'Fn::Sub':['arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${__FunctionArn__}/invocations',{'__FunctionArn__':{'Fn::GetAtt':['ApiFunction','Arn']}}]}}}}
logical=[k for k in t['Resources'] if k.startswith('ApiDeployment')][0]
newlogical='ApiDeploymentWebCognitoV2'
t['Resources'][newlogical]=t['Resources'].pop(logical)
def replace(value):
 if isinstance(value,dict):
  return {k:(newlogical if k=='Ref' and v==logical else replace(v)) for k,v in value.items()}
 if isinstance(value,list):return [replace(v) for v in value]
 return value
t=replace(t)
for name,path in [('PublicHome','/'),('PublicAsset','/*')]:
 t['Resources'][name+'Permission']={'Type':'AWS::Lambda::Permission','Properties':{'Action':'lambda:InvokeFunction','FunctionName':{'Ref':'ApiFunction'},'Principal':'apigateway.amazonaws.com','SourceArn':{'Fn::Sub':f'arn:${{AWS::Partition}}:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{Api}}/*/GET{path}'}}}
env=t['Resources']['ApiFunction']['Properties']['Environment']['Variables']
env['COGNITO_USER_POOL_ID']={'Ref':'UserPoolId'};env['COGNITO_CLIENT_ID']={'Ref':'WebClient'}
t['Outputs']['WebsiteUrl']={'Value':{'Fn::Sub':'https://${Api}.execute-api.${AWS::Region}.amazonaws.com/demo/'}}
t['Outputs']['ClientId']={'Value':{'Ref':'WebClient'}}
t['Outputs']['UserPoolId']={'Value':{'Ref':'UserPoolId'}}
# A JWT replaces the shared API key on business routes. Keep the old key resources for rollback.
for gateway_response in body.get('x-amazon-apigateway-gateway-responses',{}).values():pass
(root/'infra/template-web-api-auth.json').write_text(json.dumps(t,indent=2),encoding='utf-8')
print('Preparada actualizacion HTTPS sobre API Gateway; no crea CloudFront ni nuevos roles.')
