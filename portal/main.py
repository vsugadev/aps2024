
from app import app
from flask import flash, render_template, request, redirect, render_template_string, session
from sqlalchemy import func
from datetime import date
# from io import StringIO , BytesIO      # allows you to store response object in memory instead of on disk

#from base64 import b64decode
from flask_user import login_required, roles_required, current_user, UserManager
from views.tables import Results_Student, Results_Enrollment, Results_Payment

from views.forms import SearchForm, StudentListForm, StudentForm

from models.orm_models import db, Enrollment, Student, UIConfig, User, UserRole
from common import util, db_util
from common import constant as cons
from common.cache import Cache as cache
from common.mail import mail

from enrollment import enrollment_blueprint
from class_management import class_management_blueprint

from attendance import attendance_blueprint
from homework import homework_blueprint
from class_tracking import class_tracking_blueprint
from exam import exam_blueprint
from grade import grade_blueprint
from book_order import book_blueprint
from profile import profile_blueprint
from rollover import rollover_blueprint
from communication import comm_blueprint
from setting import setting_blueprint
from sync_data import sync_data_blueprint
from service_request import service_request_blueprint
from certificates import certificates_blueprint
from prize import prize_blueprint
from thedu import thedu_blueprint

import grade
import payment

app.config.from_pyfile('config/app_config.py')
app.app_context().push()

db.init_app(app)
mail.init_app(app)

#csrf.init_app(app)

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

app.register_blueprint( enrollment_blueprint )
app.register_blueprint( class_management_blueprint )
app.register_blueprint( attendance_blueprint )
app.register_blueprint( homework_blueprint )
app.register_blueprint( grade_blueprint )
app.register_blueprint( class_tracking_blueprint )
app.register_blueprint( exam_blueprint )
app.register_blueprint( payment.payment_blueprint )
app.register_blueprint( book_blueprint )
app.register_blueprint( profile_blueprint )
app.register_blueprint( rollover_blueprint )
app.register_blueprint( comm_blueprint )
app.register_blueprint( setting_blueprint )
app.register_blueprint( sync_data_blueprint )
app.register_blueprint( service_request_blueprint )
app.register_blueprint( certificates_blueprint )
app.register_blueprint( prize_blueprint )
app.register_blueprint( thedu_blueprint )

#Initial setup
@app.before_first_request
def initial_setup():
#    cache.cache.init_app(app)
#    cache.cache_config(app)
    cache.init(app)
#    event_id = db_util.get_active_event()
#    program_id = db_util.get_non_participant_program_id( event_id )

    cache.set_value("EVENT_ID", 1)
    cache.set_value("NOT_PARTICIPATING_PROGRAM_ID", 0)
    payment.payment_init()

@app.route('/')
@app.route('/home_page')
@login_required    # Use of @login_required decorator

