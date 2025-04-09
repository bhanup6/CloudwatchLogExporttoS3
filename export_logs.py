from datetime import datetime
from utils import get_logs_client, log_export_task, initialize_database,get_log_group_size

def export_all_logs(source_account_id, log_group_name):
    """Export logs for a specific log group"""
    logs = get_logs_client(source_account_id)
    #get_log_group_size(log_group_name,source_account_id)
    try:
        response = logs.create_export_task(
            logGroupName=log_group_name,
            fromTime=0,  # 1970-01-01
            to=int(datetime.now().timestamp() * 1000),
            destination='vpc-flow-logs-test001',
            destinationPrefix=f'account-{source_account_id}/'
        )
        
        task_id = response['taskId']
        log_export_task(
            task_id=task_id,
            log_group_name=log_group_name,
            start_time=0,
            end_time=int(datetime.now().timestamp() * 1000),
            source_account_id=source_account_id
        )
        return task_id
    except Exception as e:
        print(f"Export failed: {e}")
        return None

if __name__ == "__main__":
    initialize_database()
    task_id = export_all_logs(337909782124,'/aws/lambda/EBSVolume')
    if task_id:
        print(f"Export started with Task ID: {task_id}")
