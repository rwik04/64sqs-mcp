import boto3
import pickle
import os
import sys
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def load_nodes_from_file(
    s3_path: str,
    bucket_name: str = None,
    aws_access_key: str = None,
    aws_secret_access_key: str = None
) -> List[Any]:
    """
    Load nodes from a binary file stored in S3, without saving locally.

    Args:
        s3_path: S3 path to the binary file (key in S3)
        bucket_name: S3 bucket name (optional, defaults to Config.AWS_BUCKET_NAME)
        aws_access_key: AWS access key (optional, defaults to Config.AWS_ACCESS_KEY)
        aws_secret_access_key: AWS secret access key (optional, defaults to Config.AWS_SECRET_ACCESS_KEY)

    Returns:
        List of loaded nodes
    """
    config = Config()
    
    bucket = bucket_name or config.AWS_BUCKET_NAME
    access_key = aws_access_key or config.AWS_ACCESS_KEY
    secret_key = aws_secret_access_key or config.AWS_SECRET_ACCESS_KEY

    # print(f"Loading nodes directly from S3: s3://{bucket}/{s3_path}")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    try:
        response = s3.get_object(Bucket=bucket, Key=s3_path)
        data = response['Body'].read()
        return pickle.loads(data)
    except Exception as e:
        # print(f"Error loading nodes from S3 {bucket}/{s3_path}: {str(e)}")
        return []

def load_summary_file(
    s3_path: str,
    bucket_name: str = None,
    aws_access_key: str = None,
    aws_secret_access_key: str = None
) -> str:
    """
    Load summary content from a file stored in S3, without saving locally.

    Args:
        bucket_name: S3 bucket name
        s3_path: S3 path to the summary file (should not include bucket name)
        aws_access_key: AWS access key
        aws_secret_access_key: AWS secret access key

    Returns:
        Summary content as string
    """
    config = Config()

    bucket = bucket_name or config.AWS_BUCKET_NAME
    access_key = aws_access_key or config.AWS_ACCESS_KEY
    secret_key = aws_secret_access_key or config.AWS_SECRET_ACCESS_KEY

    # print(f"Loading summary from S3: s3://{bucket}/{s3_path}")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    
    try:
        response = s3.get_object(Bucket=bucket, Key=s3_path)
        data = response['Body'].read()
        return data.decode('utf-8') if isinstance(data, bytes) else data
    except Exception as e:
        # print(f"Error loading summary from S3 {bucket}/{s3_path}: {str(e)}")
        return ""

def get_file_paths_for_project(
    base_path: str,
    client: str,
    project_id: str,
    filename: str
) -> Dict[str, str]:
    """
    Get all relevant file paths for a project.

    Args:
        base_path: Base path for local storage
        client: Client identifier
        project_id: Project identifier
        filename: Filename

    Returns:
        Dictionary of file paths
    """
    project_base = os.path.join(base_path, client, project_id)
    return {
        'uploaded_files': os.path.join(project_base, 'uploaded_files', filename),
        'list_index_files': os.path.join(project_base, 'list_index_files', filename),
        'vector_index_files': os.path.join(project_base, 'vector_index_files', filename),
        'summary_files': os.path.join(project_base, 'summary_files', filename),
        'faq_files': os.path.join(project_base, 'FAQ_files', filename)
    }

def file_exists(
    s3_path: str,
    bucket_name: str = None,
    aws_access_key: str = None,
    aws_secret_access_key: str = None
) -> bool:
    """
    Check if a file exists in S3.

    Args:
        bucket_name: S3 bucket name
        s3_path: S3 path to the file
        aws_access_key: AWS access key
        aws_secret_access_key: AWS secret access key

    Returns:
        True if file exists, False otherwise
    """
    config = Config()
    
    bucket = bucket_name or config.AWS_BUCKET_NAME
    access_key = aws_access_key or config.AWS_ACCESS_KEY
    secret_key = aws_secret_access_key or config.AWS_SECRET_ACCESS_KEY

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    try:
        s3.head_object(Bucket=bucket, Key=s3_path)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    config = Config()
    filenames = [
        "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    ]
    for file in filenames:
        print(load_summary_file(s3_path=f"{config.AWS_CLIENT_ID}/{config.AWS_PROJECT_ID}/summary_files/{file}/summary.md"))