from flask import Blueprint, flash, redirect, request, render_template, session
from sqlalchemy.sql.expression import literal
from sqlalchemy import and_, func, case
from datetime import datetime
import pandas as pd

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons

from models.orm_models import db, Enrollment, Lesson, Homework, Section, Student
from views.forms import HomeworkMainForm, HomeworkForm
from views.tables import Results_Homework, Results_HomeworkDetail

homework_blueprint = Blueprint('homework', __name__ )

@homework_blueprint.route('/homework_dashboard' )
@login_required
@roles_required('admin')

def homework_dashboard():
    util.trace()
    try:
        hw_type = int(request.args.get('type',0))
        subquery_hw = ~db.session.query(Homework.enrollment_id).filter( Homework.lesson_no == Lesson.lesson_no, Homework.enrollment_id == Enrollment.enrollment_id, Homework.homework_type == hw_type ).exists()

        query_enroll = db.session.query(Enrollment.enrollment_id, Enrollment.section.label("section"), Lesson.lesson_no.label("lesson_no"), literal('1').label("homework_count"))
        query_enroll = query_enroll.join(Lesson, Enrollment.academic_year == Lesson.academic_year )
        query_enroll = query_enroll.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_enroll = query_enroll.filter( subquery_hw)

        query_hw = db.session.query(Homework.enrollment_id, Enrollment.section, Lesson.lesson_no, literal('0').label("homework_count"))
        query_hw = query_hw.join(Enrollment, Enrollment.enrollment_id == Homework.enrollment_id )
        query_hw = query_hw.join(Lesson, Lesson.lesson_no == Homework.lesson_no )
        query_hw = query_hw.filter(Lesson.academic_year == Enrollment.academic_year, Homework.homework_type == hw_type  )
        query_hw = query_hw.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        sub_query = query_enroll.union(query_hw).subquery()

        query = db.session.query( sub_query.c.section.label("Class"), sub_query.c.lesson_no.label("Lesson #"),
                            func.sum(sub_query.c.homework_count).label("homework_count"),
                            case([(func.sum(sub_query.c.homework_count) > 0 , literal(cons._SYMBOL_UNTICK)),],
                                else_ = literal(cons._SYMBOL_TICK)).label("status"))

        query = query.group_by(sub_query.c.section, sub_query.c.lesson_no).order_by( sub_query.c.section, sub_query.c.lesson_no  )

        # title = '%s Dashboard' %('Homework' if hw_type == 0 else 'Project')
        if hw_type == 0 :
            type = 'Homework'
        elif hw_type == 1 :
            type = 'Project'
        elif hw_type == 2 :
            type = 'Classwork'
        else :
            type = 'Quiz'
        title = '%s Dashboard' %(type)

        df = pd.read_sql(query.statement,  db.engine.connect())
        if df.shape[0] == 0 :
            return render_template('main/dashboard_summary.html', tables="", rowcount= 0, title = title )
        else :
            df_summary = df.set_index(['Lesson #','Class']).unstack()['status']
            return render_template('main/dashboard_summary.html',  tables=[df_summary.to_html(classes='data')], titles=df_summary.columns.values, rowcount=len (df_summary), title = title )

    except Exception as e:
        flash('Error while fetching homework dashborad', 'error')
        print(e)
        return redirect('/')

@homework_blueprint.route('/homework_status')
@homework_blueprint.route('/homework_status/<int:section>')
@login_required
@roles_required('teacher')