def main_menu():
    util.trace()
                # <h2>{%trans%}Setting{%endtrans%}</h2>
                # <h2>{%trans%}Finance{%endtrans%}</h2>
                # <p><a href={{ url_for('search', mode='payment') }}>{%trans%}Payments Tracking{%endtrans%}</a></p>


    start_block = """{% extends "flask_user_layout.html" %}
            {% block content %}"""
    parent_menu = """<h2>{%trans%}Parent{%endtrans%}</h2>
                    <p><a href={{ url_for('class_tracking.class_status') }}>{%trans%}Class Updates{%endtrans%}</a></p>
                    <p><a href={{ url_for('grade.myevaluation') }}>{%trans%}Evaluations{%endtrans%}</a></p>
                    <p><a href={{ url_for('certificates.my_certs') }}>{%trans%}Certificates{%endtrans%}</a></p>
                    <p><a href={{ url_for('enrollment.myenrollment') }}>{%trans%}Enrollments{%endtrans%}</a></p>
                    <p><a href={{ url_for('payment.mypayment') }}>{%trans%}Payments{%endtrans%}</a></p>
                    <p><a href={{ url_for('profile.user_profile_page') }}>{%trans%}Profile{%endtrans%}</a></p>
                    <p><a href="https://sites.google.com/avvaiyarpadasalai.org/apsportal?pli=1" target="_blank" rel="noopener noreferrer">{%trans%}APS Intranet{%endtrans%}</a></p>
                  """

    teacher_menu = """<h2>{%trans%}Teacher{%endtrans%}</h2>
                      <p><a href="https://sites.google.com/avvaiyarpadasalai.org/apsportal?pli=1" target="_blank" rel="noopener noreferrer">{%trans%}APS Intranet{%endtrans%}</a></p>
                      <p><a href={{ url_for('class_management.myclass') }}>{%trans%}My Class{%endtrans%}</a></p>
                      <p><a href={{ url_for('class_tracking.class_tracking_status') }}>{%trans%}Class Progress{%endtrans%}</a></p>
                      <p><a href={{ url_for('attendance.attendance_status') }}>{%trans%}Attendance{%endtrans%}</a></p>
                      <p><a href={{ url_for('homework.homework_status', type=3 )}}>{%trans%}Classwork{%endtrans%}</a></p>
                      <p><a href={{ url_for('homework.homework_status', type=2 )}}>{%trans%}Quiz{%endtrans%}</a></p>
                      <p><a href={{ url_for('homework.homework_status', type=1 )}}>{%trans%}Project{%endtrans%}</a></p>
                      <p><a href={{ url_for('homework.homework_status')}}>{%trans%}Homework{%endtrans%}</a></p>
                      <p><a href={{ url_for('exam.search_exam') }}>{%trans%}Trimester Evaluations{%endtrans%}</a></p>
                      <p><a href={{ url_for('grade.summary_score') }}>{%trans%}Evaluation Summary{%endtrans%}</a></p>
                      <p><a href={{ url_for('profile.name_list') }}>{%trans%}Student Details Update{%endtrans%}</a></p>
                    """

    hr_menu = """<h2>{%trans%}HR{%endtrans%}</h2>
                 <p><a href={{ url_for('thedu.view_page') }}>{%trans%}Find APSians{%endtrans%}</a></p>
                 <p><a href={{ url_for('prize.add_page') }}>{%trans%}Prize{%endtrans%}</a></p>
                 <p><a href={{ url_for('prize.add_page') }}>{%trans%}Volunteer Time Tracking{%endtrans%}</a></p>
              """

    treasurer_menu = """<h2>{%trans%}Treasurer{%endtrans%}</h2>
                        <p><a href={{ url_for('prize.distribution_page', view=0) }}>{%trans%}Prize Distribution{%endtrans%}</a></p>
                        <p><a href={{ url_for('prize.distribution_page', view=1) }}>{%trans%}Volunteer Discount(2022-23){%endtrans%}</a></p>
                        <p><a href={{ url_for('search', mode='payment') }}>{%trans%}Students Payments Tracking{%endtrans%}</a></p>
                    """

    _dash = 'enrollment.enrollment_dashboard'

    super_admin_menu = """<h2>{%trans%}Super Admin{%endtrans%}</h2>
                <p><a href={{ url_for('communication.notify') }}>{%trans%}Communication{%endtrans%}</a></p>
                <p><a href={{ url_for('communication.trigger_notification') }}>{%trans%}Trigger Notification{%endtrans%}</a></p>
                <p><a href={{ url_for('communication.email_list') }}>{%trans%}Email List{%endtrans%}</a></p>
                <p><a href={{ url_for('profile.search_profile' ) }}>{%trans%}Profile Update{%endtrans%}</a></p>
                <p><a href={{ url_for('search', mode='score') }}>{%trans%}Score Report{%endtrans%}</a></p>
                <p><a href={{ url_for('setting.category_list') }}>{%trans%}Config{%endtrans%}</a></p>
                <p><a href={{ url_for('rollover.change_year') }}>{%trans%}Change Year{%endtrans%}</a></p>
                <p><a href={{ url_for('rollover.school_year') }}>{%trans%}School Year{%endtrans%}</a></p>
                """

    admin_menu = """<h2>{%trans%}Admin{%endtrans%}</h2>
                <p><a href={{ url_for('""" + _dash + """') }}>{%trans%}Dashboard{%endtrans%}</a></p>
                <p><a href={{ url_for('search', mode='enroll') }}>{%trans%}Enrollments{%endtrans%}</a></p>
                <p><a href={{ url_for('search', mode='list') }}>{%trans%}Student List{%endtrans%}</a></p>
                <p><a href={{ url_for('class_management.class_allocation') }}>{%trans%}Class Allocation{%endtrans%}</a></p>
                <p><a href={{ url_for('search', mode='bulk') }}>{%trans%}Section Assignment{%endtrans%}</a></p>
                <p><a href={{ url_for('rollover.calendar_view') }}>{%trans%}School Calendar{%endtrans%}</a></p>
                <p><a href={{ url_for('service_request.admin_page', view=0) }}>{%trans%}Help Desk (Admin){%endtrans%}</a></p>
                <p><a href={{ url_for('service_request.feedback_view') }}>{%trans%}Teachers Feedback{%endtrans%}</a></p>
                <h2>{%trans%}Books{%endtrans%}</h2>
                <p><a href={{ url_for('book_order.book_order') }}>{%trans%}Order Tracking{%endtrans%}</a></p>
                <p><a href={{ url_for('search', mode='book') }}>{%trans%}Books Distribution{%endtrans%}</a></p>
                """

    end_block = """{% endblock %}"""

    user_roles = db_util.get_user_roles(current_user.id)

    main_menu =  start_block
    if "super_admin" in user_roles :
        main_menu =  main_menu + super_admin_menu + admin_menu + treasurer_menu + hr_menu + teacher_menu + parent_menu
    elif "admin" in user_roles :
        main_menu =  main_menu + admin_menu + treasurer_menu + hr_menu + teacher_menu + parent_menu
    elif "teacher" in user_roles :
        main_menu =  main_menu + teacher_menu
    elif "hr" in user_roles :
        main_menu = main_menu + hr_menu + teacher_menu
    elif "treasurer" in user_roles :
        main_menu = main_menu + treasurer_menu
    elif "parent" in user_roles :
        main_menu = main_menu + parent_menu

    main_menu = main_menu + end_block

    if not session.get('ACADEMIC_YEAR') :
        return redirect('/user/sign-out')

    if "parent" in user_roles :
        return render_template_string( main_menu )
    else :
        return redirect('/profile')



