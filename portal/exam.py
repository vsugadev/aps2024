from flask import Blueprint, flash, redirect, request, render_template, session
from datetime import datetime, date
from sqlalchemy.sql.expression import literal
import sqlalchemy
from sqlalchemy import and_, func
import pandas as pd
import numpy as np

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons

from models.orm_models import db, Enrollment, Exam, Section, Student, UIConfig
from views.forms import ExamForm, ExamMainForm, SearchExamForm

exam_blueprint = Blueprint('exam', __name__ )

@exam_blueprint.route('/exam_dashboard' )
@login_required
@roles_required('admin')

def exam_dashboard():
    util.trace()
    try:
        term_dict = { c.category_key : c.category_value for c in UIConfig.query.filter_by(category = 'EXAM_TERM' ).all() }
        df_list = []
        for term_id, term_name in term_dict.items():
            query = db.session.query(Enrollment.section.label("section"), UIConfig.category_key, UIConfig.category_value,
                        func.sum(func.coalesce(Exam.exam_score, -10000)).label("exam_count") ,
                        func.sum(sqlalchemy.cast(Exam.is_ptm_completed, sqlalchemy.Integer)).label("ptm_count"),
                        func.count(Enrollment.enrollment_id).label("class_count"),
                        func.concat( Enrollment.section, '|', literal(0), '|', literal(5), '|',func.unix_timestamp(date.today())).label("section_id"),
                        func.concat( literal(term_id), '|', literal(1), '|',literal(6), '|',func.unix_timestamp(date.today())).label("link_id")) \
                        .outerjoin( Exam, and_( Exam.enrollment_id == Enrollment.enrollment_id, Exam.trimester_id == term_id )) \
                        .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                        .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
                        .filter( UIConfig.category_key == term_id ) \
                        .filter( UIConfig.category == 'EXAM_TERM' ) \
                        .filter( func.length(Enrollment.section) > 0)
            query = query.group_by( Enrollment.section, UIConfig.category_key, UIConfig.category_value ).order_by( Enrollment.section, UIConfig.category_key )

#            results = query.all()
#            for u in results:
#                print( u._asdict() )

            df = pd.read_sql(query.statement,  db.engine.connect())
            df_list.append(df)

        title = "Trimester Dashboard"

        df = pd.concat( df_list )
        if df.shape[0] == 0 :
            return render_template('main/dashboard_summary.html', tables="", rowcount= 0, title = title )
        else :
            df.columns = ['section', 'term_id', 'term', 'exam_count','ptm_count', 'class_count', 'section_id', 'link_id']
            df['status'] = df['exam_count'].apply(lambda score: cons._SYMBOL_TICK if score > 0 else cons._SYMBOL_UNTICK )
            df['ptm'] = df.apply(lambda row: cons._SYMBOL_TICK if row["ptm_count"] == row["class_count"] else cons._SYMBOL_UNTICK , axis=1)
            df['term_combined'] = df.apply(lambda row: "%s.%s" %(row["term_id"], row["term"] ) , axis=1 )
            df['term_link'] = df.apply(util.get_url_term_dashboard, by='term', axis=1)
            df['class_link'] = df.apply(util.get_url_term_dashboard, by='section', axis=1)
            df.rename(columns={'term_link':'Term #', 'class_link':'Class' }, inplace=True)
            df_summary = df.set_index(['Term #', 'Class']).unstack()['status']
            df_ptm = df.set_index(['Term #', 'Class']).unstack()['ptm']

#            for (idx, row) in df.iterrows():
#                print(row.section, row.exam_count, row.ptm_count, row.class_count )
            sub_title = [ "Exam Completion", "PTM Completion" ]
            return render_template('main/dashboard_summary.html', tables=[df_summary.to_html(classes='data', escape = False), df_ptm.to_html(classes='data', escape = False) ],
                    sub_title= sub_title, rowcount=len (df_summary), title = title , view = 'exam')

    except Exception as e:
        flash('Error while fetching exam dashborad', 'error')
        print(e)
        return redirect('/')


@exam_blueprint.route('/search_exam', methods=['GET', 'POST'])
@login_required
@roles_required('teacher')
def search_exam():
    util.trace()
    search = SearchExamForm( request.form )
    if request.method == 'POST':
        return search_exam_results(search)

    title = 'Select Trimester Term'
    return render_template('main/search_exam.html', form=search, title = title )


