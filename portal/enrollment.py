
from flask import Blueprint, flash, redirect, request, render_template, session, current_app
from datetime import datetime, date
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased
import pandas as pd

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.cache import Cache as cache
from common.mail import mail

from models.orm_models import db, Enrollment, Nilai, Section, Student, UIConfig, User
from views.forms import EnrollConfirmationForm, EnrollmentEditForm, SelfEnrollForm, SelfEnrollListForm,  StudentEditForm, UserProfileForm
from views.tables import Results_MyEnrollment

from payment import update_due_amount

enrollment_blueprint = Blueprint('enrollment', __name__ )

@enrollment_blueprint.route('/enrollment_dashboard' )
@login_required
@roles_required('admin')

def enrollment_dashboard():
    util.trace()
    try:
        query = db.session.query(Enrollment.enrollment_status, UIConfig.category_value.label("Status"), Student.start_year, func.count(Enrollment.enrollment_id).label("enroll_count")) \
                    .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                    .join( Student, Enrollment.student_id == Student.student_id ) \
                    .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
                    .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
                    .group_by(Enrollment.enrollment_status, UIConfig.category_value, Student.start_year )

#        results = query.all()
#        for u in results:
#            print( u._asdict() )

        df = pd.read_sql(query.statement,  db.engine.connect())
        df['Type'] =df.apply(lambda row: 'NEW' if row['start_year'] == session["ACADEMIC_YEAR"] else 'EXISTING', axis=1 )
        df_count = df.groupby(['Status','Type'], as_index=False)['enroll_count'].sum()

#        df_summary = df_count.set_index(['new', 'enroll_status']).unstack()['enroll_count']
#        df_summary.fillna(0, inplace=True)

        df_summary = pd.pivot_table(df_count, index = 'Type', values = 'enroll_count', columns = 'Status', aggfunc = 'sum', fill_value = 0, margins = True, margins_name='Total...')
        return render_template('main/dashboard_summary.html', tables=[df_summary.to_html(classes='data')], titles=df_summary.columns.values, rowcount=len (df_summary), title = "Enrollment Dashboard" )

    except Exception as e:
        flash('Error while fetching enrollment dashborad', 'error')
        print(e)
        return redirect('/')


