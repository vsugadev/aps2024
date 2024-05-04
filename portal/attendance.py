from flask import Blueprint, flash, redirect, request, render_template, session
from sqlalchemy.sql.expression import literal
from sqlalchemy import and_, func, case, desc
from datetime import datetime, date
import pandas as pd

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons
from common.cache import Cache as cache

from models.orm_models import db, Attendance, Enrollment, SchoolCalendar, Section, Student, UIConfig
from views.forms import AttendanceForm, AttendanceMainForm
from views.tables import Results_Attendance, Results_AttendanceDetail

attendance_blueprint = Blueprint('attendance', __name__ )

@attendance_blueprint.route('/attendance_dashboard' )
@login_required
@roles_required('admin')

def attendance_dashboard():
    util.trace()
    try:
        subquery_attend = ~db.session.query(Attendance.enrollment_id).filter( Attendance.school_date == SchoolCalendar.school_date, Attendance.enrollment_id == Enrollment.enrollment_id).exists()

        query_enroll = db.session.query(Enrollment.enrollment_id, Enrollment.section.label("section"), SchoolCalendar.school_date.label("school_date"), literal('1').label("attend_count"))
        query_enroll = query_enroll.join(SchoolCalendar, Enrollment.academic_year == SchoolCalendar.academic_year )
        query_enroll = query_enroll.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_enroll = query_enroll.filter( SchoolCalendar.attendance_required == 1 ).filter( SchoolCalendar.school_date <= date.today() )
        query_enroll = query_enroll.filter( subquery_attend)

        query_attend = db.session.query(Attendance.enrollment_id, Enrollment.section, SchoolCalendar.school_date, literal('0').label("attend_count"))
        query_attend = query_attend.join(Enrollment, Enrollment.enrollment_id == Attendance.enrollment_id )
        query_attend = query_attend.join(SchoolCalendar, SchoolCalendar.school_date == Attendance.school_date )
        query_attend = query_attend.filter(SchoolCalendar.academic_year == Enrollment.academic_year  )
        query_attend = query_attend.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_attend = query_attend.filter( SchoolCalendar.attendance_required == 1 ).filter( SchoolCalendar.school_date <= date.today() )

        sub_query = query_enroll.union(query_attend).subquery()
##      func.ifnull(func.nullif(sub_query.c.section,''), 'UnAssigned')

        query = db.session.query(sub_query.c.section.label("Class"), sub_query.c.school_date.label("School Date"),
                            func.sum(sub_query.c.attend_count).label("attend_count"),
                            case([(func.sum(sub_query.c.attend_count) > 0 , literal(cons._SYMBOL_UNTICK)),],
                                else_ = literal(cons._SYMBOL_TICK)).label("status")  )

        query = query.group_by(sub_query.c.section, sub_query.c.school_date).order_by( sub_query.c.section, desc(sub_query.c.school_date)  )

#        results = query.all()
#        for u in results:
#            print( u._asdict() )

        title = "Attendance Dashboard"

        df = pd.read_sql(query.statement,  db.engine.connect())
        if df.shape[0] == 0 :
            return render_template('main/dashboard_summary.html', tables="", rowcount= 0, title = title )
        else :
            df_summary = df.set_index(['School Date','Class']).unstack()['status']
            return render_template('main/dashboard_summary.html', tables=[df_summary.to_html(classes='data')], titles=df_summary.columns.values, rowcount=len (df_summary), title = title )

    except Exception as e:
        flash('Error while fetching attendance dashborad', 'error')
        print(e)
        return redirect('/')

@attendance_blueprint.route('/attendance_status')
@attendance_blueprint.route('/attendance_status/<int:section>')
@login_required
@roles_required('teacher')