@exam_blueprint.route('/search_exam_results')
@login_required
@roles_required('teacher')

def search_exam_results(search):
    util.trace()
    term = search.data['term']
    return exam_status(term)

@exam_blueprint.route('/exam_status/<int:term>')
@exam_blueprint.route('/exam_status/<int:term>/<int:section>')
@login_required
@roles_required('teacher')

def exam_status(term, section=None):
    util.trace()
    try:
        rows = []
        sections = db_util.get_teacher_sections( current_user.id )

        if not sections  :
            flash('No Class assigned yet!', 'success')
            return redirect('/')

        if section and len(sections) > section :
            current_section = [ sections[section] ]
        else :
            current_section =  [ sections[0] ]

        query = db.session.query( Enrollment.enrollment_id, Enrollment.section, Enrollment.academic_year, Student.student_name,
                    Exam.oral_score, Exam.written_score, Exam.exam_score, Exam.listening_eval, Exam.speaking_eval, Exam.reading_eval , Exam.writing_eval ,
                    Exam.exam_date, Exam.note, Exam.is_ptm_completed, Exam.ptm_completed_date, literal( term ).label("trimester_id") ) \
                .outerjoin( Exam, and_( Exam.enrollment_id == Enrollment.enrollment_id, Exam.trimester_id == term )) \
                .join( Student, Enrollment.student_id == Student.student_id ) \
                .filter( Enrollment.section.in_( current_section )) \
                .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"]) \
                .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED ))

        rows = query.order_by( Enrollment.section, Student.student_name ).all()
        if not rows:
            flash('No Student Assigned to your class!', 'success')
            return redirect('/')
        term_dict = {1:"First", 2:"Second", 3:"Final" }
##        dict(form.status.choices).get(form.status.data)

        count = len(rows)
        exam_date = None
        main_form = ExamMainForm()
        for exam in rows:
            exam_form = ExamForm()
            exam_form.enrollment_id = exam.enrollment_id
            exam_form.trimester_id = exam.trimester_id
            exam_form.section = exam.section
            exam_form.student_name = exam.student_name
            exam_form.exam_score =  exam_form.exam_score_previous = exam.exam_score
            exam_form.oral_score = exam_form.oral_score_previous = exam.oral_score
            exam_form.written_score = exam_form.written_score_previous = exam.written_score
            exam_form.listening_eval = exam_form.listening_eval_previous = exam.listening_eval
            exam_form.speaking_eval  = exam_form.speaking_eval_previous  = exam.speaking_eval
            exam_form.reading_eval   = exam_form.reading_eval_previous   = exam.reading_eval
            exam_form.writing_eval   = exam_form.writing_eval_previous   = exam.writing_eval
            exam_form.note = exam_form.note_previous = exam.note
            exam_form.is_ptm_completed   = exam_form.is_ptm_completed_previous   = exam.is_ptm_completed
            exam_form.ptm_completed_date = exam_form.ptm_completed_date_previous = exam.ptm_completed_date

            main_form.exam.append_entry(exam_form)
            if exam.exam_date and exam_date is None :
                exam_date = exam.exam_date  # .strftime('%Y-%m-%d')

        if exam_date :
            main_form.exam_date_previous = exam_date
#            main_form.exam_date.default  = exam_date
            main_form.exam_date.default  = exam_date.strftime('%Y-%m-%d')

#        for u in rows:
#            print( u._asdict() )

        title='%s Trimester Evaluation' %(term_dict.get(int(term)))
        section_dict = {}
        if len(sections) > 1 :
            section_dict = {k: v for k, v in enumerate(sections)}
            title = "%s - %s" %( title, current_section[0] )

        return render_template('main/exam_update.html', title=title, form=main_form, count=count, section_dict=section_dict, term=term )

    except Exception as e:
        flash('Error while searching Exam data', 'error')
        print(e)
        return redirect('/search_exam')

@exam_blueprint.route('/exam_update', methods=['POST'])
@login_required
@roles_required('teacher')

