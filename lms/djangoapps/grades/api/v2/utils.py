from django.conf import settings

from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.course_data import CourseData


from opaque_keys.edx.keys import CourseKey, UsageKey
from common.djangoapps.third_party_auth.lti_consumers.willolabs.exceptions import LTIBusinessRuleError


import logging
log = logging.getLogger(__name__)

def parent_usagekey(
    user,
    course_id=None, 
    course_key=None,
    usage_id=None, 
    usage_key=None, 
    usage_key_string=None
    ):
    """
    Returns a dict containing:
        - the url of the homework assignment containing the usage_key that was passed.
        - a grade dictionary for the homework assignment
    This method assumes that the usage_key passed points to a homework problem.

    example usage_key_string: block-v1:ABC+OS9471721_9626+01+type@swxblock+block@c081d7653af211e98379b7d76f928163

    example return:
    {
        'grades': {
            'section_attempted_graded': True, 
            'section_grade_possible': 17.0, 
            'section_grade_earned': 0.0, 
            'section_grade_percent': 0.0
            },
        'url': u'https://dev.roverbyopenstax.org/courses/course-v1:ABC+OS9471721_9626+01/courseware/c0a9afb73af311e98367b7d76f928163/c8bc91313af211e98026b7d76f928163'
    }
    """
    if course_key is None and course_id is not None:
        course_key = CourseKey.from_string(course_id)

    if usage_key is None and usage_id is not None:
        usage_key = UsageKey.from_string(usage_id)
    else:
        if usage_key is None and usage_key_string is not None:
            usage_key = UsageKey.from_string(usage_key_string)

    if course_key is None:
        raise LTIBusinessRuleError("Did not receive a valid course_key object nor identifier.")

    if usage_key is None:
        raise LTIBusinessRuleError("Did not receive a valid usage_key object nor identifier.")

    problem_key_string = 'block-v1:' + usage_key._to_string()

    course_data = CourseData(
        user=user, 
        course=None, 
        collected_block_structure=None, 
        structure=None, 
        course_key=course_key
        )
    
    course_grade = CourseGradeFactory().read(
        user=user, 
        course_key=course_key
        )

    for chapter in course_grade.chapter_grades.itervalues():
        for section in chapter['sections']:
            grades_factory = SubsectionGradeFactory(
                student=user, 
                course=None, 
                course_structure=None, 
                course_data=course_data
                )
            subsection_grades = grades_factory.create(
                subsection=section, 
                read_only=True
                )

            for problem_key_BlockUsageLocator, problem_ProblemScore in subsection_grades.problem_scores.items():
                if str(problem_key_BlockUsageLocator) == problem_key_string:
                    grades = {
                        'section_attempted_graded': section.attempted_graded,
                        'section_earned_all': section.all_total.earned,
                        'section_possible_all': section.all_total.possible,
                        'section_earned_graded': section.graded_total.earned,
                        'section_possible_graded': section.graded_total.possible,
                        'section_grade_percent': _calc_grade_percentage(section.graded_total.earned, section.graded_total.possible),
                        }

                    section_url = u'{scheme}://{host}/{url_prefix}/{course_id}/courseware/{chapter}/{section}'.format(
                            scheme = u"https" if settings.HTTPS == "on" else u"http",
                            host = settings.SITE_NAME,
                            url_prefix='courses',
                            course_id=course_key.html_id(),
                            chapter=chapter['url_name'],
                            section=section.url_name
                            )

                    retval = {
                        'grades':  grades,
                        'url': section_url
                    }
                    return retval

    raise LTIBusinessRuleError("Did not find problem_key_string {problem_key_string} in the grade data for course {course_id}".format(
        course_id = course_key.html_id(),
        problem_key_string = problem_key_string
    ))
    return None


def _calc_grade_percentage(earned, possible):
    """
        calculate the floating point percentage grade score based on the
        integer parameters "earned" and "possible"
    """
    f_grade = float(0)
    if possible != 0:
        f_grade = float(earned) / float(possible)
    return f_grade
