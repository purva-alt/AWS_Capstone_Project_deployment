
import boto3, os
from dotenv import load_dotenv
load_dotenv()

sns = boto3.client(
    "sns",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)

def notify(msg):
    sns.publish(
        TopicArn=os.getenv("SNS_TOPIC_ARN"),
        Message=msg,
        Subject="Cloud Bank Alert"
    )

