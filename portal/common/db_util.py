
from flask import session
from pandas.core.common import flatten
from sqlalchemy import func
from sqlalchemy.sql.expression import literal
from datetime import date

from flask_user import current_user

from models.orm_models import db, BookOrder, ClassTracking, Enrollment, Role, \
                                SchoolCalendar, SchoolYear, Section, Student, UIConfig, User, UserRole, ServiceRequests, ServiceRequestAnnualDay
from common import util, constant as cons
from common.cache import Cache as cache


def get_user_roles(user_id) :
    util.trace()
    return [row.name for row in Role.query.join(UserRole, UserRole.role_id== Role.id).filter(UserRole.user_id==user_id).all() ]

def is_user_role(user_id, role_name) :
    util.trace()
    user_role = UserRole.query.join(Role, UserRole.role_id== Role.id).filter(UserRole.user_id==user_id, Role.name == role_name).first()
    return True if user_role else False

def enrollment_count(user_id, enroll_status = None) :
    util.trace()
    query = db.session.query(func.count(Enrollment.enrollment_id)) \
            .join( Student, Enrollment.student_id == Student.student_id ) \
            .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ).filter( Student.parent_id == user_id)

    if enroll_status or enroll_status == 0 :
        query = query.filter( Enrollment.enrollment_status == enroll_status )
    return query.scalar()

def get_enroll_info(enroll_id ) :
    util.trace()
    enroll = db.session.query(Student.student_name, Student.start_year,  Enrollment.due_amount, Enrollment.paid_amount, Enrollment.discount_amount, Enrollment.previous_balance ) \
            .join(Enrollment, Student.student_id == Enrollment.student_id) \
            .filter(Enrollment.enrollment_id == enroll_id).first()
    return enroll.student_name, enroll.start_year, float(enroll.due_amount or 0), float(enroll.paid_amount or 0), float(enroll.discount_amount or 0), float(enroll.previous_balance or 0)

def get_payment_info( parent_id ) :
    util.trace()
    try:
        query = db.session.query(Student.student_name, Student.start_year, Enrollment.enrollment_id, Enrollment.academic_year, Enrollment.nilai, Enrollment.section,
                UIConfig.category_value.label("enrollment_status"), Enrollment.payment_status, Enrollment.due_amount, Enrollment.paid_amount, Enrollment.previous_balance,
                (func.ifnull(Enrollment.due_amount, literal(0)) - Enrollment.paid_amount).label("balance"), Enrollment.paid_date, Enrollment.check_no ) \
                    .join(Enrollment, Enrollment.student_id == Student.student_id).filter(Student.parent_id == parent_id ) \
                     .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                     .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
                .filter( Enrollment.enrollment_status != 3 )  #.filter(Enrollment.academic_year == session["ACADEMIC_YEAR"]  )
        return query.order_by(Enrollment.academic_year, Enrollment.nilai, Enrollment.section, Student.student_name ).all()

    except Exception as e:
        raise e

def get_query_confirmed(nilai_id) :
    util.trace()
    return db.session.query(func.count(Enrollment.enrollment_id)) \
                .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
                .filter( Enrollment.enrollment_status.in_( [cons._ENROLLED_ONLINE, cons._ENROLL_CONFIRMED ] )) \
                .filter( Enrollment.nilai == nilai_id )

def get_query_ordered(col_name, for_order = True) :
    util.trace()
    query = db.session.query(func.ifnull(func.sum(BookOrder.__table__.c[col_name] ),  literal(0)) ) \
        .filter( BookOrder.academic_year == session["ACADEMIC_YEAR"] )

    if for_order :
        return query.filter( BookOrder.type.notin_(["TEACHERS_COPY" , "BUFFER" ]))
    else :
        return query.filter( BookOrder.type.in_(["TEACHERS_COPY" , "BUFFER" ]))

def get_required_count( nilai_id ) :
    util.trace()

    nilai_name = "nilai_A" if nilai_id == -1 else "nilai_%d" %nilai_id
    return get_query_confirmed( nilai_id ).scalar() + get_query_ordered(nilai_name, False).scalar() - get_query_ordered( nilai_name ).scalar()

def get_parents_city( user_id ) :
    util.trace()
    return db.session.query(User.parents_city).filter(User.id == user_id ).scalar()

def get_email_for_class_parents( section ) :
    util.trace()
    users = User.query.join(Student, Enrollment).filter(Enrollment.section == section).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"]).all()
    email_list = [[user.email, user.email2] for user in users ]
    return list(set(util.clean_list( list(flatten(email_list)) )))

def get_email_for_class( section ) :
    util.trace()
    section_row = Section.query.filter(Section.section == section ).filter(Section.academic_year == session["ACADEMIC_YEAR"]).first()
    return section_row.class_email or get_config( "SCHOOL_EMAIL" )