def exam_update():
    util.trace()
    try :
        on_commit = False

        data = request.form.to_dict()
        count = util.count( data.keys() )
        exam_list_update =  []
        exam_list_insert =  []

        exam_date = data.get("exam_date")
        previous_date = data.get("exam_date_previous")

        for row in range(count) :
            enrollment_id = data.get("exam-%s-enrollment_id" %row)
            trimester_id = data.get("exam-%s-trimester_id" %row)
            section = data.get("exam-%s-section" %row)
            oral_score = data.get("exam-%s-oral_score" %row , 0)
            written_score = data.get("exam-%s-written_score" %row, 0 )
            listening_eval = data.get("exam-%s-listening_eval" %row, 0 )
            speaking_eval = data.get("exam-%s-speaking_eval" %row, 0 )
            reading_eval = data.get("exam-%s-reading_eval" %row, 0 )
            writing_eval = data.get("exam-%s-writing_eval" %row, 0 )
            note = data.get("exam-%s-note" %row)
            is_ptm_completed = data.get("exam-%s-is_ptm_completed" %row, 0 )
            ptm_completed_date = data.get("exam-%s-ptm_completed_date" %row )

            previous_score = data.get("exam-%s-exam_score_previous" %row)
            previous_note = data.get("exam-%s-note_previous" %row)
            previous_listening_eval = data.get("exam-%s-listening_eval_previous" %row, 0 )
            previous_speaking_eval = data.get("exam-%s-listening_eval_previous" %row, 0 )
            previous_reading_eval = data.get("exam-%s-listening_eval_previous" %row, 0 )
            previous_writing_eval = data.get("exam-%s-listening_eval_previous" %row, 0 )
            previous_oral_score = data.get("exam-%s-oral_score_previous" %row)
            previous_written_score = data.get("exam-%s-written_score_previous" %row)
            previous_ptm_completed = data.get("exam-%s-is_ptm_completed_previous" %row, 0 )
            previous_ptm_completed_date = data.get("exam-%s-ptm_completed_data_previous" %row )

            oral_score = util.conv_to_float( oral_score )
            written_score = util.conv_to_float( written_score )
            exam_score =  oral_score + written_score

            if is_ptm_completed == 'y' or is_ptm_completed == 1 :
                is_ptm_completed = 1
            else :
                is_ptm_completed = 0

            if is_ptm_completed == 1 and not ptm_completed_date :
                ptm_completed_date = db_util.get_last_school_date()

            if ptm_completed_date and is_ptm_completed == 0 :
                is_ptm_completed = 1

            if oral_score != previous_oral_score or written_score != previous_written_score or note != previous_note or exam_date != previous_date or \
                listening_eval != previous_listening_eval or speaking_eval != previous_speaking_eval or reading_eval != previous_reading_eval or \
                writing_eval != previous_writing_eval or is_ptm_completed != previous_ptm_completed or ptm_completed_date != previous_ptm_completed_date :
                exam_data = { 'enrollment_id' : enrollment_id,
                                'trimester_id' : trimester_id,
                                'academic_year' : session["ACADEMIC_YEAR"],
                                'section' : section,
                                'oral_score' : oral_score,
                                'written_score' : written_score,
                                'exam_score' : exam_score,
                                'listening_eval' : listening_eval,
                                'speaking_eval' : speaking_eval,
                                'reading_eval' : reading_eval,
                                'writing_eval' : writing_eval,
                                'exam_date' : exam_date,
                                'note' : note ,
                                'is_ptm_completed' : is_ptm_completed,
                                'ptm_completed_date' : ptm_completed_date,
                                'last_updated_at' : datetime.now() ,
                                'last_updated_id' : current_user.id
                              }

                if previous_score :   ## Modifed
                    exam_list_update.append( exam_data )
                else :   ## New
                    if exam_score or note :
                        exam_list_insert.append( exam_data )

        if exam_list_update or exam_list_insert :
            ##TODO : Add logic for locking

            on_commit = True
            if exam_list_update :
                db.session.bulk_update_mappings(Exam, exam_list_update )
            if exam_list_insert :
                db.session.bulk_insert_mappings(Exam, exam_list_insert )
            db.session.commit()
            on_commit = False
            flash('Exam score info successfully updated for %d students' % (len(exam_list_update) + len(exam_list_insert) ) , 'success')
        else :
            flash('No score changes to update' , 'success')

        return redirect('/search_exam')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating exam scores', 'error')
        print(e)
        return redirect('/search_exam')


