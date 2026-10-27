"""Compile the school SAM template locally without granting a cloud SAM transform permission."""
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".tools" / "samtranslator"))
os.environ["AWS_DEFAULT_REGION"] = "us-east-2"
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
from samtranslator.yaml_helper import yaml_parse
from samtranslator.translator.transform import transform

class LocalManagedPolicies:
    def load(self):
        return {
            "AWSLambdaBasicExecutionRole": "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "AWSLambdaSQSQueueExecutionRole": "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole",
            "AWSLambdaDynamoDBExecutionRole": "arn:aws:iam::aws:policy/service-role/AWSLambdaDynamoDBExecutionRole",
        }

template = yaml_parse((ROOT / "infra" / "template-escolar-aws.yaml").read_text(encoding="utf-8"))
compiled = transform(template, {"CorsOrigin": "http://localhost:4200"}, LocalManagedPolicies())
assert "Transform" not in compiled
assert "Globals" not in compiled
for logical in ["ApiFunctionRole", "PublisherFunctionRole", "ProcessorFunctionRole"]:
    role = compiled["Resources"][logical]
    # Preserve the already approved IAM ARN patterns even when retrying with another stack name.
    role["Properties"]["RoleName"] = "nubixia-escolar-" + logical + "-demo"
# Replace broad event-source managed policies with inline permissions on the project's queue/stream.
for logical in ["PublisherFunctionRole", "ProcessorFunctionRole"]:
    compiled["Resources"][logical]["Properties"]["ManagedPolicyArns"] = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    ]
compiled["Resources"]["PublisherFunctionRole"]["Properties"]["Policies"].append({
    "PolicyName": "ProjectStreamRead",
    "PolicyDocument": {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["dynamodb:DescribeStream", "dynamodb:GetRecords", "dynamodb:GetShardIterator"],
         "Resource": {"Fn::GetAtt": ["Documents", "StreamArn"]}},
        {"Effect": "Allow", "Action": "dynamodb:ListStreams", "Resource": "*",
         "Condition": {"StringEquals": {"aws:RequestedRegion": "us-east-2"}}}
    ]}
})
compiled["Resources"]["ProcessorFunctionRole"]["Properties"]["Policies"].append({
    "PolicyName": "ProjectQueuePoll",
    "PolicyDocument": {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
         "Resource": {"Fn::GetAtt": ["Queue", "Arn"]}}
    ]}
})
assert all(not r["Type"].startswith("AWS::Serverless::") for r in compiled["Resources"].values())
result = ROOT / "infra" / "template-escolar-cloudformation.json"
result.write_text(json.dumps(compiled, indent=2), encoding="utf-8")
print(f"CloudFormation estandar generado: {len(compiled['Resources'])} recursos, sin Transform ni Globals.")
print("No se solicitaron credenciales ni se llamo a AWS.")
