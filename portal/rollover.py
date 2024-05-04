from flask import Blueprint, flash, redirect, request, render_template, session
from datetime import datetime
import pandas as pd
from sqlalchemy import func

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons
from common.cache import Cache as cache

from models.orm_models import db, Enrollment, SchoolCalendar, SchoolYear, Student
from views.forms import AcademicYearForm, CalendarForm, CalendarMainForm, SchoolYearForm
from views.tables import Results_SchoolYear
from grade import summary_score
from book_order import create_book_order_template

rollover_blueprint = Blueprint('rollover', __name__ )

@rollover_blueprint.route('/calendar_view')
@login_required
@roles_required('admin')

def calendar_view():
    util.trace()
    try:
        rows = SchoolCalendar.query.filter(SchoolCalendar.academic_year == session["ACADEMIC_YEAR"]).all()
        if not rows:
            flash('No Calendar Setup for %d' %session["ACADEMIC_YEAR"], 'error')   ##Hard coded year
            return redirect('/')
        count = len(rows)
        mainform = CalendarMainForm()
        for calendar in rows:
            calendarform = CalendarForm()
            calendarform.school_date = calendar.school_date
            calendarform.is_session = calendar.is_session
            calendarform.attendance_required = calendar.attendance_required
            calendarform.note = calendar.note

            mainform.calendar.append_entry(calendarform)

        return render_template('main/calendar_update.html', title='School Calendar', form=mainform, count=count )

    except Exception as e:
        flash('Error while building Calendar', 'error')
        print(e)
        return redirect('/')

@rollover_blueprint.route('/calendar_update', methods=['POST'])
@login_required    # Use of @login_required decorator
@roles_required('admin')

def calendar_update():
    util.trace()
    try :
        on_commit = False
        data = request.form.to_dict()
        count = util.count( data.keys() )
#        print(data)
#        print( "data %s , count %s" %(len(data), count ) )
        days_list =  []

        for row in range(count) :
            is_session = data.get("calendar-%s-is_session" %row)
            attendance_required = data.get("calendar-%s-attendance_required" %row)
            note = data.get("calendar-%s-note" %row)

            calendar_data = {'school_date': data.get("calendar-%s-school_date" %row) ,
                            'is_session' : 1 if is_session else 0 ,
                            'attendance_required' : 1 if attendance_required else 0 ,
                            'note' : note ,
                            'last_updated_at' : datetime.now() ,
                            'last_updated_id' : current_user.id
                            }

            days_list.append( calendar_data )
        on_commit = True
        db.session.bulk_update_mappings(SchoolCalendar, days_list )
        db.session.commit()
        on_commit = False
#        print( days_list )
        if len(days_list) > 0 :
            flash('Calendar has successfully updated' , 'success')

        return redirect('/calendar_view')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating calendar', 'error')
        print(e)
        return redirect('/calendar_view')


@rollover_blueprint.route('/generate_calendar' )
@login_required
@roles_required('admin')

def generate_calendar(year = None):
    util.trace()

    try :
        add_year = cache.get_value("ROLLOVER")
        if not add_year :
            flash('Rollover option not enabled yet', 'error')
            return redirect('/')
        if not year:
            year = generate_calendar_needed()
        if year == 0 :
            flash('School Year Data does not exist' , 'error')
            return redirect('/')

        conn = db.engine.connect()
        year_data =  SchoolYear.query.filter(SchoolYear.academic_year == year).all()
        if year_data :
	        populate_calendar(year_data[0], conn, year)
	        create_book_order_template(year)
	        flash('Calendar generated for %d.' %year , 'success')
        else :
	        flash('School Year Data does not exist for %d.' %year , 'error')

        return redirect('/')

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        flash('Error while Generating Calendar for %d.' %year, 'error')
        return redirect('/')


@rollover_blueprint.route('/rollover' )
@login_required
@roles_required('admin')

def rollover():
    util.trace()
    try :
        add_year = cache.get_value("ROLLOVER")
        if not add_year :
            flash('Rollover option not enabled yet', 'error')
            return redirect('/')

        # year = rollover_needed()
        year = 2023
        if year == 0 :
            flash('School Year Data does not exist' , 'error')
            return redirect('/')

        on_commit = False
        year_data =  SchoolYear.query.filter(SchoolYear.academic_year == year).all()
        if not year_data :
            flash('School Year Data does not exist for %d.' %year , 'error')
            return redirect('/')

        df_score = rollover_evaluation()
        df_pass = df_score[(df_score.final_score >= cache.get_value("PASSING_SCORE")) | (df_score.nilai_id == -1) ]

#        print( "Promoting %s out of %s" %(len(df_pass), len(df_score) ) )

        pass_enroll = list(df_pass['enrollment_id'])
#        print(pass_enroll )

        rows_promoted = Enrollment.query.filter( Enrollment.enrollment_status == cons._ENROLL_PROMOTED).filter( Enrollment.enrollment_id.in_( pass_enroll )) \
            .filter( Enrollment.academic_year == (year -1 )).all()
        enroll_promoted = [ row.enrollment_id for row in rows_promoted ]
