from flask import Blueprint, flash, redirect, render_template, session
from datetime import date
from sqlalchemy import and_, func
from sqlalchemy.sql.expression import literal
import pandas as pd
import numpy as np

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons

from models.orm_models import db, Attendance, Enrollment, Exam, Homework, Nilai, Section, Student

grade_blueprint = Blueprint('grade', __name__ )

@grade_blueprint.route('/summary_score')
@grade_blueprint.route('/summary_score/<int:section>')
@login_required
@roles_required(['teacher', 'parent', 'admin'])

def summary_score(view = 1, enroll_list = None, to_csv = False, roll_over = False, current=True, section=None ):
    # view : 0 for parents, 1 for class, 2 for admin & 3 for rollover
    util.trace()
    try:
        previous = False
        inactive = False
        if view == 1 :
            sections = db_util.get_teacher_sections( current_user.id )
            if not sections  :
                flash('No Class assigned yet!', 'success')
                return redirect('/')

            if section and len(sections) > section :
                current_section = [ sections[section] ]
            else :
                current_section =  [ sections[0] ]

        elif view == 0 :
            query = db.session.query(Enrollment.enrollment_id ).join(Student, Student.student_id == Enrollment.student_id) \
                        .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
                        .filter( Student.parent_id == current_user.id ) \
                        .filter( Enrollment.enrollment_status != 3 )

            enroll_list = enroll_list_previous = [ row.enrollment_id for row in query.filter( Enrollment.academic_year < session["ACADEMIC_YEAR"]).all() ]
            enroll_list_current = [ row.enrollment_id for row in query.filter( Enrollment.academic_year == session["ACADEMIC_YEAR"]).all() ]
            if current :
                enroll_list = enroll_list_current
                if enroll_list_previous :
                    previous = True

            if not ( enroll_list_current + enroll_list_previous ) :
                flash('No Class assigned yet!', 'success')
                return redirect('/')

            if not enroll_list_current and enroll_list_previous :
                previous = True
                current = False
                inactive = True
                enroll_list = enroll_list_previous

        elif view == 2 and db_util.is_user_role( current_user.id, 'admin') :
            enroll_list = enroll_list
        elif view ==3 and db_util.is_user_role( current_user.id, 'admin') :

            query = db.session.query(Enrollment.enrollment_id ) \
                        .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                        .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] )

            enroll_list = [ row.enrollment_id for row in query.all() ]

            if not enroll_list  :
                flash('No Info Available!', 'success')

        else :
            flash('Not a valid option!', 'success')
            return redirect('/')

        subq_attend = db.session.query(func.least(func.ifnull(func.sum(Attendance.attendance_score), literal(0)), literal(25))).filter( Attendance.enrollment_id == Enrollment.enrollment_id)
        subq_hw = db.session.query(func.ifnull(func.sum(Homework.homework_score), literal(0))).filter( Homework.enrollment_id == Enrollment.enrollment_id)
        subq_hw_cw = subq_hw.filter( Homework.homework_type == 3 )
        subq_hw_quiz = subq_hw.filter( Homework.homework_type == 2 )
        subq_hw_audio = subq_hw.filter( Homework.homework_type == 1 )
        subq_hw_written = subq_hw.filter( Homework.homework_type == 0 )
        subq_exam = db.session.query(Exam.exam_score).filter( Exam.enrollment_id == Enrollment.enrollment_id)
        subq_exam_1 = subq_exam.filter( Exam.trimester_id == 1 )
        subq_exam_2 = subq_exam.filter( Exam.trimester_id == 2 )
        subq_exam_3 = subq_exam.filter( Exam.trimester_id == 3 )

        query_score = db.session.query(Enrollment.enrollment_id, Enrollment.academic_year, Enrollment.section.label('section'), \
                        Student.student_name, Student.student_name_tamil, Enrollment.nilai.label('nilai_id'), Nilai.name.label('Nilai'),  \
                        subq_attend.label('attendance'), subq_hw_cw.label('hw_cw'), subq_hw_quiz.label('hw_quiz'), subq_hw_audio.label('hw_audio'), subq_hw_written.label('hw_written'), \
                        subq_exam_1.label('exam_1'), subq_exam_2.label('exam_2'), subq_exam_3.label('exam_3'), \
                        func.concat(Enrollment.enrollment_id, '|', Enrollment.academic_year, '|', literal(view), '|', func.unix_timestamp(date.today())).label("link_id")  ) \
                .join( Student, Student.student_id == Enrollment.student_id ) \
                .join( Nilai, Nilai.nilai_id == Enrollment.nilai )

        section_dict = {}
        if view != 0 :
            query_score = query_score.filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        if view == 1 :
            query_score = query_score.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                .filter( Enrollment.section.in_( current_section ))
            title =  "Evaluation Summary"

            if len(sections) > 1 :
                section_dict = {k: v for k, v in enumerate(sections)}
                title = title + " - %s" %current_section[0]

        else :
            query_score = query_score.filter( Enrollment.enrollment_id.in_( enroll_list ))
            title =  "Evaluations" if view == 0 else "Score Report"

        query_score = query_score.order_by(Enrollment.academic_year, Enrollment.section, Student.student_name )

