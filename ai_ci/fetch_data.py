import boto3
import os


def get_database(project_dir):
    
    if os.path.exists(f'{project_dir}/data/raw/ai_ci_database.dump') == False:
        AccessKey = os.getenv('AWSAccessKey')
        SecretKey = os.getenv('AWSSecretKey')
        bucketname = 'ai_ci' # replace with your bucket name
        filename = 'ai_ci_database.dump' # replace with your object key
        s3 = boto3.resource('s3', aws_access_key_id=AccessKey, aws_secret_access_key=SecretKey)
        s3.Bucket(bucketname).download_file(filename, f'{project_dir}/data/raw/ai_ci_database.dump')
