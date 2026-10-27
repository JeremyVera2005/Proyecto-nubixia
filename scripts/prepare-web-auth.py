"""Prepare the public website stack and authenticated backend update without AWS calls."""
import json,sys,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'.tools/samtranslator'))
os.environ['AWS_DEFAULT_REGION']='us-east-2'
os.environ['AWS_EC2_METADATA_DISABLED']='true'
from samtranslator.yaml_helper import yaml_parse
from samtranslator.translator.transform import transform
source=yaml_parse((root/'infra/template-escolar-aws.yaml').read_text(encoding='utf-8'))
source['Parameters']['UserPoolArn']={'Type':'String','Description':'ARN del user pool Cognito de nubixia-escolar-web'}
source['Globals']['Function']['CodeUri']='s3://nubixia-escolar-deploy-002333107613-use2/comprobantes-serverless-2.0.0-lambda.jar'
source['Resources']['Api']['Properties']['Cors']['AllowHeaders']="'Content-Type,X-API-Key,Authorization'"
source['Resources']['Api']['Properties']['Auth'].update({'DefaultAuthorizer':'UserAccounts','AddDefaultAuthorizerToCorsPreflight':False,'Authorizers':{'UserAccounts':{'UserPoolArn':{'Ref':'UserPoolArn'},'Identity':{'Header':'Authorization'}}}})
source['Resources']['ApiFunction']['Properties'].setdefault('Environment',{}).setdefault('Variables',{})['AUTH_REQUIRED']='true'
source['Resources']['ApiFunction']['Properties']['Events']['Health']['Properties']['Auth']['Authorizer']='NONE'
for statement in source['Resources']['ProcessorFunction']['Properties']['Policies'][0]['Statement']:
 if 'dynamodb:PutItem' in statement['Action']: statement['Action'].append('dynamodb:UpdateItem')
class Policies:
 def load(self):
  return {n:'arn:aws:iam::aws:policy/service-role/'+n for n in ['AWSLambdaBasicExecutionRole','AWSLambdaSQSQueueExecutionRole','AWSLambdaDynamoDBExecutionRole']}
compiled=transform(source,{'CorsOrigin':'http://localhost:4200'},Policies())
previous=json.loads((root/'infra/template-escolar-cloudformation.json').read_text())
for logical in ['ApiFunctionRole','PublisherFunctionRole','ProcessorFunctionRole']:
 compiled['Resources'][logical]['Properties']['RoleName']=previous['Resources'][logical]['Properties']['RoleName']
for logical,policy in [('PublisherFunctionRole','ProjectStreamRead'),('ProcessorFunctionRole','ProjectQueuePoll')]:
 props=compiled['Resources'][logical]['Properties']; props['ManagedPolicyArns']=['arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole']
 props['Policies'].extend(p for p in previous['Resources'][logical]['Properties']['Policies'] if p['PolicyName']==policy)
