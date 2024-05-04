from flask import Blueprint, flash, redirect, request, render_template, session
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import literal
from datetime import date

from flask_user import current_user, login_required, roles_required
from common import db_util, util, constant as cons
from models.orm_models import db, Nilai, Enrollment, Section, Student, UIConfig, User
from views.forms import ClassEditForm
from views.tables import Results_Class, Results_Dashboard, Results_Enrollment, Results_MyClass

class_management_blueprint = Blueprint('class_management', __name__ )

@class_management_blueprint.route('/dashboard', methods=['GET'])
@login_required    # Use of @login_required decorator
@roles_required('admin')
def dashboard():
    util.trace()
    try:
        query = db.session.query( Nilai.nilai_id, Nilai.name.label('nilai'),
                        func.IF(Enrollment.section == '', literal('Unassigned-New'), func.ifnull(Enrollment.section, literal('Unassigned'))).label("section"),
                        func.count(Enrollment.enrollment_id).label("count")) \
                    .join(Enrollment, Nilai.nilai_id == Enrollment.nilai ) \
                    .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
                    .filter( Enrollment.enrollment_status.notin_((0,3,4)) ) \
                    .group_by( Nilai.nilai_id, Nilai.name, Enrollment.section )
        rows = query.all()
        if not rows:
            flash('No results found!', 'success')
            return redirect('/')
        table = Results_Dashboard(rows )
        table.border = True
        #flash('%s students enrolled' %len(rows))
        total = sum([row.count for row in rows ])
        return render_template('main/dashboard.html', table=table, total=total, title = "Class Dashboard" )
    except Exception as e:
        flash('Error while processing class dashboard', 'error')
        print(e)
        return redirect('/')


@class_management_blueprint.route('/class/<string:section>' )
@login_required
@roles_required('admin')

def class_list(section):
    util.trace()
    try:
        query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year,
                       User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id, Enrollment.last_year_class,
                       Enrollment.school_grade,  Enrollment.nilai,Enrollment.section,  Enrollment.enrollment_status, Enrollment.payment_status, Enrollment.paid_amount,
                       Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Student.skill_level_joining, Student.prior_tamil_school,
                       func.concat(Student.student_id, '|', func.unix_timestamp(date.today())).label("link_id"),
                       func.concat(User.id, '|', func.unix_timestamp(date.today())).label("parent_id") ).join(User, Enrollment) \
                .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] )

        if section == 'Unassigned' :
            query = query.filter( Enrollment.section  == None )
        else :
            query = query.filter( Enrollment.section == section)

        rows = query.order_by(Enrollment.nilai, Enrollment.section, Student.student_name ).all()
        if not rows:
            flash('No results found!', 'success')
            return redirect('/dashboard')
        table = Results_Enrollment(rows )
        table.border = True
        return render_template('main/generic.html', table=table, mode='dashboard', rowcount=len(rows) )
    except Exception as e:
        flash('Error while searching for dashboard', 'error')
        print(e)
        return redirect('/dashboard')

@class_management_blueprint.route('/nilai/<int:id>' )
@login_required
@roles_required('admin')

def nilai_list(id):
    util.trace()
    try:
        query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year,
                         User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id, Enrollment.last_year_class,
                         Enrollment.school_grade,  Enrollment.nilai,Enrollment.section,  Enrollment.enrollment_status, Enrollment.payment_status, Enrollment.paid_amount,
                         Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Student.skill_level_joining, Student.prior_tamil_school,
                         func.concat(Student.student_id, '|', func.unix_timestamp(date.today())).label("link_id"),
                         func.concat(User.id, '|', func.unix_timestamp(date.today())).label("parent_id") ).join(User, Enrollment) \
                .filter( Enrollment.nilai  == id ) \
                .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"]  )

        rows = query.order_by(Enrollment.nilai, Enrollment.section, Student.student_name ).all()
        if not rows:
            flash('No results found!', 'success')
            return redirect('/dashboard')
        table = Results_Enrollment(rows )
        table.border = True
        return render_template('main/generic.html', table=table, mode='dashboard', rowcount=len(rows)  )
    except Exception as e:
        flash('Error while searching for dashboard', 'error')
        print(e)
        return redirect('/dashboard')

@class_management_blueprint.route('/class_allocation' )
@login_required
@roles_required('admin')

def class_allocation():
    util.trace()
    try:
        U1 = aliased(User)
        U2 = aliased(User)
        U3 = aliased(User)

        query = db.session.query(Section.section, Section.academic_year, Section.teacher_view, Section.parent_view, Nilai.name, Section.room,
                Section.class_email, Section.class_day, Section.class_start_time, Section.teacher1_id,
                U1.father_name.label("teacher1"), U2.father_name.label("teacher2"), U3.father_name.label("teacher3")) \
        .join(Nilai ) \
        .outerjoin(U1, U1.id == Section.teacher1_id ) \
        .outerjoin(U2, U2.id == Section.teacher2_id ) \
        .outerjoin(U3, U3.id == Section.teacher3_id ) \
        .filter(Section.academic_year == session["ACADEMIC_YEAR"])
        rows = query.all()