def homework_status(section=None):
    util.trace()
    try:
        hw_type = int(request.args.get('type',0))
        sections = db_util.get_teacher_sections( current_user.id )
        if not sections  :
            flash('No Class assigned yet!', 'success')
            return redirect('/')

        if section and len(sections) > section :
            current_section = [ sections[section] ]
        else :
            current_section =  [ sections[0] ]

        subquery_hw = ~db.session.query(Homework.enrollment_id).filter( Homework.lesson_no == Lesson.lesson_no, Homework.enrollment_id == Enrollment.enrollment_id, Homework.homework_type == hw_type ).exists()

        query_enroll = db.session.query(Enrollment.enrollment_id, Enrollment.section.label("section"), Lesson.lesson_no.label("lesson_no"), literal('1').label("homework_count"),
                        func.concat(Enrollment.section, '|', hw_type , '|', Lesson.lesson_no).label("section_lesson")  )
        query_enroll = query_enroll.join(Lesson, Enrollment.academic_year == Lesson.academic_year )
        query_enroll = query_enroll.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_enroll = query_enroll.filter( Enrollment.section.in_( current_section ))
        query_enroll = query_enroll.filter( subquery_hw)

        query_hw = db.session.query(Homework.enrollment_id, Enrollment.section, Lesson.lesson_no, literal('0').label("homework_count") ,
                        func.concat(Enrollment.section, '|', hw_type, '|', Lesson.lesson_no).label("section_lesson") )
        query_hw = query_hw.join(Enrollment, Enrollment.enrollment_id == Homework.enrollment_id )
        query_hw = query_hw.join(Lesson, Lesson.lesson_no == Homework.lesson_no )
        query_hw = query_hw.filter(Lesson.academic_year == Enrollment.academic_year, Homework.homework_type == hw_type  )
        query_hw = query_hw.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_hw = query_hw.filter( Enrollment.section.in_( current_section ))

        sub_query = query_enroll.union(query_hw).subquery()

        query = db.session.query( sub_query.c.section, sub_query.c.lesson_no,  sub_query.c.section_lesson,
                            func.sum(sub_query.c.homework_count).label("homework_count"),
                            case([(func.sum(sub_query.c.homework_count) > 0 , literal("Pending")),],
                                else_ = literal("Completed")).label("status"))

        query = query.group_by(sub_query.c.section, sub_query.c.lesson_no).order_by( sub_query.c.section, sub_query.c.lesson_no,  )
        results = query.all()
        # title = '%s Tracking' %('Homework' if hw_type == 0  else 'Project')
        if hw_type == 0 :
            type = 'Homework'
        elif hw_type == 1 :
            type = 'Project'
        elif hw_type == 2 :
            type = 'Quiz'
        else :
            type = 'Classwork'
        title = '%s Tracking' %(type)

        if len(sections) > 1 :
            section_dict = {k: v for k, v in enumerate(sections)}
            title = title + " - %s" %current_section[0]
        else :
            section_dict = {}

        table = Results_Homework(results )
        table.border = True
        return render_template('main/homework_status.html', table=table, title=title, rowcount=len( results ), section_dict=section_dict, type=hw_type )
    except Exception as e:
        flash('Error while fetching homework status', 'error')
        print(e)
        return redirect('/')


@homework_blueprint.route('/homework/<string:id>' )
@login_required
@roles_required('teacher')