def get_email_for_teachers( section ) :
    util.trace()
    section_row = Section.query.filter(Section.section == section ).filter(Section.academic_year == session["ACADEMIC_YEAR"]).first()
    teachers_list = util.clean_list( [section_row.teacher1_id, section_row.teacher2_id, section_row.teacher3_id] )
    return [ u.email for u in User.query.filter(User.id.in_(teachers_list)).all() ]

def get_email_for_class_students( section ) :
    util.trace()
    students = Student.query.join(Enrollment).filter(Enrollment.section == section).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"]).all()
    email_list = [student.student_email for student in students ]
    return util.clean_list( email_list)

def get_map_teachers( section ) :
    util.trace()
    section_row = Section.query.filter(Section.section == section ).filter(Section.academic_year == session["ACADEMIC_YEAR"]).first()
    teachers_list = util.clean_list( [section_row.teacher1_id, section_row.teacher2_id, section_row.teacher3_id] )
    return { u.id : u.father_name for u in User.query.filter(User.id.in_(teachers_list)).all() }

def get_email_for_enroll( enroll_id ) :
    util.trace()
    users = User.query.join(Student, Enrollment).filter(Enrollment.enrollment_id == enroll_id).first()
    return [users.email, users.email2 ] if users.email2 else [users.email ], users.father_name, users.mother_name

def get_enrolled_sections(current_user_id) :
    util.trace()
    enroll = Enrollment.query.join(Student, User ).filter(User.id == current_user_id) \
             .filter(Enrollment.academic_year == session["ACADEMIC_YEAR"]).filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).all()
    return util.clean_list([e.section for e in enroll ] )

def get_teacher_sections( current_user_id ) :
    util.trace()
    query = Section.query.filter(Section.academic_year == session["ACADEMIC_YEAR"] ).filter( Section.teacher_view == 1 ) \
            .filter(Section.teacher1_id == current_user_id)
            #.filter((Section.teacher1_id == current_user_id) | (Section.teacher2_id == current_user_id) | (Section.teacher3_id == current_user_id ))
    return [s.section for s in query.order_by(Section.section).all() ]

def get_last_school_date() :
    util.trace()
    return db.session.query(func.max(SchoolCalendar.school_date)).filter(SchoolCalendar.is_session == 1) \
            .filter(SchoolCalendar.academic_year == session["ACADEMIC_YEAR"]).filter(SchoolCalendar.school_date <= date.today()).scalar()

def get_next_lesson( section ) :
    util.trace()
    current_lesson =  db.session.query(func.max(ClassTracking.lesson_no)).filter(ClassTracking.academic_year == session["ACADEMIC_YEAR"]).filter(ClassTracking.section == section).scalar()
    return current_lesson + 1 if current_lesson else 1

def get_last_session_volunteer( section ) :
    util.trace()
    last_class_row = ClassTracking.query.filter(func.coalesce(ClassTracking.volunteers_present, '') != '' ) \
                    .filter(ClassTracking.academic_year == session["ACADEMIC_YEAR"]).filter(ClassTracking.section == section) \
                    .order_by(ClassTracking.school_date.desc()).first()
    return last_class_row.volunteers_present if last_class_row else ""

def get_class_day_time( section ) :
    util.trace()
    section_row = Section.query.filter(Section.academic_year == session["ACADEMIC_YEAR"]).filter( Section.section == section ).first()
    return section_row.class_day, section_row.class_start_time

def get_school_day_time() :
    util.trace()
    school_year_row = SchoolYear.query.filter(SchoolYear.academic_year == session["ACADEMIC_YEAR"]).first()
    return school_year_row.school_day, school_year_row.school_start_time

def get_ui_config( _category ) :
    util.trace()
    return { int(c.category_key) : c.category_value for c in UIConfig.query.filter_by( category = _category ).all() }

def get_config(category_key, category = "CONFIG"):
    util.trace()
    return db.session.query(UIConfig.category_value) \
            .filter(UIConfig.category == category) \
            .filter(UIConfig.category_key == category_key).scalar()

def find_or_create_user_roles( user_id, role_name):
    util.trace()
    """
    Find or create a UserRoles record
    """
    user_role = UserRole.query.join(Role, UserRole.role_id== Role.id).filter(UserRole.user_id==user_id,  Role.name == role_name).first()
    if not user_role:
        result =  Role.query.filter( Role.name == role_name ).first()
        role_id = result.id
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.session.add(user_role)
    return user_role

def get_service_requests( current_user_id ):
    util.trace()
    service_request = ServiceRequests.query().all();

    if not service_request:
        service_request = ServiceRequests(open=0, closed=0)
    return service_request

def get_service_request_id( current_user_id ):
    util.trace()
    service_request_id = db.session.query(ServiceRequests.service_id).filter(User.id == current_user_id ).order_by(ServiceRequests.service_id.desc()).first();
    return service_request_id

def get_annualday_registration_id( current_user_id ):
    util.trace()
    annualday_registration_id = db.session.query(ServiceRequestAnnualDay.registration_id).filter(User.id == current_user_id ).order_by(ServiceRequestAnnualDay.registration_id.desc()).first();
    return annualday_registration_id
