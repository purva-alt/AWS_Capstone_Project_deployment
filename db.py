<<<<<<< HEAD
import boto3, os
from dotenv import load_dotenv
load_dotenv()

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)

users = dynamodb.Table("Users")
accounts = dynamodb.Table("Accounts")
transactions = dynamodb.Table("Transactions")
=======
import boto3, os
from dotenv import load_dotenv
load_dotenv()

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)

users = dynamodb.Table("Users")
accounts = dynamodb.Table("Accounts")
transactions = dynamodb.Table("Transactions")
>>>>>>> da2098cc04425f3a7a89fbc75c10a93eb971733d
