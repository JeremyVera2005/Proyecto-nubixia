import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=json.loads((root/'infra/deployment-role-policy.json').read_text(encoding='utf-8-sig'))
account='002333107613'
p['Statement'] += [
 {'Sid':'CreateSchoolUserPool','Effect':'Allow','Action':'cognito-idp:CreateUserPool','Resource':'*','Condition':{'StringEquals':{'aws:RequestTag/Project':'Nubixia','aws:RequestedRegion':'us-east-2'}}},
 {'Sid':'ManageSchoolUserPool','Effect':'Allow','Action':['cognito-idp:DescribeUserPool','cognito-idp:UpdateUserPool','cognito-idp:DeleteUserPool','cognito-idp:CreateUserPoolClient','cognito-idp:DescribeUserPoolClient','cognito-idp:UpdateUserPoolClient','cognito-idp:DeleteUserPoolClient','cognito-idp:GetUserPoolMfaConfig','cognito-idp:SetUserPoolMfaConfig','cognito-idp:ListTagsForResource','cognito-idp:TagResource','cognito-idp:UntagResource'],'Resource':f'arn:aws:cognito-idp:us-east-2:{account}:userpool/*','Condition':{'StringEquals':{'aws:ResourceTag/Project':'Nubixia'}}},
 {'Sid':'CreateTaggedSchoolDistribution','Effect':'Allow','Action':'cloudfront:CreateDistribution','Resource':'*','Condition':{'StringEquals':{'aws:RequestTag/Project':'Nubixia'}}},
 {'Sid':'TagNewSchoolDistribution','Effect':'Allow','Action':'cloudfront:TagResource','Resource':f'arn:aws:cloudfront::{account}:distribution/*','Condition':{'StringEquals':{'aws:RequestTag/Project':'Nubixia'}}},
 {'Sid':'ManageSchoolDistribution','Effect':'Allow','Action':['cloudfront:GetDistribution','cloudfront:GetDistributionConfig','cloudfront:UpdateDistribution','cloudfront:DeleteDistribution','cloudfront:CreateInvalidation','cloudfront:GetInvalidation','cloudfront:ListTagsForResource','cloudfront:TagResource','cloudfront:UntagResource'],'Resource':f'arn:aws:cloudfront::{account}:distribution/*','Condition':{'StringEquals':{'aws:ResourceTag/Project':'Nubixia'}}},
 {'Sid':'CreateSchoolPathFunction','Effect':'Allow','Action':'cloudfront:CreateFunction','Resource':'*'},
 {'Sid':'ManageSchoolPathFunction','Effect':'Allow','Action':['cloudfront:DescribeFunction','cloudfront:GetFunction','cloudfront:UpdateFunction','cloudfront:PublishFunction','cloudfront:DeleteFunction','cloudfront:ListTagsForResource'],'Resource':f'arn:aws:cloudfront::{account}:function/nubixia-escolar-api-path'},
 {'Sid':'SchoolDistributionConfiguration','Effect':'Allow','Action':['cloudfront:CreateOriginAccessControl','cloudfront:GetOriginAccessControl','cloudfront:UpdateOriginAccessControl','cloudfront:DeleteOriginAccessControl','cloudfront:CreateCachePolicy','cloudfront:GetCachePolicy','cloudfront:GetCachePolicyConfig','cloudfront:UpdateCachePolicy','cloudfront:DeleteCachePolicy','cloudfront:CreateResponseHeadersPolicy','cloudfront:GetResponseHeadersPolicy','cloudfront:GetResponseHeadersPolicyConfig','cloudfront:UpdateResponseHeadersPolicy','cloudfront:DeleteResponseHeadersPolicy'],'Resource':'*'}
]
path=root/'infra/deployment-role-policy-web.json'
path.write_text(json.dumps(p,indent=2),encoding='utf-8')
size=len(json.dumps(p,separators=(',',':')))
print(f'Politica preparada: {len(p["Statement"])} statements, {size} caracteres compactos; no aplicada en AWS.')
assert size<=6144