#        results = query_score.all()
#        for u in results :
#            print( u._asdict() )

        df = pd.read_sql(query_score.statement,  db.engine.connect() )
        df['final_score'] = df.apply(util.calc_final_score, axis=1)
        ata_df = pd.read_sql(query_score.statement,  db.engine.connect() )
        ata_df['final_score'] = df.apply(util.calc_final_score, axis=1)

        if view == 3 :
            return df[['enrollment_id', 'nilai_id', 'final_score' ]]

        # df['final_grade'] = df.apply(util.calc_final_grade, axis=1)
        # ata_df['final_grade'] = df.apply(util.calc_final_grade, axis=1)
        if not to_csv :
            df.fillna('', inplace = True)
            df['attend_link'] = df.apply(util.get_url_attend, axis=1)
            df['hw_cw_link'] = df.apply(util.get_url_hw, type=3 ,axis=1)
            df['hw_quiz_link'] = df.apply(util.get_url_hw, type=2 ,axis=1)
            df['hw_audio_link'] = df.apply(util.get_url_hw, type=1 ,axis=1)
            df['hw_written_link'] = df.apply(util.get_url_hw, axis=1)
            df['term_1_link'] = df.apply(util.get_url_term, term=1, axis=1)
            df['term_2_link'] = df.apply(util.get_url_term, term=2, axis=1)
            df['term_3_link'] = df.apply(util.get_url_term, term=3, axis=1)

            ata_df.fillna('', inplace = True)
            ata_df['attend_link'] = df.apply(util.get_url_attend, axis=1)
            ata_df['hw_written_link'] = df.apply(util.get_url_hw, axis=1)
            ata_df['term_1_link'] = df.apply(util.get_url_term, term=1, axis=1)
            ata_df['term_2_link'] = df.apply(util.get_url_term, term=2, axis=1)
            ata_df['term_3_link'] = df.apply(util.get_url_term, term=3, axis=1)

            col_list = ['section', 'student_name','student_name_tamil', 'term_1_link', 'term_2_link', 'term_3_link', \
                        'attend_link', 'hw_cw_link', 'hw_quiz_link', 'hw_audio_link', 'hw_written_link', 'final_score'] # , 'final_grade']
            ata_col_list = ['section', 'student_name','student_name_tamil', 'term_1_link', 'term_2_link', 'term_3_link', \
                        'attend_link', 'hw_written_link', 'final_score'] # , 'final_grade']


            if view == 0:
                col_list = ['academic_year'] + col_list
                ata_col_list = ['academic_year'] + ata_col_list

            df = df[col_list].replace([np.nan, 0 ], ['', '' ] )
            ata_df = df[ata_col_list].replace([np.nan, 0 ], ['', '' ] )

            df.rename(columns={'academic_year':'Academic Year', 'section' : "Class", 'student_name' : "Student Name", 'student_name_tamil' : 'மாணவர் பெயர்'      ,\
                            'term_1_link' : "First Trimester", 'term_2_link' : "Second Trimester", 'term_3_link' : "Final Trimester", \
                                'attend_link': 'Attendance', 'hw_cw_link': 'Classwork', 'hw_quiz_link': 'Quiz', 'hw_audio_link': 'Project', 'hw_written_link': 'Homework',  \
                                'final_score' : 'Final Score' }, inplace=True) # , 'final_grade' : 'Final Grade'
            ata_df.rename(columns={'academic_year':'Academic Year', 'section' : "Class", 'student_name' : "Student Name", 'student_name_tamil' : 'மாணவர் பெயர்'      ,\
                            'term_1_link' : "First Trimester", 'term_2_link' : "Second Trimester", 'term_3_link' : "Final Trimester", \
                                'attend_link': 'Attendance', 'hw_written_link': 'Homework',  \
                                'final_score' : 'Final Score' }, inplace=True) # , 'final_grade' : 'Final Grade'

            # pd.set_option('display.max_colwidth', -1) # deprecated setting -1
            return render_template('main/summary_score.html', \
                                    tables=[df.to_html(classes='data', index = False, escape = False)], \
                                    ata_tables=[ata_df.to_html(classes='data', index = False, escape = False)], \
                                    titles=df.columns.values, rowcount=len(df), title = title, view=view, current=current , \
                                    previous = previous, inactive = inactive, section_dict=section_dict )

        elif view == 2:

            df['fname'] = df.apply(lambda row: util.get_name_part(row['student_name'], 1), axis=1 )
            df['mname'] = df.apply(lambda row: util.get_name_part(row['student_name'], 2), axis=1 )
            df['lname'] = df.apply(lambda row: util.get_name_part(row['student_name'], 3), axis=1 )

            df['fname_tamil'] = df.apply(lambda row: util.get_name_part(row['student_name_tamil'], 1), axis=1 )
            df['mname_tamil'] = df.apply(lambda row: util.get_name_part(row['student_name_tamil'], 2), axis=1 )
            df['lname_tamil'] = df.apply(lambda row: util.get_name_part(row['student_name_tamil'], 3), axis=1 )
            df['hw'] = df.apply(lambda row: (row['hw_audio'] + row['hw_written'])/2, axis=1 )