def homework(id):
    util.trace()
    try:
        id_list = id.split('|')
        section, hw_type, lesson_no = id_list[0], int(id_list[1]), int(id_list[2])

        sections = db_util.get_teacher_sections( current_user.id )

        if (section not in sections) or lesson_no < 1 or lesson_no > 20 or (hw_type not in [0,1,2,3 ]) :
            flash('Warning : URL is altered manually!!', 'error')
            print('*** URL alter attempt by %s ***' %current_user.id )
            return redirect('/homework_status?type=%d' %hw_type )

        subquery_hw = db.session.query(Homework.enrollment_id).join(Enrollment, Enrollment.enrollment_id == Homework.enrollment_id )
        subquery_hw = subquery_hw.filter( Enrollment.section == section ).filter(Homework.lesson_no == lesson_no)
        subquery_hw = subquery_hw.filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] ).filter(Homework.homework_type == hw_type)

        query_enroll = db.session.query(Enrollment.enrollment_id, Student.student_name, literal(lesson_no).label("lesson_no"), \
            literal(None).label("homework_date"), literal("").label("note"), literal(None).label("homework_status"), \
            literal(None).label("homework_score") )
        query_enroll = query_enroll.join(Student, Enrollment.student_id == Student.student_id )
        query_enroll = query_enroll.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_enroll = query_enroll.filter( Enrollment.section == section )
        query_enroll = query_enroll.filter( Enrollment.enrollment_id.notin_( subquery_hw ))

        query_hw = db.session.query(Homework.enrollment_id, Student.student_name, Homework.lesson_no, Homework.homework_date, \
                Homework.note, Homework.homework_status, Homework.homework_score )
        query_hw = query_hw.join(Enrollment, Enrollment.enrollment_id == Homework.enrollment_id )
        query_hw = query_hw.join(Student, Enrollment.student_id == Student.student_id )
        query_hw = query_hw.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        query_hw = query_hw.filter( Enrollment.section == section ).filter(Homework.lesson_no == lesson_no )
        query_hw = query_hw.filter( Homework.homework_type == hw_type )
        rows = query_enroll.union(query_hw).order_by(Student.student_name ).all()

        count = len(rows)
        first_time = True
        for hw in rows:
            if hw.homework_status is not None :
                first_time = False
                break

        hw_date = None
        main_form = HomeworkMainForm()
        for hw in rows:
            hw_form = HomeworkForm()
            hw_form.lesson_no = hw.lesson_no
            hw_form.enrollment_id = hw.enrollment_id
            hw_form.homework_type = hw_type
            hw_form.section = section
            hw_form.student_name = hw.student_name
            hw_form.homework_score_previous = hw.homework_score

            if first_time or (hw.homework_status and hw.homework_status == 1) :
                hw_form.homework_status.checked = True
                hw_form.homework_status_previous = 'y'
            else :
                hw_form.homework_status  = None
                hw_form.homework_status_previous = 'n'

            hw_form.note = hw_form.note_previous = hw.note

            main_form.homework.append_entry(hw_form)
            if hw.homework_date and hw_date is None :
                hw_date = hw.homework_date

        if hw_date :
            main_form.homework_date_previous = hw_date
            main_form.homework_date.default  = hw_date.strftime('%Y-%m-%d')

        # title = '%s Tracking' %('Homework' if hw_type == 0 else 'Project')
        if hw_type == 0 :
            type = 'Homework'
        elif hw_type == 1 :
            type = 'Project'
        elif hw_type == 2 :
            type = 'Quiz'
        else :
            type = 'Classwork'
        title = '%s Tracking' %(type)

        sub_title = 'Lesson / Week # :  %s (%s) %s' %( lesson_no, section, '- [NOT SUBMITTED]' if first_time else '' )
        return render_template('main/homework_update.html', title=title, sub_title = sub_title, type=hw_type, form=main_form, count=count )

    except Exception as e:
        flash('Error while fetching Homework Details', 'error')
        print(e)
        return redirect('/homework_status?type=%s' %hw_type )


@homework_blueprint.route('/homework_update', methods=['POST'])
@login_required
@roles_required('teacher')

def homework_update():
    util.trace()
    try :
        on_commit = False

        data = request.form.to_dict()
        count = util.count( data.keys() )
#        print(data)
#        print( "data %s , count %s" %(len(data), count ) )
        hw_list_update =  []
        hw_list_insert =  []

        hw_date = data.get("homework_date")
        hw_type = data.get("hw_type")
#        print("HW Type : %s" %hw_type)

        previous_date = data.get("homework_date_previous")

        for row in range(count) :
            enrollment_id = data.get("homework-%s-enrollment_id" %row)
            homework_type = data.get("homework-%s-homework_type" %row)
            lesson_no = data.get("homework-%s-lesson_no" %row)

            hw_type = homework_type
            section = data.get("homework-%s-section" %row)
            homework_status = data.get("homework-%s-homework_status" %row , 'n')
            note = data.get("homework-%s-note" %row)
            previous_status = data.get("homework-%s-homework_status_previous" %row)
            previous_score  = data.get("homework-%s-homework_score_previous" %row)
            previous_note = data.get("homework-%s-note_previous" %row)
            if homework_status == 'y' :
                homework_score = 1
                homework_status = 1
            else :
                homework_score = 0
                homework_status = 0

            if homework_status != previous_status or note != previous_note or hw_date != previous_date or homework_score != previous_score :
                hw_data = { 'enrollment_id' : enrollment_id,
                                'homework_type' : homework_type,
                                'lesson_no' : lesson_no,
                                'academic_year' : session["ACADEMIC_YEAR"],
                                'section' : section,
                                'homework_status' : homework_status,
                                'homework_score' : homework_score,
                                'homework_date' : hw_date,
                                'note' : note ,
                                'last_updated_at' : datetime.now() ,
                                'last_updated_id' : current_user.id
                              }