#        print( "Promoted already : %d" %len(enroll_promoted) )
        rows_enrolled = Enrollment.query.filter( Enrollment.academic_year == year ).all()
        student_enrolled = [ row.student_id for row in rows_enrolled ]
#        print( "Enrolled already : %d" %len(student_enrolled) )

        rows = Enrollment.query.filter( Enrollment.enrollment_id.in_( pass_enroll )).all()
#        print( "Eligible : %d" %len(rows) )

        promoted_list = []
        enroll_new_list = []
#        student_update_list = []

        for row in rows :
            if row.enrollment_id not in enroll_promoted :
                promote_data = {'enrollment_id': row.enrollment_id,
                            'enrollment_status' : cons._ENROLL_PROMOTED ,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }

                promoted_list.append( promote_data )

            if row.student_id not in student_enrolled :
                enroll_new_data = { 'student_id' : row.student_id ,
                            'academic_year' : year ,
                            'nilai' : row.nilai + 1 ,
                            'school_grade' : row.school_grade + 1,
                            'last_year_class' : row.section ,
                            'enrollment_status' : cons._NOT_ENROLLED ,
                            'active' : 1 ,
                            'note' : "Auto Enrolled %s" %(datetime.now()),
                            'previous_balance' : row.due_amount - row.paid_amount,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }
                enroll_new_list.append( enroll_new_data )


        on_commit = True
        if promoted_list :
            db.session.bulk_update_mappings(Enrollment, promoted_list )
        if enroll_new_list :
            db.session.bulk_insert_mappings(Enrollment, enroll_new_list )

        update_rollover_status( year )

        db.session.commit()
        on_commit = False
#        order_list =
#        db_util.create_book_order_template(year)

        message = '%d Eligble students, %d already Promoted, %d newly Promoted, %d already Enrolled and %d newly Enrolled' %(len(pass_enroll), len(enroll_promoted), len(promoted_list), len(student_enrolled), len(enroll_new_list))
        print( message )
        flash(message, 'success')

        return redirect('/')

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        flash('Error while Rollover for %d.' %year, 'error')
        if on_commit :
            db.session.rollback()

        return redirect('/')

@rollover_blueprint.route('/manual_rollover/<int:enroll_id>/<int:year>' )
@login_required
@roles_required('admin')

def manual_rollover(enroll_id, year):
    util.trace()
    try :
        on_commit = False
#        print( "enroll_id : %d, year : %d" %( enroll_id, year ))
        # enroll_previous = Enrollment.query.filter( Enrollment.enrollment_id == enroll_id).first()
        enroll_previous = Enrollment.query.filter( Enrollment.enrollment_id == enroll_id).filter( Enrollment.academic_year == (year -1 )).first()
        if not enroll_previous :
            flash("Enrollment info not found for %d" %enroll_id, 'success')
            return redirect('/')

        student_name, start_year, _, _, _, _ = db_util.get_enroll_info(enroll_id )
#        print( "Name : %s, year : %d, ID : %d " %( student_name, start_year, enroll_previous.student_id ))

        enrolled = Enrollment.query.filter( Enrollment.academic_year == year).filter(Enrollment.student_id == enroll_previous.student_id).first()

        if enrolled :
            flash("Arealdy enrolled for %s in %d" %(student_name, year), 'success')
            return redirect('/')

        enroll_new_data = { 'student_id' : enroll_previous.student_id ,
                            'academic_year' : year ,
                            'nilai' : enroll_previous.nilai + 1 ,
                            'school_grade' : (enroll_previous.school_grade + 1),
                            'last_year_class' : enroll_previous.nilai ,
                            'enrollment_status' : cons._NOT_ENROLLED ,
                            'active' : 1 ,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }
#        print(enroll_new_data)
        student_data = None

#        print( "Paid Amount : %s - %s - %s" %(type(enroll_previous.paid_amount), type(enroll_previous.academic_year), type(start_year )))
        if enroll_previous.paid_amount == 0.0 and enroll_previous.academic_year == start_year :

            student_data = [{'student_id' : enroll_previous.student_id,
                            'start_year' : year,
                            'last_updated_at' : datetime.now() ,
                            'last_updated_id' : current_user.id
                          }]
#            print( student_data )

        on_commit = True
        enrollment_new = Enrollment( **enroll_new_data )
        db.session.add( enrollment_new )
        if student_data :
            db.session.bulk_update_mappings(Student, student_data )
#            print( "Updating student Data" )

        db.session.commit()
        flash("%s is sucessfully enrolled for %d" %(student_name, year ), 'success')

        return redirect('/')

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        flash('Error while Rollovering for %d.' %enroll_id, 'error')
        if on_commit :
            db.session.rollback()

        return redirect('/')