#        if not rows:
#            flash('No results found!', 'success')
#            return redirect('/')

        table = Results_Class(rows )
        table.border = True
        return render_template('main/generic.html', table=table, mode='class_list', rowcount=len(rows) )
    except Exception as e:
        flash('Error while searching for classes', 'error')
        print(e)
        return redirect('/')

@class_management_blueprint.route('/class_edit', defaults={'section': None} ,  methods=['GET', 'POST'] )  ##
@class_management_blueprint.route('/class_edit/<string:section>' ,  methods=['GET', 'POST'] )

@login_required
@roles_required('admin')
def class_edit(section=None):
    util.trace()
    # Initialize form
    if section == '0':
        section_obj = Section()
        section_obj.academic_year = session["ACADEMIC_YEAR"]
        section_obj.class_day, section_obj.class_start_time = db_util.get_school_day_time()
    else :
        section_obj = db.session.query(Section).filter(Section.section == section).filter(Section.academic_year == session["ACADEMIC_YEAR"]).first()

#    print("Section Count is %s - %s " %( len( section_obj) , section_obj[0].room ) )
    form = ClassEditForm(request.form, obj=section_obj )
    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to class fields
        form.populate_obj(section_obj)
        section_obj.academic_year = session["ACADEMIC_YEAR"]
        section_obj.section = section_obj.section.upper().strip()
        if section_obj.teacher1_id == -1 :
            section_obj.teacher1_id = None
        if section_obj.teacher2_id == -1 :
            section_obj.teacher2_id = None
        if section_obj.teacher3_id == -1 :
            section_obj.teacher3_id = None
        try:
            if section == '0':
                if not section_obj.class_email :
                    if db_util.get_config( 'CLASS_EMAIL_AUTO_ADD' ) == '1' :
                        domain = db_util.get_config( 'EMAIL_DOMAIN' ).strip()
                        section_obj.class_email = "nilai.%s@%s" %(section_obj.section.lower().strip(), domain )

                db.session.add(section_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Class Assignment Failed..', 'error')
            print(e)
            return redirect('/class_allocation')
        flash('Class Allocation successfully Updated..', 'success')
        return redirect('/class_allocation')

    # Process GET or invalid POST
    return render_template('main/class_allocation.html', form=form )




#@app.route('/myclass', defaults={'mode': 'view'})
@class_management_blueprint.route('/myclass')
@class_management_blueprint.route('/myclass/<string:mode>/<int:section>')
@login_required
@roles_required('teacher')

def myclass(mode = 'view', section=None):
    util.trace()
    try:
        sections = db_util.get_teacher_sections( current_user.id )
        if not sections  :
            flash('No Class assigned yet!', 'success')
            return redirect('/')

        if section and len(sections) > section :
            current_section = [ sections[section] ]
        else :
            current_section =  [ sections[0] ]

        U1 = aliased(User)
        U2 = aliased(User)

        query = db.session.query(Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year, Student.student_email,
                         User.email, User.email2, User.phone1, User.phone2, Enrollment.last_year_class,
                         Enrollment.school_grade, Enrollment.nilai, Enrollment.section,  UIConfig.category_value.label("enrollment_status"), Enrollment.payment_status,
                         Enrollment.book_status, Nilai.name.label("nilai_name"), Section.room, Section.teacher1_id, U1.father_name.label("teacher1"), U2.father_name.label("teacher2") ) \
        .join(User, Student.parent_id == User.id ) \
        .join(Enrollment, Student.student_id == Enrollment.student_id ) \
        .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
        .join(Nilai, Nilai.nilai_id == Enrollment.nilai) \
        .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
        .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
        .outerjoin(U1, U1.id == Section.teacher1_id  ) \
        .outerjoin(U2, U2.id == Section.teacher2_id  ) \
        .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
        .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"]  ) \
        .filter((Section.teacher1_id == current_user.id) | (Section.teacher2_id == current_user.id) | (Section.teacher3_id == current_user.id) ) \
        .filter( Section.section.in_( current_section ))

        rows = query.order_by(Enrollment.nilai, Enrollment.section, Student.student_name ).all()

        if not rows:
            flash('Class to be assigned!', 'success')
            return redirect('/')

        title = "My Class List"
        if mode == "view" :
            if len(sections) > 1 :
                section_dict = {k: v for k, v in enumerate(sections)}
                title = title + " - %s" %current_section[0]
            else :
                section_dict = {}

            table = Results_MyClass(rows )
            table.border = True
            return render_template('main/myclass.html', table=table, rowcount=len(rows), title=title, section_dict=section_dict, section=section if section else 0 )
        elif mode == "csv" :
            return util.download( rows, '%s_class_list_%s.csv' %(current_section[0], date.today().strftime('%Y%m%d')), query )

    except Exception as e:
        flash('Error while fetching Class List', 'error')
        # flash(str(e), 'error')
        print(e)
        return redirect('/')


