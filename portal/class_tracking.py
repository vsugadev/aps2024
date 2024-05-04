from flask import Blueprint, flash, redirect, request, render_template, session
from sqlalchemy.sql.expression import literal
from sqlalchemy import and_, func, case, desc
from datetime import datetime, date
import pandas as pd

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.mail import mail

from models.orm_models import db, ClassTracking, SchoolCalendar, Section
from views.forms import ClassTrackingForm
from views.tables import Results_ClassTracking, Results_ClassTrackingAdmin, Results_ClassTrackingDetails, Results_ClassTrackingMain

class_tracking_blueprint = Blueprint('class_tracking', __name__ )

@class_tracking_blueprint.route('/class_tracking_dashboard' )
@login_required
@roles_required('admin')

def class_tracking_dashboard():
    util.trace()
    try:
        query = db.session.query(SchoolCalendar.school_date.label("school_date" ), Section.section.label("section"),
                    case([(ClassTracking.is_email_sent == 1, literal(cons._SYMBOL_TICK))], else_ = literal(cons._SYMBOL_UNTICK)).label('status') ,
                    func.concat( Section.section, '|', literal(0), '|', func.unix_timestamp(date.today())).label("section_id"), \
                    func.concat(SchoolCalendar.school_date, '|', literal(1), '|', func.unix_timestamp(date.today())).label("date_id")) \
                .join(Section, Section.academic_year == SchoolCalendar.academic_year ) \
                .outerjoin( ClassTracking, and_( ClassTracking.school_date == SchoolCalendar.school_date, ClassTracking.section == Section.section )) \
                .filter( SchoolCalendar.academic_year == session["ACADEMIC_YEAR"] ) \
                .filter( SchoolCalendar.attendance_required == 1 ).filter( SchoolCalendar.school_date <= date.today() ) \
                .filter( SchoolCalendar.school_date >= "2020-12-01" )
        query = query.order_by( desc(SchoolCalendar.school_date), Section.section )

#        results = query.all()
#        for u in results:
#            print( u._asdict() )

        title = "Class Progress Dashboard"
        df = pd.read_sql(query.statement,  db.engine.connect())
        if df.shape[0] == 0 :
            return render_template('main/dashboard_summary.html', tables="", rowcount= 0, title = title )
        else :
            df['school_date_link'] = df.apply(util.get_url_tracking, by='date', axis=1)
            df['class_link'] = df.apply(util.get_url_tracking, by='section', axis=1)
            df.rename(columns={'school_date_link':'School Date', 'class_link':'Class' }, inplace=True)
            df_summary = df.set_index(['School Date','Class']).unstack()['status']
            return render_template('main/dashboard_summary.html', tables=[df_summary.to_html(classes='data', escape = False)], titles=df_summary.columns.values, rowcount=len (df_summary), title = title )

    except Exception as e:
        flash('Error while fetching class progess dashboard', 'error')
        print(e)
        return redirect('/')


@class_tracking_blueprint.route('/class_tracking_list/<string:id>' )
@login_required
@roles_required('admin')

def class_tracking_list( id ):
    util.trace()
    id_list = id.split('|')
    type  = int(id_list[1])
    if type == 0 :
        school_date = None
        section = id_list[0]
        mode = 3
    else :
        school_date = id_list[0]
        section = None
        mode = 4
#    print( "School Date : %s - Section : %s " %(school_date, section ) )
    return class_tracking_status(mode, school_date, section)


@class_tracking_blueprint.route('/class_status' )
@login_required
@roles_required('parent')

def class_status():
    util.trace()
    return class_tracking_status(mode = 0)

# mode : 0 for parents, 1 for teacher summary, 2 for teacher details, 3 for admin by class & 4 for admin by date

@class_tracking_blueprint.route('/class_tracking_status')
@class_tracking_blueprint.route('/class_tracking_status/<int:section>')

@login_required
@roles_required(['teacher', 'parent', 'admin'])