(root/'infra/template-backend-auth.json').write_text(json.dumps(compiled,indent=2),encoding='utf-8')
ref=lambda name:{'Ref':name}
sub=lambda text:{'Fn::Sub':text}
att=lambda name,field:{'Fn::GetAtt':[name,field]}
res={
 'UserPool':{'Type':'AWS::Cognito::UserPool','DeletionPolicy':'Retain','UpdateReplacePolicy':'Retain','Properties':{'UserPoolName':'nubixia-escolar-users','UserPoolTier':'LITE','UsernameAttributes':['email'],'UsernameConfiguration':{'CaseSensitive':False},'AutoVerifiedAttributes':['email'],'MfaConfiguration':'OFF','EmailConfiguration':{'EmailSendingAccount':'COGNITO_DEFAULT'},'AccountRecoverySetting':{'RecoveryMechanisms':[{'Name':'verified_email','Priority':1}]},'Policies':{'PasswordPolicy':{'MinimumLength':10,'RequireUppercase':True,'RequireLowercase':True,'RequireNumbers':True,'RequireSymbols':False,'TemporaryPasswordValidityDays':1}},'Schema':[{'Name':'email','Required':True,'Mutable':True},{'Name':'name','Required':False,'Mutable':True}],'UserPoolTags':{'Project':'Nubixia','Environment':'school'}}},
 'WebClient':{'Type':'AWS::Cognito::UserPoolClient','Properties':{'UserPoolId':ref('UserPool'),'ClientName':'nubixia-web','GenerateSecret':False,'PreventUserExistenceErrors':'ENABLED','EnableTokenRevocation':True,'ExplicitAuthFlows':['ALLOW_USER_PASSWORD_AUTH','ALLOW_REFRESH_TOKEN_AUTH'],'SupportedIdentityProviders':['COGNITO'],'AccessTokenValidity':15,'IdTokenValidity':15,'RefreshTokenValidity':1,'TokenValidityUnits':{'AccessToken':'minutes','IdToken':'minutes','RefreshToken':'days'},'ReadAttributes':['email','email_verified','name'],'WriteAttributes':['email','name']}},
 'WebBucket':{'Type':'AWS::S3::Bucket','Properties':{'BucketName':sub('nubixia-escolar-web-${AWS::AccountId}-${AWS::Region}'),'PublicAccessBlockConfiguration':{'BlockPublicAcls':True,'BlockPublicPolicy':True,'IgnorePublicAcls':True,'RestrictPublicBuckets':True},'BucketEncryption':{'ServerSideEncryptionConfiguration':[{'ServerSideEncryptionByDefault':{'SSEAlgorithm':'AES256'}}]}}},
 'WebOAC':{'Type':'AWS::CloudFront::OriginAccessControl','Properties':{'OriginAccessControlConfig':{'Name':'nubixia-escolar-web','OriginAccessControlOriginType':'s3','SigningBehavior':'always','SigningProtocol':'sigv4'}}},
 'ApiPath':{'Type':'AWS::CloudFront::Function','Properties':{'Name':'nubixia-escolar-api-path','AutoPublish':True,'FunctionConfig':{'Comment':'Remove only /api prefix for API Gateway demo stage','Runtime':'cloudfront-js-2.0'},'FunctionCode':"function handler(event) { var r=event.request; r.uri=r.uri.replace(/^\\/api(?=\\/|$)/,'') || '/'; return r; }"}},
 'WebCache':{'Type':'AWS::CloudFront::CachePolicy','Properties':{'CachePolicyConfig':{'Name':'nubixia-escolar-assets','DefaultTTL':300,'MaxTTL':86400,'MinTTL':0,'ParametersInCacheKeyAndForwardedToOrigin':{'CookiesConfig':{'CookieBehavior':'none'},'HeadersConfig':{'HeaderBehavior':'none'},'QueryStringsConfig':{'QueryStringBehavior':'none'},'EnableAcceptEncodingGzip':True,'EnableAcceptEncodingBrotli':True}}}},
 'SecurityHeaders':{'Type':'AWS::CloudFront::ResponseHeadersPolicy','Properties':{'ResponseHeadersPolicyConfig':{'Name':'nubixia-escolar-security','SecurityHeadersConfig':{'ContentTypeOptions':{'Override':True},'FrameOptions':{'FrameOption':'DENY','Override':True},'ReferrerPolicy':{'ReferrerPolicy':'no-referrer','Override':True},'StrictTransportSecurity':{'AccessControlMaxAgeSec':31536000,'IncludeSubdomains':True,'Override':True},'ContentSecurityPolicy':{'Override':True,'ContentSecurityPolicy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https://cognito-idp.us-east-2.amazonaws.com https://*.s3.us-east-2.amazonaws.com https://*.s3.amazonaws.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"}}}}},
}
base={'ViewerProtocolPolicy':'redirect-to-https','Compress':True,'ResponseHeadersPolicyId':ref('SecurityHeaders')}
res['Distribution']={'Type':'AWS::CloudFront::Distribution','Properties':{'DistributionConfig':{'Enabled':True,'Comment':'Nubixia escolar frontend y API autenticada','DefaultRootObject':'index.html','PriceClass':'PriceClass_100','HttpVersion':'http2','IPV6Enabled':True,'ViewerCertificate':{'CloudFrontDefaultCertificate':True},'Origins':[{'Id':'assets','DomainName':att('WebBucket','RegionalDomainName'),'S3OriginConfig':{'OriginAccessIdentity':''},'OriginAccessControlId':ref('WebOAC')},{'Id':'api','DomainName':'0qx6ww77nl.execute-api.us-east-2.amazonaws.com','OriginPath':'/demo','CustomOriginConfig':{'OriginProtocolPolicy':'https-only','OriginSSLProtocols':['TLSv1.2'],'HTTPSPort':443},'OriginCustomHeaders':[{'HeaderName':'X-API-Key','HeaderValue':ref('ApiKeyValue')}]}],'DefaultCacheBehavior':{**base,'TargetOriginId':'assets','AllowedMethods':['GET','HEAD','OPTIONS'],'CachedMethods':['GET','HEAD'],'CachePolicyId':ref('WebCache')},'CacheBehaviors':[{**base,'PathPattern':'/api/*','TargetOriginId':'api','AllowedMethods':['GET','HEAD','OPTIONS','PUT','PATCH','POST','DELETE'],'CachedMethods':['GET','HEAD'],'CachePolicyId':'4135ea2d-6df8-44a3-9df3-4b5a84be39ad','OriginRequestPolicyId':'b689b0a8-53d0-40ab-baf2-68738e2966ac','FunctionAssociations':[{'EventType':'viewer-request','FunctionARN':att('ApiPath','FunctionARN')}]}]},'Tags':[{'Key':'Project','Value':'Nubixia'}]}}
res['WebBucketPolicy']={'Type':'AWS::S3::BucketPolicy','Properties':{'Bucket':ref('WebBucket'),'PolicyDocument':{'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'cloudfront.amazonaws.com'},'Action':'s3:GetObject','Resource':sub('${WebBucket.Arn}/*'),'Condition':{'StringEquals':{'AWS:SourceArn':sub('arn:${AWS::Partition}:cloudfront::${AWS::AccountId}:distribution/${Distribution}')}}},{'Effect':'Deny','Principal':'*','Action':'s3:*','Resource':[att('WebBucket','Arn'),sub('${WebBucket.Arn}/*')],'Condition':{'Bool':{'aws:SecureTransport':'false'}}}]}}}
web={'AWSTemplateFormatVersion':'2010-09-09','Description':'Nubixia - sitio publico HTTPS y cuentas Cognito Lite','Parameters':{'ApiKeyValue':{'Type':'String','NoEcho':True,'MinLength':20,'MaxLength':128}},'Resources':res,'Outputs':{'WebsiteUrl':{'Value':sub('https://${Distribution.DomainName}')},'DistributionId':{'Value':ref('Distribution')},'WebBucketName':{'Value':ref('WebBucket')},'UserPoolId':{'Value':ref('UserPool')},'UserPoolArn':{'Value':att('UserPool','Arn')},'ClientId':{'Value':ref('WebClient')}}}
(root/'infra/template-web-auth.json').write_text(json.dumps(web,indent=2),encoding='utf-8')
print('Preparadas plantillas web (9 recursos) y backend con Cognito. Sin llamadas a AWS.')