def attendance_status(section=None):
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

        subquery_attend = ~db.session.query(Attendance.enrollment_id).filter( Attendance.school_date == SchoolCalendar.school_date, Attendance.enrollment_id == Enrollment.enrollment_id).exists()
        query_enroll = db.session.query(Enrollment.enrollment_id, Enrollment.section.label("section"), SchoolCalendar.school_date.label("school_date"), literal('1').label("attend_count"),
                          func.concat(Enrollment.section, '|', SchoolCalendar.school_date).label("section_date")  )
        query_enroll = query_enroll.join(SchoolCalendar, Enrollment.academic_year == SchoolCalendar.academic_year )
        query_enroll = query_enroll.filter( Enrollment.enrollment_status.notin_(cons._ENROLL_DISCONTINUED)).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_enroll = query_enroll.filter( SchoolCalendar.attendance_required == 1 ).filter( SchoolCalendar.school_date <= date.today() )
        query_enroll = query_enroll.filter( Enrollment.section.in_( current_section ))
        query_enroll = query_enroll.filter( subquery_attend)

        query_attend = db.session.query(Attendance.enrollment_id, Enrollment.section, SchoolCalendar.school_date, literal('0').label("attend_count") ,
                        func.concat(Enrollment.section, '|', SchoolCalendar.school_date).label("section_date") )
        query_attend = query_attend.join(Enrollment, Enrollment.enrollment_id == Attendance.enrollment_id )
        query_attend = query_attend.join(SchoolCalendar, SchoolCalendar.school_date == Attendance.school_date )
        query_attend = query_attend.filter(SchoolCalendar.academic_year == Enrollment.academic_year  )
        query_attend = query_attend.filter( Enrollment.enrollment_status.notin_(cons._ENROLL_DISCONTINUED)).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_attend = query_attend.filter( Enrollment.section.in_( current_section ))
        query_attend = query_attend.filter( SchoolCalendar.attendance_required == 1 ).filter( SchoolCalendar.school_date <= date.today() )

        sub_query = query_enroll.union(query_attend).subquery()

        query = db.session.query( sub_query.c.section, sub_query.c.school_date,  sub_query.c.section_date,
                            func.sum(sub_query.c.attend_count).label("attend_count"),
                            case([(func.sum(sub_query.c.attend_count) > 0 , literal("Pending")),],
                                else_ = literal("Completed")).label("status"),
                            case([(func.datediff( date.today(), sub_query.c.school_date ) > cache.get_value("LOCKOUT_DAYS_ATTENDANCE"), literal("Yes")),],
                                else_ = literal("No")).label("locked")  )

        query = query.group_by(sub_query.c.section, sub_query.c.school_date).order_by( sub_query.c.section, desc(sub_query.c.school_date) )
        results = query.all()

        if len(sections) > 1 :
            section_dict = {k: v for k, v in enumerate(sections)}
            title = "Attendance Status - %s" %current_section[0]
        else :
            section_dict = {}
            title = "Attendance Status"

        table = Results_Attendance(results )
        table.border = True

        return render_template('main/attendance_status.html', table=table, view='attendance', rowcount=len( results ), title = title, section_dict = section_dict )
    except Exception as e:
        flash('Error while fetching attendance status', 'error')
        print(e)
        return redirect('/')

@attendance_blueprint.route('/attendance/<string:id>' )
@login_required
@roles_required('teacher')

def attendance(id):
    util.trace()
    try:
        id_list = id.split('|')
        section = id_list[0]
        school_date  = id_list[1]

        sections = db_util.get_teacher_sections( current_user.id )
        query = SchoolCalendar.query.filter(SchoolCalendar.academic_year == session["ACADEMIC_YEAR"] ).filter(SchoolCalendar.attendance_required == 1 ).filter(SchoolCalendar.school_date <= date.today() )
        school_days = [ row.school_date.strftime("%Y-%m-%d") for row in query.all() ]

        if (section not in sections) or (school_date not in school_days) :
            flash('Warning : URL is altered manually!!', 'error')
            print('*** URL alter attempt by %s ***' %current_user.id )
            return redirect('/attendance_status')

        subquery_attend = db.session.query(Attendance.enrollment_id).join(Enrollment, Enrollment.enrollment_id == Attendance.enrollment_id )
        subquery_attend = subquery_attend.filter( Enrollment.section == section ).filter(Attendance.school_date == school_date).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )

        query_enroll = db.session.query(Enrollment.enrollment_id, Student.student_name, literal(school_date).label("school_date"), literal("").label("note"), literal(None).label("attendance_status") )
        query_enroll = query_enroll.join(Student, Enrollment.student_id == Student.student_id )
        query_enroll = query_enroll.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_enroll = query_enroll.filter( Enrollment.section == section )
        query_enroll = query_enroll.filter( Enrollment.enrollment_id.notin_( subquery_attend ))

        query_attend = db.session.query(Attendance.enrollment_id, Student.student_name, Attendance.school_date, Attendance.note, Attendance.attendance_status )
        query_attend = query_attend.join(Enrollment, Enrollment.enrollment_id == Attendance.enrollment_id )
        query_attend = query_attend.join(Student, Enrollment.student_id == Student.student_id )
        query_attend = query_attend.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_attend = query_attend.filter( Enrollment.section == section ).filter(Attendance.school_date == school_date)

        rows = query_enroll.union(query_attend).order_by(Student.student_name ).all()

#        print(str(query))
#        for u in rows:
#            print( u._asdict() )

        count = len(rows)
        first_time = True
        for attend in rows:
            if attend.attendance_status is not None :
                first_time = False
                break

        mainform = AttendanceMainForm()
        for attend in rows:
            attendance_form = AttendanceForm()
            attendance_form.school_date = attend.school_date
            attendance_form.enrollment_id = attend.enrollment_id
            attendance_form.section = section
            attendance_form.student_name = attend.student_name
            attendance_form.attendance_status_previous = attend.attendance_status
            if first_time :
                attendance_form.attendance_status = 2  # Default to Present if not entered.
            else :
                attendance_form.attendance_status = attend.attendance_status
            attendance_form.note = attendance_form.note_previous = attend.note
            mainform.attendance.append_entry(attendance_form)
        title = 'Take Attendance : %s (%s) %s' %(util.format_date(school_date), section, '- [NOT SUBMITTED]' if  first_time else '')

        return render_template('main/attendance_update.html', title=title, form=mainform, count=count )

    except Exception as e:
        flash('Error while fetching Attendance List', 'error')
        print(e)
        return redirect('/attendance_status')