@enrollment_blueprint.route('/enrollment/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def enrollment_view(role='parent'):
    util.trace()

    # Initialize form
    form = UserProfileForm(request.form, obj=current_user)

    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to user_profile fields
        form.populate_obj(current_user)
        try:
            # role = 'parent'
            db_util.find_or_create_user_roles( current_user.id, role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Profile(%s) Failed..' %role,  'error')
            print(e)
            return redirect('/')
        flash('Profile(%s) Updated..' %role, 'success')
        # Redirect to home page
        return redirect('/')

    # Process GET or invalid POST
    return render_template('main/user_profile.html', form=form)

@enrollment_blueprint.route('/enrollment_edit/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def enrollment_edit(id):
    util.trace()
    # Initialize form
    enrollment = Enrollment.query.get(id)
    student = Student.query.get(enrollment.student_id)

    form = EnrollmentEditForm(request.form, obj=enrollment,
                                student_name = student.student_name,
                                start_year = student.start_year,
                                skill_level_joining = student.skill_level_joining,
                                prior_tamil_school = student.prior_tamil_school
                                )

    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to user_profile fields
        form.populate_obj(enrollment)
        try:
            section_list = [s.section for s in Section.query.filter_by(academic_year = session["ACADEMIC_YEAR"] ).all()]
            section = enrollment.section

            if section :
                section = section.strip().upper()
                if len(section) == 1 :
                    nilai = enrollment.nilai
                    if nilai < 1 :
                        nilai_value = dict(form.nilai.choices).get(form.nilai.data)

                        section = "%s%s" %(nilai_value[0:1] , section)
                    elif nilai > 0 and nilai < 99:
                        section = "%s%s" %(nilai, section)

                if section in section_list :
                    enrollment.section = section
                else :
                    flash('Incorrect or Undefined section %s , Enter correct section' %section, 'error')
                    return render_template('main/enrollment.html', form=form)
#                    return redirect('/search?mode=enroll')
            else :
                section = None
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Enrollment info update Failed..', 'error')
            print(e)
            return redirect('/search?mode=enroll')
        flash('Enrollment info sucessfully Updated..', 'success')
        # Redirect to home page
        return redirect('/search?mode=enroll')

    # Process GET or invalid POST
    return render_template('main/enrollment.html', form=form)


@enrollment_blueprint.route('/enrollment_update_bulk', methods=['POST'])
@login_required    # Use of @login_required decorator
@roles_required('admin')

def enrollment_update_bulk():
    util.trace()
    try :
        on_commit = False
        data = request.form.to_dict()
        count = util.count( data.keys() )
#        print("Enrollment count is %s" %count  )
        enroll_list =  []
        section_missing = []
        section_list = [s.section for s in Section.query.filter_by(academic_year = session["ACADEMIC_YEAR"] ).all()]

        #TODO: Do not update enrollment info if sectiom is not changed. Need to compare amount from DB

        for row in range(count) :
            enrollment_id = data.get("students-%s-enrollment_id" %row)
            section = data.get("students-%s-section" %row)
            if section :
                section = section.strip().upper()
                if section not in section_list :
                    section_missing.append(section)
                    continue

            enroll_data = {'enrollment_id': enrollment_id ,
                            'section' : section,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }

            enroll_list.append( enroll_data )
        on_commit = True
        db.session.bulk_update_mappings(Enrollment, enroll_list )
        db.session.commit()
        on_commit = False
#        print( enroll_list )
        if len(enroll_list) > 0 :
            flash('Section successfully updated for %s students' %len(enroll_list) , 'success')
        if len(section_missing) > 0 :
            flash('Not able to update section for %s students due to incorrct or undefined sections %s' %(len(section_missing), ', '.join( s for s in list(set(section_missing )))) , 'error')

        return redirect('/search?mode=bulk')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating enrollment info', 'error')
        print(e)
        return redirect('/search?mode=bulk')


@enrollment_blueprint.route('/student_edit', defaults={'id_str': '0', 'mode':None} ,  methods=['GET', 'POST'] )  ##
@enrollment_blueprint.route('/student_edit/<string:id_str>/<string:mode>' ,  methods=['GET', 'POST'] )

@login_required
@roles_required(['parent', 'admin'])
def student_edit(id_str='0', mode=None):
    util.trace()
    # Initialize form
    if id_str == '0':
        id = 0
        student_obj = Student()
        enroll_obj = Enrollment()
    else :
        id_list = id_str.split('|')
        id = int(id_list[0])
        if mode != 'edit' :
            students = [ row.student_id for row in Student.query.filter( Student.parent_id == current_user.id ).all() ]
            if (id not in students )  :
                flash('Warning : URL is altered manually!!', 'error')
                print('*** URL alter attempt by %s ***' %current_user.id )
                return redirect('/myenrollment')

        student_obj = db.session.query(Student).filter(Student.student_id == id).first()
        enroll_obj  = db.session.query(Enrollment).filter(Enrollment.student_id == id).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"]).first()
        if enroll_obj :
            student_obj.school_grade = enroll_obj.school_grade
#    print("Section Count is %s - %s " %( len( section_obj) , section_obj[0].room ) )
    form = StudentEditForm(request.form, academic_year = session["ACADEMIC_YEAR"], obj=student_obj  )
    form.school_grade.label = "School Grade in %d *" %session["ACADEMIC_YEAR"]
    if student_obj.skill_level_joining :
        form.skill_level_joining.data = util.str_to_list( student_obj.skill_level_joining )
#    print(util.str_to_list( student_obj.skill_level_joining ))
    # Process valid POST
    if request.method == 'POST' :
        if form.validate():
            # Copy form fields to class fields
#            print("POST: Student Id : %d, mode : %s" %(id, mode) )
            if mode == 'edit' :
                url_redirect = '/search?mode=enroll'
            else :
                url_redirect = '/myenrollment'

            form.populate_obj(student_obj)
            try:
                if id == 0:
                    student_obj.parent_id = current_user.id
                    student_obj.start_year = session["ACADEMIC_YEAR"]
                    student_obj.last_updated_id = current_user.id
                    student_obj.skill_level_joining = util.list_to_str( student_obj.skill_level_joining )
                    db.session.add(student_obj)
                    db.session.flush()
                    student_new = db.session.query(Student).filter(Student.student_name == student_obj.student_name).order_by(Student.student_id.desc()).first()
                    enroll_obj.student_id = student_new.student_id
                    enroll_obj.book_shipment_preference = student_obj.book_shipment_preference
                    enroll_obj.school_grade = student_obj.school_grade
                    print("______________________________________" )
                    print("student_obj.school_grade : %s" %student_obj.school_grade  )
                    enroll_obj.nilai = 11 if student_obj.school_grade == 13 else 99
                    enroll_obj.academic_year = session["ACADEMIC_YEAR"]
                    enroll_obj.enrollment_status = cons._NOT_ENROLLED
                    enroll_obj.last_updated_id = current_user.id
                    db.session.add(enroll_obj)
                else :
                    student_obj.skill_level_joining = util.list_to_str( request.form.getlist('skill_level_joining'))
                    enroll_obj.book_shipment_preference = student_obj.book_shipment_preference
                    enroll_obj.school_grade = student_obj.school_grade
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                if id == 0 :
                    flash('New Student enrollement Failed..', 'error')
                else :
                    flash('Student update Failed..', 'error')
                print(e)
                return redirect(url_redirect)
            if id == 0 :
                flash('Sucessfully enrolled a new Student..', 'success')
            else :
                flash('Sucessfully updated student info..', 'success')
            return redirect(url_redirect)
        else :
            flash('Issue with updating Student info', 'error')

    # Process GET or invalid POST
    return render_template( 'main/student_edit.html', form=form, mode=mode )

@enrollment_blueprint.route('/myenrollment/<mode>')
@enrollment_blueprint.route('/myenrollment' )
@login_required

def myenrollment(mode = 0 ):
    util.trace()
    try:
        U1 = aliased(User)
        U2 = aliased(User)
        query_main = db.session.query(Student.student_id, Student.student_name, Student.student_name_tamil, Student.age, Student.sex, Student.start_year,
                     User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id, Enrollment.academic_year, Enrollment.last_year_class,
                     Enrollment.school_grade, Enrollment.nilai, Enrollment.section, UIConfig.category_value.label("enrollment_status"), Enrollment.payment_status,
                     func.concat(Student.student_id, '|', func.unix_timestamp(date.today())).label("link_id"),
                     Enrollment.book_shipment_preference, Enrollment.book_shipped_date, Enrollment.book_tracking_number, Enrollment.book_delivered_date,
                     Enrollment.book_status, Nilai.name.label("nilai_name"), Section.room, Section.teacher1_id,
                     U1.father_name.label("teacher1"), U2.father_name.label("teacher2") ,
                     func.concat(Student.start_year, func.lpad(Student.student_id, 4, '0')).label("student_no"),
                     func.concat(Enrollment.academic_year, func.lpad(Enrollment.enrollment_id, 4, '0')).label("enrollment_no") ) \
            .join(User, User.id == Student.parent_id )\
            .join(Enrollment, Enrollment.student_id == Student.student_id )\
            .join(Nilai, Nilai.nilai_id == Enrollment.nilai) \
            .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status ) \
            .outerjoin(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
            .outerjoin(U1, U1.id == Section.teacher1_id  ) \
            .outerjoin(U2, U2.id == Section.teacher2_id  ) \
            .filter( User.id == current_user.id ) \
            .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
            .order_by(Enrollment.academic_year, Enrollment.nilai, Enrollment.section, Student.student_name )

        if mode == 0 :
            rows_confirmed =  query_main.filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ).filter(Enrollment.enrollment_status != cons._NOT_ENROLLED ).all()
            rows_unconfirmed =  query_main.filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ).filter(Enrollment.enrollment_status == cons._NOT_ENROLLED ).all()
            rows_previous =  query_main.filter( Enrollment.academic_year < session["ACADEMIC_YEAR"] ).all()

            if rows_confirmed :
                table_confirmed = Results_MyEnrollment(rows_confirmed )
                table_confirmed.border = True
            else :
                table_confirmed = None

            main_form = SelfEnrollListForm()
            for row in rows_unconfirmed :
                detail_form = SelfEnrollForm()
                detail_form.enrollment_id = row.enrollment_id
                detail_form.student_name = row.student_name
                detail_form.student_name_tamil = row.student_name_tamil
                detail_form.age = row.age
                detail_form.sex = row.sex
                detail_form.school_grade = row.school_grade
                detail_form.start_year = row.start_year
                detail_form.enrollment_status =  cons._ENROLLED_ONLINE
                main_form.students.append_entry(detail_form)

            return render_template('main/myenrollment.html', table_confirmed=table_confirmed, form = main_form, count_confirmed=len(rows_confirmed),\
                    count_unconfirmed=len(rows_unconfirmed), count_previous=len(rows_previous), new_enroll = cache.get_value("NEW_ENROLL") , mode ='current' )

        else :
            rows_previous =  query_main.filter( Enrollment.academic_year < session["ACADEMIC_YEAR"] ).all()
            if rows_previous :
                table_previous = Results_MyEnrollment(rows_previous )
                table_previous.border = True
            else :
                table_previous = None

            return render_template('main/myenrollment.html', table_previous = table_previous, count_previous=len(rows_previous), mode ='previous' )


    except Exception as e:
        flash('Error while fetching Enrollments', 'error')
        print(e)
        return redirect('/')


@enrollment_blueprint.route('/enrollment_confirm', methods=['GET', 'POST'])
@login_required
@roles_required('parent')
def enrollment_confirm():
    util.trace()
    enroll_lookup = {"1" : "ENROLLED for %s" %session["ACADEMIC_YEAR"], "3" : "DISCONTINUED" }
    data = request.form.to_dict()
    count = util.count( data.keys() )
    student_names = None
    enroll_list = None
    enroll_statuses = None
    start_years = None
    table = """<table  border= "1px solid black;"><tr><th>Student Name</th><th>Enrollment Status</th><th>Enrollment Type</th></tr>"""
    for row in range(count) :
        enrollment_id = data.get("students-%s-enrollment_id" %row)
        student_name = data.get("students-%s-student_name" %row)
        enrollment_status = data.get("students-%s-enrollment_status" %row)
        start_year = data.get("students-%s-start_year" %row)

        student_names = student_names + ',' + student_name if student_names else student_name
        enroll_list = enroll_list + ',' + enrollment_id if enroll_list else enrollment_id
        enroll_statuses = enroll_statuses + ',' +  enroll_lookup.get(enrollment_status) if enroll_statuses else  enroll_lookup.get(enrollment_status)
        start_years = start_years + ',' + start_year if start_years else start_year

        table = table + "<tr><td>%s &nbsp;&nbsp;&nbsp;&nbsp;</td><td>%s &nbsp;&nbsp;&nbsp;&nbsp;</td><td>%s </td></tr>" \
                    %(student_name, enroll_lookup.get(enrollment_status), "NEW" if int(start_year) == session["ACADEMIC_YEAR"] else "EXISTING"  )
#        print( "Start Year : %s - %s " %(start_year, start_years ) )
    table = table + "</table>"

    with current_app.open_resource('static/terms_of_service.txt', mode ='r') as f:
        tos = f.read()
    tos = str(tos)  #.replace('\n', '<br>')
    tos = tos.replace("\\r\\n|\\r|\\n", "</br>")

    with current_app.open_resource('static/waiver.txt', mode ='r') as f:
        waiver = f.read()
    waiver = str(waiver)  #.replace('\n', '<br>')
    waiver = waiver.replace("\\r\\n|\\r|\\n", "</br>")


    form = EnrollConfirmationForm( request.form, enroll_ids = enroll_list,  student_names = student_names , \
            enroll_statuses = enroll_statuses, start_years = start_years, consent_signed_by =  "" , agreement = tos, \
            waiver = waiver, consent_dated =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")   )

    return render_template('main/enroll_confirmation.html', form=form, table = table)

@enrollment_blueprint.route('/enrollment_confirm_update', methods=['GET', 'POST'])
@login_required
@roles_required('parent')
def enrollment_confirm_update():
    util.trace()
    on_commit = False
    try:
        enroll_lookup = {"ENROLLED for %s" %session["ACADEMIC_YEAR"] : "1" , "DISCONTINUED" : "3"  }

        enroll_list =  []
        mail_data_all = []
        enroll_ids = request.form.get("enroll_ids")
        enroll_statuses = request.form.get("enroll_statuses").split(",")
        student_names = request.form.get("student_names").split(",")
        start_years   = request.form.get("start_years").split(",")
        is_new = True

        for index, enroll_id in enumerate(enroll_ids.split(",")) :
            enroll_data = { 'enrollment_id' : enroll_id,
                            'enrollment_status' : enroll_lookup.get( enroll_statuses[index] ),
                            'consent_signed_by' : request.form.get("consent_signed_by"),
                            'consent_dated' : datetime.now(),
                            'is_consent_signed' : 1,
                            'is_waiver_signed' : 1,
                            'last_updated_at' : datetime.now() ,
                            'last_updated_id' : current_user.id
                        }

            mail_data = {   'enrollment_id' : enroll_id,
                            'student_name' : student_names[index],
                            'enrollment_status' : enroll_statuses[index],
                            'enrollment_type' : "NEW" if int(start_years[index]) == session["ACADEMIC_YEAR"] else "EXISTING"
                        }

            enroll_list.append(enroll_data)
            mail_data_all.append(mail_data)
            if int(start_years[index]) != session["ACADEMIC_YEAR"] :
                is_new = False
#        print("Enrollment Confirmation Info ")
#        print( enroll_list )
#        print( mail_data_all )
        on_commit = True
        db.session.bulk_update_mappings(Enrollment, enroll_list )
        db.session.commit()
        on_commit = False
        flash('Enrollment info successfully updated for %d students' %(len(enroll_list)) , 'success')
        emails, parent1 , parent2 = db_util.get_email_for_enroll( mail_data_all[0].get("enrollment_id" ) )
        email.send_enroll_confirmation(mail, mail_data_all, emails, parent1, parent2, is_new)
        update_due_amount( current_user.id )
        return redirect('/mypayment')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Enrollment update Failed..', 'error')
        print(e)
        return redirect('/myenrollment')
    return redirect('/myenrollment')