#                print( hw_data )
                if previous_score :   ## Modifed
                    hw_list_update.append( hw_data )
                else :   ## New
                    hw_list_insert.append( hw_data )

        if hw_list_update or hw_list_insert :
            ##TODO : Add logic for locking

            on_commit = True
            if hw_list_update :
                db.session.bulk_update_mappings(Homework, hw_list_update )
            if hw_list_insert :
                db.session.bulk_insert_mappings(Homework, hw_list_insert )
            db.session.commit()
            on_commit = False
            flash('Homework details successfully updated for %d students' % (len(hw_list_update) + len(hw_list_insert) ) , 'success')
        else :
            flash('No score changes to update' , 'success')

        return redirect('/homework_status?type=%s' %hw_type )

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating homework details', 'error')
        print(e)
        return redirect('/homework_status?type=%s' %hw_type )


@homework_blueprint.route('/homework_detail/<string:id>' )
@login_required
@roles_required(['teacher', 'parent', 'admin'])

def homework_detail(id):
    util.trace()
    try:
        id_list = id.split('|')
        enroll_id = int(id_list[0])
        academic_year = int(id_list[1])
        view = int(id_list[2])
        type = int(request.args.get('type',0))
        if view == 1 :
            sections = db_util.get_teacher_sections( current_user.id )

            query = Enrollment.query.filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] ).filter( Enrollment.section.in_( sections ))
            enroll_list = [ row.enrollment_id for row in query.all() ]
        elif view == 0 :
            query = db.session.query(Enrollment.enrollment_id ).join(Student, Student.student_id == Enrollment.student_id) \
                        .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
                        .filter( Enrollment.academic_year == academic_year ) \
                        .filter( Student.parent_id == current_user.id ) \
                        .filter( Enrollment.enrollment_status !=  3 )

            enroll_list = [ row.enrollment_id for row in query.all() ]
        elif view == 2 and db_util.is_user_role( current_user.id, 'admin')  :
            enroll_list = [ enroll_id ]

        if enroll_id not in enroll_list or type > 1 or view > 2 :
            flash('Warning : URL is altered manually!!', 'error')
            print('*** URL alter attempt by %s ***' %current_user.id )
            return redirect('/')

        subq_status = db.session.query(Homework.lesson_no).filter(Homework.enrollment_id == enroll_id, Homework.homework_type == type )

        query_missing = db.session.query(Lesson.lesson_no.label("lesson_no"), literal(None).label("homework_date"), literal('').label("homework_status"), literal('').label("note") ) \
                        .filter( Lesson.lesson_no.notin_( subq_status )) \

        query_hw = db.session.query(Homework.lesson_no, Homework.homework_date, Homework.homework_status, Homework.note ) \
                        .filter( Homework.enrollment_id == enroll_id ) \
                        .filter( Homework.homework_type == type )

        rows = query_missing.union(query_hw).order_by(Lesson.lesson_no ).all()

        result_name = db.session.query(Student.student_name).join(Enrollment, Enrollment.student_id == Student.student_id) \
                            .filter(Enrollment.enrollment_id == enroll_id).one()
        student_name = result_name.student_name

#        for u in rows:
#            print( u._asdict() )

        # title = "%s Details for %s" %( 'Project' if type == 1 else 'Homework' , student_name)
        if hw_type == 0 :
            type = 'Homework'
        elif hw_type == 1 :
            type = 'Project'
        elif hw_type == 2 :
            type = 'Classwork'
        else :
            type = 'Quiz'
        title = '%s Details for %s' %(type, student_name)

        count = len(rows)
        table = Results_HomeworkDetail( rows )
        table.border = True
        return render_template('main/show_details.html', table=table, mode='show_homework', rowcount=count, title = title, view=view )

    except Exception as e:
        flash('Error while fetching Homework Details', 'error')
        print(e)
        return redirect('/')