def class_tracking_status(mode=1, school_date = None, section = None):
    util.trace()
    try:
        if mode == 1:
            view = int(request.args.get('view',0))
            if view == 1 :
                mode = 2

            sections = db_util.get_teacher_sections( current_user.id )
            if not sections  :
                flash('No Class assigned yet!', 'success')
                return redirect('/')

            if section and len(sections) > section :
                current_section = [ sections[section] ]
            else :
                current_section =  [ sections[0] ]

        elif mode == 0:
            sections = db_util.get_enrolled_sections( current_user.id )
            if not sections  :
                flash('No Class assigned yet!', 'success')
                return redirect('/')

        query = db.session.query(SchoolCalendar.school_date, Section.section, ClassTracking.class_date, ClassTracking.class_start_time, ClassTracking.class_end_time,
                    ClassTracking.lesson_no, ClassTracking.teacher1_id, ClassTracking.teacher2_id, ClassTracking.substitute_teacher, ClassTracking.class_activities,
                    ClassTracking.homework_paper, ClassTracking.homework_audio, ClassTracking.note_to_parents, ClassTracking.note_to_admin, ClassTracking.note_from_admin,
                    ClassTracking.email_sent_date, ClassTracking.volunteers_present, ClassTracking.volunteers_activities,
                    case([(ClassTracking.is_email_sent == 1, literal("Published")), (ClassTracking.is_email_sent == 0, literal("Saved"))], else_ = literal("Pending")).label('status'),
                    case([(ClassTracking.is_email_sent == 1, literal( cons._SYMBOL_LOCK ))], else_ = literal("")).label('locked') ,
                    func.concat(Section.section, '|', func.coalesce(ClassTracking.is_email_sent, -1), '|', SchoolCalendar.school_date).label("section_date") ) \
                .join(Section, Section.academic_year == SchoolCalendar.academic_year ) \
                .outerjoin( ClassTracking, and_( ClassTracking.school_date == SchoolCalendar.school_date, ClassTracking.section == Section.section )) \
                .filter( SchoolCalendar.academic_year == session["ACADEMIC_YEAR"] ) \
                .filter( SchoolCalendar.attendance_required == 1 ).filter( SchoolCalendar.school_date <= date.today() ) \
                .filter( SchoolCalendar.school_date >= "2020-12-01" )

        title = "Class Progress"
        section_dict = {}
        if mode == 0 :
            query = query.filter( Section.section.in_( sections )).filter( ClassTracking.is_email_sent == 1 )
        elif mode in [1, 2] :
            query = query.filter( Section.section.in_( current_section ))
            if len(sections) > 1 :
                section_dict = {k: v for k, v in enumerate(sections)}
                title = "%s - %s" %( title, current_section[0] )
        elif mode == 3 :
            query = query.filter( Section.section == section).filter( ClassTracking.is_email_sent == 1 )
        elif mode == 4 :
            query = query.filter( SchoolCalendar.school_date == school_date).filter( ClassTracking.is_email_sent == 1 )
        else :
            flash('Invalid Option!', 'success')
            return redirect('/')

        if mode == 1 :
            results = query.order_by( Section.section, desc(SchoolCalendar.school_date) ).all()
        else :
            results = query.order_by( Section.section, SchoolCalendar.school_date ).all()

        if mode == 0 :
            table = Results_ClassTrackingMain(results )
            title = "Class Updates"
        elif mode == 1 :
            table = Results_ClassTracking(results )
        elif mode == 2 :
            table = Results_ClassTrackingDetails(results )
        elif mode in (3 , 4):
            table = Results_ClassTrackingAdmin(results )  ## To be changed for Admin

        table.border = True

        return render_template('main/attendance_status.html', table=table, mode=mode, rowcount=len( results ) , title = title, view="tracking" , section_dict = section_dict, section=section if section else 0)
    except Exception as e:
        flash('Error while fetching class progress', 'error')
        print(e)
        return redirect('/')


@class_tracking_blueprint.route('/class_tracking/<string:id>' , methods=['GET', 'POST'])
@class_tracking_blueprint.route('/class_tracking/<string:id>/<int:mode>' , methods=['GET', 'POST'])

@login_required
@roles_required(['teacher', 'admin' ] )

def class_tracking(id, mode=0):
    util.trace()
    try:
        id_list = id.split('|')
        section = id_list[0]
        status  = id_list[1]
        school_date = id_list[2]

        sections = db_util.get_teacher_sections( current_user.id )
        query = SchoolCalendar.query.filter(SchoolCalendar.academic_year == session["ACADEMIC_YEAR"] ).filter(SchoolCalendar.attendance_required == 1 ).filter(SchoolCalendar.school_date <= date.today() )
        school_days = [ row.school_date.strftime("%Y-%m-%d") for row in query.all() ]

        if not db_util.is_user_role( current_user.id, 'admin') and ((section not in sections) or (school_date not in school_days)) :
            flash('Warning : URL is altered manually!!', 'error')
            print('*** URL alter attempt by %s ***' %current_user.id )
            return redirect('/class_tracking_status')

#        print( "Status : %s - Section : %s - School Date : %s"  %(status, section, school_date) )
        if status == '-1':
            tracking_obj = ClassTracking()
            tracking_obj.school_date =  datetime.strptime(school_date, "%Y-%m-%d").date()  # .strftime('%Y-%m-%d')
            tracking_obj.section = section
            tracking_obj.teacher1_id = current_user.id
            tracking_obj.lesson_no = db_util.get_next_lesson( section )
            class_day, tracking_obj.class_start_time  = db_util.get_class_day_time( section )
            school_day, _ = db_util.get_school_day_time()
            if school_day == class_day :
                tracking_obj.class_date =  tracking_obj.school_date

            tracking_obj.volunteers_present = db_util.get_last_session_volunteer( section )
        else :
            tracking_obj = db.session.query(ClassTracking).filter(ClassTracking.section == section).filter(ClassTracking.school_date == school_date).first()

        form = ClassTrackingForm(request.form, section = section, academic_year = session["ACADEMIC_YEAR"], obj=tracking_obj )
        locked = False
        form.mode = mode
        if tracking_obj.is_email_sent :
            form.is_email_sent.checked = True
            if mode == 0 :
                locked = True
            else :
                form.note_from_admin.render_kw = {'readonly': False}
                form.class_date.render_kw = {'readonly': True}
                form.class_start_time.render_kw = {'readonly': True}
                form.class_end_time.render_kw = {'readonly': True}
                form.teacher1_id.render_kw = {'readonly': True}
                form.teacher2_id.render_kw = {'readonly': True}
                form.substitute_teacher.render_kw = {'readonly': True}
                form.lesson_no.render_kw = {'readonly': True}
                form.class_activities.render_kw = {'readonly': True}
                form.homework_paper.render_kw = {'readonly': True}
                form.homework_audio.render_kw = {'readonly': True}
                form.note_to_parents.render_kw = {'readonly': True}
                form.note_to_admin.render_kw = {'readonly': True}
                form.volunteers_present.render_kw = {'readonly': True}
                form.volunteers_activities.render_kw = {'readonly': True}
                form.is_email_sent.render_kw = {'readonly': True}
                form.email_sent_date.render_kw = {'readonly': True}

        if request.method == 'POST' and form.validate():
            # Copy form fields to class fields