@attendance_blueprint.route('/attendance_update', methods=['POST'])
@login_required
@roles_required('teacher')

def attendance_update():
    util.trace()
    try :
        on_commit = False

        data = request.form.to_dict()
        count = util.count( data.keys() )
        attend_list_update =  []
        attend_list_insert =  []

        for row in range(count) :
            school_date = data.get("attendance-%s-school_date" %row)
            enrollment_id = data.get("attendance-%s-enrollment_id" %row)
            attendance_status = data.get("attendance-%s-attendance_status" %row, 0)
            note = data.get("attendance-%s-note" %row)
            section = data.get("attendance-%s-section" %row)
            previous_status = data.get("attendance-%s-attendance_status_previous" %row)
            previous_note = data.get("attendance-%s-note_previous" %row)
            attendance_score = 1 if int(attendance_status) > 1 else 0

            if attendance_status != previous_status or note != previous_note :
                attend_data = {  'school_date': school_date,
                                        'enrollment_id' : enrollment_id,
                                        'attendance_status' : attendance_status,
                                        'attendance_score' : attendance_score,
                                        'note' : note ,
                                        'section' : section,
                                        'last_updated_at' : datetime.now() ,
                                        'last_updated_id' : current_user.id
                                    }

                if previous_status : # attendance_id :   ## Modifed
                    attend_list_update.append( attend_data )
                else :   ## New
                    attend_list_insert.append( attend_data )

        if attend_list_update or attend_list_insert :
            if ( date.today() - datetime.strptime(school_date, '%Y-%m-%d').date()).days > cache.get_value("LOCKOUT_DAYS_ATTENDANCE") :
                flash('Attendance has been locked for %s, no updates made' %school_date , 'error')
                return redirect('/attendance_status')

            on_commit = True
            if attend_list_update :
                db.session.bulk_update_mappings(Attendance, attend_list_update )
            if attend_list_insert :
                db.session.bulk_insert_mappings(Attendance, attend_list_insert )
            db.session.commit()
            on_commit = False
            flash('Attendance info successfully updated for %d students for %s (%s)' % (len(attend_list_update) + len(attend_list_insert), school_date, section) , 'success')
        else :
            flash('No changes to update' , 'success')

        return redirect('/attendance_status')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating attendance', 'error')
        print(e)
        return redirect('/attendance_status')

@attendance_blueprint.route('/attendance_detail/<string:id>' )
@login_required
@roles_required(['teacher', 'parent', 'admin'])

def attendance_detail(id):
    util.trace()
    try:
        id_list = id.split('|')
        enroll_id = int(id_list[0])
        academic_year = int(id_list[1])
        view = int(id_list[2])
        if view == 1 :
            sections = db_util.get_teacher_sections( current_user.id )
            query = Enrollment.query.filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] ).filter( Enrollment.section.in_( sections ))
            enroll_list = [ row.enrollment_id for row in query.all() ]
        elif view == 0 :
            query = db.session.query(Enrollment.enrollment_id ).join(Student, Student.student_id == Enrollment.student_id) \
                        .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
                        .filter( Enrollment.academic_year == academic_year ) \
                        .filter( Student.parent_id == current_user.id ) \
                        .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED ))

            enroll_list = [ row.enrollment_id for row in query.all() ]
        elif view == 2 and db_util.is_user_role( current_user.id, 'admin')  :
            enroll_list = [ enroll_id ]

        if enroll_id not in enroll_list or view > 2:
            flash('Warning : URL is altered manually!!', 'error')
            print('*** URL alter attempt by %s ***' %current_user.id )
            return redirect('/')

        subq_status = db.session.query(Attendance.school_date).filter(Attendance.enrollment_id == enroll_id )

        query_missing = db.session.query(SchoolCalendar.school_date.label("school_date"), literal('').label("attendance_status"), literal('').label("note") ) \
                        .filter( SchoolCalendar.school_date.notin_( subq_status )) \
                        .filter( SchoolCalendar.academic_year == academic_year ) \
                        .filter( SchoolCalendar.attendance_required == 1) \
                        .filter( SchoolCalendar.school_date <= date.today() )

        query_attend = db.session.query(Attendance.school_date, UIConfig.category_value.label("attendance_status"), Attendance.note ) \
                        .join( UIConfig, UIConfig.category_key == Attendance.attendance_status ) \
                        .filter( UIConfig.category == 'ATTENDACE_STATUS' ) \
                        .filter( Attendance.enrollment_id == enroll_id )

        rows = query_missing.union(query_attend).order_by(SchoolCalendar.school_date ).all()

        result_name = db.session.query(Student.student_name).join(Enrollment, Enrollment.student_id == Student.student_id) \
                            .filter(Enrollment .enrollment_id == enroll_id).one()
        student_name = result_name.student_name

#        for u in rows:
#            print( u._asdict() )

        count = len(rows)
        table = Results_AttendanceDetail( rows )
        table.border = True
        return render_template('main/show_details.html', table=table, mode='show_attend', rowcount=count, title = "Attendance Details for %s" %student_name, view =view )

    except Exception as e:
        flash('Error while fetching Attendance Details', 'error')
        print(e)
        return redirect('/')