#            df['hw'] = df.apply(lambda row: 0 if not row['hw_audio'] or not row['hw_written'] else (row['hw_audio'] + row['hw_written'])/2, axis=1 )

            df = df [['section', 'student_name', 'fname', 'mname', 'lname', 'student_name_tamil', 'fname_tamil', 'mname_tamil', 'lname_tamil',\
                    'Nilai', 'exam_1', 'exam_2', 'exam_3', 'attendance', 'hw_cw', 'hw', 'hw_quiz', 'hw_audio', \
                    'hw_written', 'final_score', 'final_grade']].replace([np.nan, 0 ], ['', '' ] )

            df.rename(columns={'section' : "Class", 'student_name' : "Student Name", 'student_name_tamil' : 'மாணவர் பெயர்'      ,\
                            'exam_1' : "First Trimester", 'exam_2' : "Second Trimester", 'exam_3' : "Final Trimester", \
                                'attend': 'Attendance', 'hw_cw': 'Classwork', 'hw_quiz': 'Quiz', 'hw_audio': 'Project', 'hw_written': 'Homework',  \
                                'final_score' : 'Final Score', 'final_grade' : 'Final Grade' }, inplace=True)

            return util.download( df, 'program_list.csv' )

    except Exception as e:
        flash('Error while fetching summary score', 'error')
        print(e)
        return redirect('/')


@grade_blueprint.route('/myevaluation/<mode>' )
@grade_blueprint.route('/myevaluation')
@login_required

def myevaluation(mode=0):
    util.trace()
    current = (mode == 0)
    return summary_score(0, current = current) # For Parents
