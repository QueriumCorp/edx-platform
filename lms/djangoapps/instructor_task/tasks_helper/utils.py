from eventtracking import tracker
from lms.djangoapps.instructor_task.models import ReportStore
from util.file import course_filename_prefix_generator

from logging import getLogger
logger = getLogger(__name__)

REPORT_REQUESTED_EVENT_NAME = u'edx.instructor.report.requested'

# define value to use when no task_id is provided:
UNKNOWN_TASK_ID = 'unknown-task_id'

# define values for update functions to use to return status to perform_module_state_update
UPDATE_STATUS_SUCCEEDED = 'succeeded'
UPDATE_STATUS_FAILED = 'failed'
UPDATE_STATUS_SKIPPED = 'skipped'


def upload_csv_to_report_store(rows, csv_name, course_id, timestamp, config_name='GRADES_DOWNLOAD'):
    """
    Upload data as a CSV using ReportStore.

    Arguments:
        rows: CSV data in the following format (first column may be a
            header):
            [
                [row1_colum1, row1_colum2, ...],
                ...
            ]
        csv_name: Name of the resulting CSV
        course_id: ID of the course

    Returns:
        report_name: string - Name of the generated report
    """
    """
    fuka apr-2020: for KU, remove the %H and %M from the filename timestamp
    """
    if str(course_id).find("course-v1:KU+") >= 0:
        ts=timestamp.strftime("%Y-%m-%d")
    else:
        ts=timestamp.strftime("%Y-%m-%d-%H%M")
    logger.info("utils.py upload_csv_to_report_store course_id={c} ts={t}".format(c=course_id,t=ts))
    report_store = ReportStore.from_config(config_name)
    report_name = u"{course_prefix}_{csv_name}_{timestamp_str}.csv".format(
        course_prefix=course_filename_prefix_generator(course_id),
        csv_name=csv_name,
        timestamp_str=ts
    )

    report_store.store_rows(course_id, report_name, rows)
    tracker_emit(csv_name)
    return report_name


def tracker_emit(report_name):
    """
    Emits a 'report.requested' event for the given report.
    """
    tracker.emit(REPORT_REQUESTED_EVENT_NAME, {"report_type": report_name, })