@app.route('/search', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def search():
    util.trace()
    mode = request.args.get('mode')
    search = SearchForm(request.form, mode = mode)

    if request.method == 'POST':
        return search_results(search)

    if mode == 'payment' :
        title = 'Students Lookup for Payments'
    elif mode == 'list' :
        title = 'Students Lookup'
    elif mode == 'bulk' :
        title = 'Students Lookup for Section Assignment'
    elif mode == 'book' :
        title = 'Students Lookup for Books Distribution'
    elif mode == 'profile' :
        title = 'Profile Lookup'
    elif mode == 'score' :
        title = 'Students Score Report'
    elif mode == 'enroll' :
        title = 'Students Lookup for Enrollment'
    else :
        return redirect('/')
    return render_template('main/search.html', form=search, title = title, mode = mode )

@app.route('/results')
@login_required    # Use of @login_required decorator
@roles_required('admin')

def search_results(search):
    util.trace()
    try:
        rows = []
        name_string = search.data['name'].strip()
        section = search.data['section']
        nilai = search.data['nilai']
        paid = search.data['paid']
        enrollment = search.data['enrollment']
        new = search.data['new']
        inactive = search.data['inactive']
        to_csv = search.data['to_csv']
        mode = search.data['mode']
        print( "Start query.." )
        query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_first_name, Student.student_last_name, Student.student_name_tamil, Student.sex,
                 Student.student_email, Student.start_year, User.father_name, User.mother_name, User.email, User.email2, User.phone1,
                 User.phone2, User.parents_street_address, User.parents_street_address2, User.parents_city, User.parents_state, User.parents_country, User.parents_zipcode, User.teaching_volunteer, User.class_parent ,
                 Enrollment.enrollment_id, Enrollment.last_year_class, Enrollment.school_grade, Enrollment.nilai, Enrollment.order_id,
                 Enrollment.section, Enrollment.payment_status, UIConfig.category_value.label("enrollment_status"),
                 Enrollment.due_amount, Enrollment.discount_amount, Enrollment.previous_balance,  Enrollment.paid_amount, Enrollment.paid_date,
                 Enrollment.book_shipped_date, Enrollment.book_tracking_number, Enrollment.book_delivered_date,
                 Enrollment.check_no, Enrollment.book_status, Student.skill_level_joining, Student.prior_tamil_school ,
                 func.concat(Student.student_id, '|', func.unix_timestamp(date.today())).label("link_id"),
                 func.concat(User.id, '|', func.unix_timestamp(date.today())).label("parent_id"),
                 func.group_concat(UserRole.role_id, ",").label("roles")  ) \
                .join(User, User.id == Student.parent_id )\
                .join(Enrollment, Enrollment.student_id == Student.student_id )\
                .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                .outerjoin(UserRole, UserRole.user_id == User.id ) \
                .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
                .filter((Student.student_name.like("%" + name_string + "%") |
                 User.father_name.like("%" + name_string + "%")| User.mother_name.like("%" + name_string + "%")| User.email.like("%" + name_string + "%") | User.email2.like("%" + name_string + "%") )) \
                .group_by(Student.student_id )

        print( "Initial query.." )
        if nilai:
            query = query.filter( Enrollment.nilai == nilai )
        if section:
            query = query.filter( Enrollment.section == section )
        if paid :
            query = query.filter( Enrollment.payment_status == paid )
        if enrollment :
            query = query.filter( Enrollment.enrollment_status == enrollment )
        elif mode == 'bulk' :
            query = query.filter( Enrollment.enrollment_status.in_( [ cons._ENROLLED_ONLINE, cons._ENROLL_CONFIRMED ] ))
        if not inactive and not enrollment :
            query = query.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED ))
        if new :
            query = query.filter( Student.start_year == session["ACADEMIC_YEAR"] )

        query = query.filter(Enrollment.academic_year == session["ACADEMIC_YEAR"])

        print(query)

