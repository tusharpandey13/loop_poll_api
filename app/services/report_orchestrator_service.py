from .redis_service import redis_set_status_completed, redis_set_status_running
from .Poll_report_generator_service import Poll_report_generator
from .s3_service import create_presigned_url, upload_file
import os
import threading

def trigger_report_generation_internal(redis_connection_pool, report_id):
    # print("trigger_report_generation started with " + report_id)

    redis_set_status_running(redis_connection_pool, report_id)

    filename = f'${report_id}.csv'

    Poll_report_generator().generate_csv(filename)

    upload_file(filename)
    url = create_presigned_url(object_name=filename)

    redis_set_status_completed(redis_connection_pool, report_id, url)

    os.remove(filename)

def trigger_report_generation(redis_connection_pool, report_id):
    report_gen_thread = threading.Thread(target=trigger_report_generation_internal, name=report_id, args=[redis_connection_pool, report_id])
    report_gen_thread.start()