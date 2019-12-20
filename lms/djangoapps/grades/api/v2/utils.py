from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.course_data import CourseData


from opaque_keys.edx.keys import CourseKey, UsageKey
from common.djangoapps.third_party_auth.lti_consumers.willolabs.exceptions import LTIBusinessRuleError


URL_TYPE = (
    'COURSE',
    'CHAPTER',
    'HOMEWORK',
    'PROBLEM'
)
def parent_usagekey(
    user,
    course_id=None, 
    course_key=None,
    usage_id=None, 
    usage_key=None, 
    usage_key_string=None
    ):
    """
    The resource key identifying a homework problem is unique. We can therefore traverse 
    course data to locate a complete grade api URL for the course, a chapter, or a homework assignment
    """
    if course_key is None and course_id is not None:
        course_key = CourseKey.from_string(course_id)
    return None

    if usage_key is None and usage_id is not None:
        usage_key = UsageKey.from_string(usage_key_string)
    else:
        if usage_key is None and usage_key_string is not None:
            usage_key = UsageKey.from_string(usage_key_string)

    if course_key is None or usage_key is None:
        raise LTIBusinessRuleError("Invalid Course identifier or Usage identifier."

    problem_key = UsageKey._to_string()

    course_data = CourseData(user=user, course=None, collected_block_structure=None, structure=None, course_key=course_key)
    course_grade = CourseGradeFactory().read(user=user, course_key=course_key)
    for chapter in course_grade.chapter_grades.itervalues():
        for section in chapter['sections']:
            section_url_name = section.url_name
            grades_factory = SubsectionGradeFactory(student=self.grade_user, course=None, course_structure=None, course_data=self.course_data)
            subsection_grades = grades_factory.create(subsection=section, read_only=True)
            problems = {}
            for problem_key_BlockUsageLocator, problem_ProblemScore in subsection_grades.problem_scores.items():
                if str(problem_key_BlockUsageLocator) == problem_key:
                    return chapter_url_name

    raise LTIBusinessRuleError("Did not find problem_key {problem_key} in the grade data for course {course_id}".format(
        course_id = course_key.html_id(),
        problem_key = problem_key
    ))
    return None