#            form.populate_obj(tracking_obj)
            if form.mode == 1 :
                tracking_data = {   'school_date': request.form.get("school_date"),
                                    'section' : request.form.get("section"),
                                    'academic_year' : session["ACADEMIC_YEAR"],
                                    'note_from_admin' : request.form.get("note_from_admin"),
                                    'last_updated_at' : datetime.now(),
                                    'last_updated_id' : current_user.id
                                    }

                tracking_obj = None
                db.session.bulk_update_mappings(ClassTracking, [tracking_data] )
                db.session.commit()
                flash('Admin Response Successfully Updated..', 'success')
                return redirect('/class_tracking_dashboard')
            else :
                form.populate_obj(tracking_obj)
                tracking_obj.last_updated_at = datetime.now()
                tracking_obj.last_updated_id = current_user.id

                if form.email.data:
                    tracking_obj.email_sent_date = datetime.today()
                    tracking_obj.is_email_sent = True
                if tracking_obj.teacher2_id == -1 :
                    tracking_obj.teacher2_id = None
                if tracking_obj.lesson_no == -1 :
                    tracking_obj.lesson_no = None
                if not tracking_obj.academic_year :
                    tracking_obj.academic_year = session["ACADEMIC_YEAR"]
                    tracking_obj.created_at = datetime.now()
                    db.session.add(tracking_obj)
                db.session.commit()
                action = "Updated"
                if form.email.data:
                    if db_util.get_config( "PUBLISH_CLASS_PROGRESS") == '1' :
                        notify_class_progress( tracking_obj.school_date, tracking_obj.section)
                        action = "Published"
                flash('Class Progress Successfully %s..' %action, 'success')
                return redirect('/class_tracking_status')

        # Process GET or invalid POST
        return render_template('main/class_tracking.html', form=form, section = section, school_date = util.format_date(school_date), locked = locked, mode = mode, id = id )

    except Exception as e:
        flash('Class Tracking Update Failed..', 'error')
        db.session.rollback()
        print(e)
        return redirect('/class_tracking_status')


def notify_class_progress( school_date, section) :
    util.trace()
    try:
        email_parents = db_util.get_email_for_class_parents( section )
        email_students = db_util.get_email_for_class_students( section )
        email_teachers = db_util.get_email_for_teachers( section )
        email_class = db_util.get_email_for_class( section )
        teachers_map = db_util.get_map_teachers (section)

#        print( "Parents email : %s" %email_parents )
#        print( "Parents email : %s" %email_students )
#        print( "Teachers email : %s" %email_teachers )
#        print( "Class email : %s" %email_class )
#        print( "teachers_map : %s" %teachers_map )

        tracking_row = ClassTracking.query.filter(ClassTracking.section == section ).filter(ClassTracking.school_date == school_date).first()
        teacher_list = []
        teacher_list.append( teachers_map.get(tracking_row.teacher1_id) )
        if tracking_row.teacher2_id :
            teacher_list.append( teachers_map.get(tracking_row.teacher2_id) )

        if tracking_row.substitute_teacher :
            teacher_list.append( tracking_row.substitute_teacher + " (Substitute)" )

        if len(teacher_list) == 1 :
            teachers = teacher_list[0]
        elif len(teacher_list) == 2 :
            teachers = teacher_list[0] + " & " + teacher_list[1]
        else :
            teachers = teacher_list[0] + ", " + teacher_list[1] + " & " + teacher_list[2]

        class_date = util.format_date(tracking_row.class_date)
        # APS admin team like to send class tracking email alerts only to the APS Email ID. Hence not sending the emails to parents.
        # email.send_class_progress(mail, email_class , email_parents + email_students, email_teachers + [email_class], section, util.format_date(school_date), class_date, teachers, tracking_row )
        email.send_class_progress(mail, email_class , email_students, email_teachers + [email_class], section, util.format_date(school_date), class_date, teachers, tracking_row )

    except Exception as e:
        flash('Error while publishing class progess', 'error')
        print(e)
        raise e