@rollover_blueprint.route('/change_year', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def change_year():
    util.trace()
    try :
        form = AcademicYearForm(request.form  )
        if request.method == 'POST' :  ## and form.validate():
            if form.year.data :
                session["ACADEMIC_YEAR"] = form.year.data
#                print( 'Year : %s' %form.year.data )
                flash('Academic Year is changed to %d' %session["ACADEMIC_YEAR"] , 'success')
            return redirect('/')
        else :
            form.year.data = session["ACADEMIC_YEAR"]
        return render_template('main/change_year.html', form=form)
    except Exception as e:
        flash('Changing year failed..', 'error')
        print(e)
        return redirect('/')


def populate_calendar(year_data, conn, acedamic_year) :
    try :
        start_date = year_data.start_date
        end_date = year_data.end_date
        school_day = year_data.school_day
        school_dates = pd.date_range( start=start_date, end=end_date, freq='W-'+ school_day[:3]  )
        conn.execute( SchoolCalendar.__table__.insert(), [{"school_date": dt.date(), "academic_year" : acedamic_year, "last_updated_id" : current_user.id } for dt in school_dates ] )
##        SchoolCalendar.__table__.insert().execute([{"school_date": dt.date(), "academic_year" : acedamic_year, "last_updated_id" : 1 } for dt in school_dates ] )
    except Exception as e:
	    print(e.message if hasattr(e, 'message') else e)
	    raise

def rollover_evaluation():
    util.trace()
    return summary_score(view = 3)

def update_rollover_status( year ) :
    year_obj = SchoolYear.query.filter(SchoolYear.academic_year == year ).first()
    year_obj.rollover_status = 1
    #Commit should done in the calling function


def generate_calendar_needed():
    util.trace()
    max_calendar_year = db.session.query(func.max(SchoolCalendar.academic_year)).scalar()
    max_school_year = db.session.query(func.max(SchoolYear.academic_year)).scalar()
    if not max_calendar_year :
        max_calendar_year = 0
    if not max_school_year :
        max_school_year = 0
    return max_school_year if max_school_year > max_calendar_year else 0

def rollover_needed():
    util.trace()

    last_rollover_year = db.session.query(func.max(SchoolYear.academic_year)).filter(SchoolYear.rollover_status == 1 ).scalar()
    if not last_rollover_year :
        last_rollover_year = 0
    calendar_year = db.session.query(func.max(SchoolYear.academic_year)).filter(SchoolYear.rollover_status == 0 ).scalar()
    if not calendar_year :
        calendar_year = 0
    if last_rollover_year == 0 and calendar_year > session["ACADEMIC_YEAR"] :
        return 1
    return last_rollover_year + 1 if (calendar_year - last_rollover_year ) == 2 else 0

def new_year_needed():
    util.trace()
    last_rollover_year = db.session.query(func.max(SchoolYear.academic_year)).filter(SchoolYear.rollover_status == 1 ).scalar()
    if not last_rollover_year :
        last_rollover_year = 0
    calendar_year = db.session.query(func.max(SchoolYear.academic_year)).filter(SchoolYear.rollover_status == 0 ).scalar()
    if not calendar_year :
        calendar_year = 0
    if last_rollover_year == 0 and calendar_year == 0 :
        return session["ACADEMIC_YEAR"]

    if last_rollover_year == 0 and calendar_year > 0 :
        return calendar_year + 1

    return last_rollover_year + 1 if (calendar_year - last_rollover_year ) == 1 else 0


@rollover_blueprint.route('/school_year' , methods=['GET'])
@login_required
@roles_required('admin')

def school_year():
    util.trace()
    try:
        rows = SchoolYear.query.order_by(SchoolYear.academic_year).all()
        table = Results_SchoolYear(rows )
        table.border = True
        rollover_enabled = cache.get_value("ROLLOVER")
        if rollover_enabled :
            add_year =  new_year_needed() > 0
            generate_calendar = generate_calendar_needed() > 0
            rollover = rollover_needed() > 0
        else :
            add_year = generate_calendar = rollover = False

        return render_template('main/generic.html', table=table, rowcount = len(rows), mode='school_year', add_year = add_year, generate_calendar = generate_calendar, rollover = rollover )
    except Exception as e:
        flash('Error while searching for event', 'error')
        print(e)
        return redirect('/')

@rollover_blueprint.route('/school_year_edit', defaults={'id': None} ,  methods=['GET', 'POST'] )  ##
@rollover_blueprint.route('/school_year_edit/<int:id>' ,  methods=['GET', 'POST'] )

@login_required
@roles_required('admin')
def school_year_edit(id=None):
    util.trace()

    if id == 0:
        obj = SchoolYear()
        obj.academic_year = session["ACADEMIC_YEAR"] + 1
        obj.rollover_status = 0
    else :
        obj = SchoolYear.query.filter( SchoolYear.academic_year == id).first()

#    print("Section Count is %s - %s " %( len( section_obj) , section_obj[0].room ) )
    form = SchoolYearForm(request.form, obj=obj )
    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to class fields
        form.populate_obj(obj)
        obj.last_updated_at = datetime.now()
        obj.last_updated_id = current_user.id
        try:
            if id == 0:
                db.session.add(obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('School Year info update failed..', 'error')
            print(e)
            return redirect('/school_year')
        flash('School Year info successfully updated..', 'success')
        return redirect('/school_year')

    # Process GET or invalid POST
    return render_template('main/school_year_edit.html', form=form )