#        if mode == 'list':
#            query = query.distinct()

        if mode == 'payment':
            rows = query.order_by(Enrollment.paid_date, Enrollment.check_no ).all()
        else :
            rows = query.order_by(Enrollment.nilai, Enrollment.section, Student.student_name ).all()

        if not rows:
            flash('No results found!', 'success')
            return redirect('/search?mode=%s' %mode)
        if not to_csv or mode == 'score' :
            # display results

            if mode == 'enroll' :
                table = Results_Enrollment(rows )
            elif mode == 'list':
                table = Results_Student(rows )
            elif mode == 'score':
                enroll_list = [ row.enrollment_id for row in rows ]
                return grade.summary_score(2, enroll_list, to_csv )

            elif mode == 'bulk' :
                count = len(rows)
                mainform = StudentListForm()
                for student in rows:
                    studentform = StudentForm()

                    studentform.enrollment_id = student.enrollment_id
                    studentform.student_name = student.student_name
                    studentform.enrollment_status = student.enrollment_status
                    studentform.sex = student.sex
                    studentform.start_year = student.start_year
                    studentform.nilai = student.nilai
                    studentform.payment_status = student.payment_status
                    studentform.last_year_class = student.last_year_class
                    studentform.school_grade = student.school_grade
                    studentform.section = student.section

                    mainform.students.append_entry(studentform)
                return render_template('main/enrollment_update_bulk.html', title='Bulk Enrollment', form=mainform, count=count )
            elif mode == 'book' :
                count = len(rows)
                mainform = StudentListForm()
                for student in rows:
                    studentform = StudentForm()

                    studentform.enrollment_id = student.enrollment_id
                    studentform.student_name = student.student_name
                    studentform.enrollment_status = student.enrollment_status
                    studentform.payment_status = student.payment_status
                    studentform.start_year = student.start_year
                    studentform.nilai = student.nilai
                    studentform.section = student.section
                    studentform.book_shipped_date = student.book_shipped_date
                    studentform.book_tracking_number = student.book_tracking_number
                    studentform.book_delivered_date = student.book_delivered_date
                    studentform.book_status = True if student.book_status == 'Y' else False

                    mainform.students.append_entry(studentform)
                return render_template('main/book_update.html', title='Book Distribution', form=mainform, count=count )

            elif mode == 'payment' :
                paid_amount = 0.0
                for row in rows:
                    paid_amount += float(row.paid_amount)

                table = Results_Payment(rows )
                table.border = True
                return render_template('main/generic.html', table=table, mode=mode, rowcount=len(rows), paid_amount=paid_amount )
            else :
                 return redirect('/')

            table.border = True
            return render_template('main/generic.html', table=table, mode=mode, rowcount=len(rows) )
        else :
            return util.download( rows, '%s_report.csv' %mode , query)

    except Exception as e:
        flash('Error while searching', 'error')
        print(e)
        return redirect('/')


@app.teardown_request
def teardown(exc):
    db.session.close()
#    print( "Teardown {0!r}".format(exc))

if __name__ == "__main__":
    app.run( debug=True )
