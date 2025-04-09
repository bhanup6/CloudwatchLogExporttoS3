import sqlite3
import boto3
from datetime import datetime
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Database Configuration
DB_PATH = 'database/exports.db'
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def get_logs_client(source_account_id=None):
    """Get logs client with optional cross-account access"""
    if source_account_id:
        creds = assume_role(source_account_id)
        return boto3.client(
            'logs',
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken'],
            region_name=AWS_REGION
        )
    else:
        return boto3.client('logs', region_name=AWS_REGION)

def initialize_database():
    """Create database table if not exists"""
    with sqlite3.connect(DB_PATH,timeout=15) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS export_status (
                task_id TEXT PRIMARY KEY,
                status TEXT,
                start_time TEXT,
                end_time TEXT,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                transfer_time REAL, 
                log_size INTEGER ,                         
                log_group_name TEXT,
                source_account_id TEXT
            )
        ''')
        conn.commit()
def log_export_task(task_id,log_group_name, start_time, end_time,source_account_id):
    """Log new export task to database"""
    with sqlite3.connect(DB_PATH,timeout=15) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO export_status 
            (task_id, log_group_name, status, start_time, end_time,source_account_id)
            VALUES (?,?, ?, ?, ?, ?)
        ''', (task_id ,log_group_name, 'PENDING', start_time, end_time,source_account_id))
        conn.commit()
def get_export_statuses():
    """Retrieve all export statuses from database"""
    with sqlite3.connect(DB_PATH,timeout=15) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM export_status ORDER BY last_checked DESC')
        return c.fetchall()

def update_export_status(task_id):

    """Update status for a single export task"""
    with sqlite3.connect(DB_PATH,timeout=15) as conn:
                c = conn.cursor()
                c.execute('SELECT source_account_id FROM export_status WHERE task_id = ?', (task_id,))
                result = c.fetchone()
                if not result:
                     print(f"No task found with ID: {task_id}")
                     return False
                source_account_id = result[0]
    logs = get_logs_client(source_account_id)
    try:
        response = logs.describe_export_tasks(taskId=task_id)
        #print(response)
        if response.get('exportTasks'):
            task = response['exportTasks'][0]
            status = task.get('status', {}).get('code', 'UNKNOWN')
            log_group_name = task.get('logGroupName', 'N/A')
            print(log_group_name)
            log_group_size_GB=get_log_group_size(log_group_name,source_account_id)
            print(log_group_size_GB)
            # Handle timestamps
            # Get timestamps from executionInfo (not fromTime/toTime)
            from_time = task.get('executionInfo', {}).get('creationTime',0)
            to_time  = task.get('executionInfo', {}).get('completionTime',0)
            print(from_time,to_time)
            start_time = datetime.fromtimestamp(from_time/1000).strftime('%Y-%m-%d %H:%M:%S') if from_time else 'N/A'
            end_time = datetime.fromtimestamp(to_time/1000).strftime('%Y-%m-%d %H:%M:%S') if to_time else 'N/A'
            transfer_time = (to_time - from_time)/1000 if from_time and to_time else 0.0
            #stored_bytes=get_log_group_size(log_group_name)
            time.sleep(3)
            c.execute('''
                    UPDATE export_status 
                    SET status=?, start_time=?, end_time=?, transfer_time=?,log_size=?
                    WHERE task_id=?
                ''', (status, start_time, end_time, transfer_time,log_group_size_GB, task_id))
            conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating {task_id}: {str(e)}")
        return False
def get_log_group_size(log_group_name,source_account_id):

    # Create a CloudWatch Logs client
    logs = get_logs_client(source_account_id)
    try:
        # Describe the log group
        response = logs.describe_log_groups(logGroupNamePrefix=log_group_name)
        
        # Find the log group and get its size
        for log_group in response.get('logGroups', []):
            if log_group['logGroupName'] == log_group_name:
                stored_bytes = log_group.get('storedBytes', 0)
                print(f"Log Group: {log_group_name}")
                print(f"Stored Bytes: {stored_bytes}")
                print(f"Size in MB: {stored_bytes / 1024 / 1024:.2f} MB")
                print(f"Size in MB: {stored_bytes / 1024:.2f} KB")
                print(f"Size in GB: {stored_bytes / 1024 / 1024 / 1024:.2f} GB")
                size_in_gb = stored_bytes / 1024 / 1024   # Convert bytes to GB
                return round(size_in_gb, 2)  # Round to 2 decimal places
                #return {stored_bytes / 1024 / 1024 / 1024:.2f}
        
        print(f"Log group '{log_group_name}' not found.")
    except Exception as e:
        print(f"Error fetching log group size: {e}")

def assume_role(source_account_id):
    """Assume role in source account"""
    sts = boto3.client('sts')
    role_arn = f"arn:aws:iam::{source_account_id}:role/LogExportRole"
    
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="LogExportSession"
        )
        print(response)
        return response['Credentials']
    except Exception as e:
        print(f"Assume role failed for {source_account_id}: {str(e)}")
        return None