@exam_blueprint.route('/term_detail/<string:id>' )
@login_required
@roles_required(['teacher', 'parent', 'admin'])

def term_detail(id):
    util.trace()
    try:
        id_list = id.split('|')
        view = int(id_list[2])

        if view < 5 :
            enroll_id = int(id_list[0])
            academic_year = int(id_list[1])
        elif view == 5 :
            section = id_list[0]
        elif view == 6 :
            term_id = int(id_list[0])
        elif view not in [0, 1, 2, 3, 5, 6 ] :
            flash('Invalid Option', 'error')
            return redirect('/')

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
        elif view in (5, 6) :
             if not db_util.is_user_role( current_user.id, 'admin') :
                flash('Access Denied', 'error')
                return redirect('/')

        query = db.session.query(Exam.trimester_id, Exam.oral_score, Exam.written_score, Exam.exam_score, Exam.listening_eval, Exam.speaking_eval,
                Exam.reading_eval, Exam.writing_eval, Exam.exam_date, Exam.note, Exam.is_ptm_completed, Exam.ptm_completed_date,
                Enrollment.section.label("Section"), Student.student_name.label("Student Name") ) \
                .join(Enrollment, Student)

        if view not in (5, 6) :
            if enroll_id not in enroll_list and view < 5  :
                flash('Warning : URL is altered manually!!', 'error')
                print('*** URL alter attempt by %s ***' %current_user.id )
                return redirect('/')

            result_name = db.session.query(Student.student_name).join(Enrollment, Enrollment.student_id == Student.student_id) \
                                .filter(Enrollment.enrollment_id == enroll_id).one()
            student_name = result_name.student_name
            title = "%d - Trimester Evaluation Details for %s" %(academic_year, student_name)

            query = query.filter(Exam.enrollment_id == enroll_id ) \
                .order_by( Exam.trimester_id )

        elif view == 5 :
            query = query.filter(Enrollment.section == section).filter( Enrollment.academic_year == session["ACADEMIC_YEAR"]) \
                        .order_by( Student.student_name, Exam.trimester_id  )

            title = "Trimester Evaluation Details for class %s" %section

        elif view == 6 :
            query = query.filter(Exam.trimester_id == term_id).filter( Enrollment.academic_year == session["ACADEMIC_YEAR"]) \
                        .order_by( Enrollment.section, Student.student_name )

            title = "Trimester Evaluation Details for term %s" %term_id

        term_dict = db_util.get_ui_config( 'EXAM_TERM' )
        eval_dict = db_util.get_ui_config( 'EVALUATION_LEVEL' )
        df = pd.read_sql(query.statement,  db.engine.connect() )

        df['Term'] = df["trimester_id"].map(term_dict)
        df['Listening'] = df["listening_eval"].map(eval_dict)
        df['Speaking']  = df["speaking_eval"].map(eval_dict)
        df['Reading']   = df["reading_eval"].map(eval_dict)
        df['Writing']   = df["writing_eval"].map(eval_dict)
        df['Is PTM Completed?' ] = df["is_ptm_completed"].map({ False : 'No' , True : "Yes" })

        col_list = ['Term', 'exam_date', 'oral_score', 'written_score', 'exam_score', 'note', 'Listening', 'Speaking', \
                    'Reading', 'Writing',  'Is PTM Completed?', 'ptm_completed_date' ]
        if view > 4 :
            col_list = ['Section', 'Student Name' ] + col_list

        df = df[col_list].replace([np.nan, 0 ], ['', '' ] )

        df.rename(columns={'exam_date':'Exam Date', 'oral_score' : "Oral Exam", 'written_score' : "Written Exam", 'exam_score' : 'Total Score' ,\
                        'note' : "Teachers' Feedback", 'ptm_completed_date' : "PTM Completed Date" }, inplace=True)

        pd.set_option('display.max_colwidth', -1)
        return render_template('main/show_details.html', tables=[df.to_html(classes='data', index = False, escape = False)], \
                        titles=df.columns.values, rowcount=len(df), title = title, view=view, mode = 'show_term' )

    except Exception as e:
        flash('Error while fetching Trimester Evaluation Details', 'error')
        print(e)
        return redirect('/')
