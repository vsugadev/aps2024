from flask import Blueprint, flash, redirect, request, render_template, session
from datetime import datetime
from time import sleep
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.mail import mail
from common.cache import Cache as cache

from models.orm_models import db, Enrollment, Nilai, Notification, Section, Student, UIConfig, User
from views.forms import EmailListForm, SearchForm
from views.tables import  Results_Payment, Results_StudentClass

comm_blueprint = Blueprint('communication', __name__ )


@comm_blueprint.route('/email_list' )
@login_required
@roles_required('admin')

def email_list():
    util.trace()
    try:
        query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, User.email, User.email2 ).join(User, Enrollment)
        query = query.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED ))
        query = query.filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        results = query.all()
        if not results :
            flash('No results found!', 'success')
            return redirect('/')

        primary_email_list = list(set([r.email for r in results]))
        secondary_email_list = list(set([r.email2 for r in results if r.email2]))

        sql = """select email, email2 from user where is_active = 1 and id not in (select parent_id from student where parent_id is not null)"""
        conn = db.engine.connect()
        rows = conn.execute( sql )
        count = rows.rowcount
        print("%s Users without enrollments" %count )
        for row in rows :
            primary_email_list.append( row[0] )
            if row[1] :
                secondary_email_list.append( row[1] )

        primary_emails =  ', '.join( email for email in primary_email_list )
        secondary_emails =  ', '.join( email2 for email2 in secondary_email_list )

        form = EmailListForm(request.form)

        form.primary_emails.data  = primary_emails
        form.secondary_emails.data  = secondary_emails
        return render_template('main/email_list.html', form=form, primary_count = len(primary_email_list) , secondary_count = len(secondary_email_list) )
    except Exception as e:
        flash('Error while getting emails List', 'error')
        print(e)
        return redirect('/')



@comm_blueprint.route('/notify', methods=['GET', 'POST'])
@login_required    # Use of @login_required decorator
@roles_required('admin')
def notify():
    util.trace()
    mode = request.args.get('mode')
    search = SearchForm(request.form, mode = mode)
    if request.method == 'POST':
        return notify_results(search)

    title = 'Lookup for Email Notification'
    return render_template('main/search_mail.html', form=search, title = title, mode = mode )

@comm_blueprint.route('/notify_results')
@login_required    # Use of @login_required decorator
@roles_required('admin')

def notify_results(search):
    util.trace()
    try:
        rows = []
        notification_type = search.data['notification_type']
        name_string = search.data['name']
        section = search.data['section']
        nilai = search.data['nilai']
        paid = search.data['paid']
        enrollment = search.data['enrollment']
        new = search.data['new']
        inactive = search.data['inactive']
        to_csv = search.data['to_csv']
        to_email = search.data['to_email']
        mode = search.data['mode']
        mode = "email"

        if notification_type == "ClassAssignment11" :

            U1 = aliased(User)
            U2 = aliased(User)
            query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year,
                             User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id, Enrollment.last_year_class,
                             Enrollment.school_grade, Enrollment.nilai, Enrollment.section, Enrollment.enrollment_status, Enrollment.payment_status, Enrollment.paid_amount,
                             Enrollment.discount_amount, Enrollment.previous_balance, Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Nilai.name.label("nilai_name"),
                             Section.room,Section.teacher1_id, U1.father_name.label("teacher1"), U2.father_name.label("teacher2") ) \
                    .join(User, Enrollment) \
                    .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
                    .join(Nilai, Nilai.nilai_id == Enrollment.nilai) \
                    .outerjoin(U1, U1.id == Section.teacher1_id  ) \
                    .outerjoin(U2, U2.id == Section.teacher2_id  )

        elif notification_type in [ "UnPaid", "EnrollmentReminder", "ClassAssignment" ] :

            if notification_type == "ClassAssignment" :
                U1 = aliased(User)
                U2 = aliased(User)
                query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year,
                                 User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id, Enrollment.last_year_class,
                                 Enrollment.school_grade, Enrollment.nilai, Enrollment.section, UIConfig.category_value.label("enrollment_status"), Enrollment.payment_status, Enrollment.paid_amount,
                                 Enrollment.discount_amount, Enrollment.previous_balance, Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Nilai.name.label("nilai_name"),
                                 Section.room,Section.teacher1_id, U1.father_name.label("teacher1"), U2.father_name.label("teacher2") ) \
                        .join(User, Enrollment) \
                        .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
                        .join(Nilai, Nilai.nilai_id == Enrollment.nilai) \
                        .outerjoin(U1, U1.id == Section.teacher1_id  ) \
                        .outerjoin(U2, U2.id == Section.teacher2_id  ) \
                        .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                        .filter( UIConfig.category == 'ENROLLMENT_STATUS' )


            else :
                query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year,
                             User.id, User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id,
                             Enrollment.last_year_class, Enrollment.school_grade, Enrollment.nilai, Enrollment.section, UIConfig.category_value.label("enrollment_status"),
                             Enrollment.payment_status, Enrollment.due_amount, Enrollment.discount_amount, Enrollment.previous_balance, Enrollment.paid_amount,
                             Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Nilai.name.label("nilai_name") ) \
                             .join(User, Enrollment).join(Nilai, Enrollment.nilai == Nilai.nilai_id ) \
                            .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                            .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \

            if notification_type ==  "UnPaid" :
                query = query.filter( (Enrollment.payment_status == 'N' ) | (Enrollment.payment_status == 'P' ) ) \
                            .filter( Enrollment.enrollment_status == cons._ENROLLED_ONLINE )
            elif notification_type ==  "EnrollmentReminder" :
                query = query.filter( Enrollment.enrollment_status == cons._NOT_ENROLLED )
            else :
                query = query.filter( Enrollment.enrollment_status.in_((cons._ENROLLED_ONLINE, cons._ENROLL_CONFIRMED )) ) \
                             .filter( func.length(Enrollment.section) > 0 )
        else :
            flash('Notification Type %s is not implemented!' %notification_type, 'success')
            return redirect('/notify?mode=%s' %mode)


        query = query.filter((Student.student_name.like("%" + name_string + "%") |
                         User.father_name.like("%" + name_string + "%")| User.mother_name.like("%" + name_string + "%")| User.email.like("%" + name_string + "%") | User.email2.like("%" + name_string + "%") ))
        if nilai:
            query = query.filter( Enrollment.nilai == nilai )
        if section:
            query = query.filter( Enrollment.section == section )
        if paid :
            query = query.filter( Enrollment.payment_status == paid )
        if enrollment :
            query = query.filter( Enrollment.enrollment_status == enrollment )
        if not inactive :
            query = query.filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED ))
        if new :
            query = query.filter( Student.start_year == session["ACADEMIC_YEAR"] )

        query = query.filter(Enrollment.academic_year == session["ACADEMIC_YEAR"])
        rows = query.order_by(User.id, Enrollment.nilai, Enrollment.section, Student.student_name ).all()
        if not rows:
            flash('No results found!', 'success')
            return redirect('/notify?mode=%s' %mode)

        if to_csv:
            return util.download( rows, '%s_report.csv' %mode , query)

        elif to_email:
#            print( "rows : %d" %len(rows) )
            count = add_notification(notification_type, rows )
            flash('%d notifications scheduled for %s' %(count, notification_type ), 'success')

            return redirect('/notify')
        else :
            if notification_type == "ClassAssignment" :
                table = Results_StudentClass(rows )
            else : ## if notification_type == "UnPaid" :
                table = Results_Payment(rows )

            table.border = True
            return render_template('main/generic.html', table=table, mode=mode, rowcount=len(rows)  )

    except Exception as e:
        print(e)
        flash('Error during sending notifications', 'error')
        return redirect('/search')
        return redirect('/notify?mode=%s' %mode)


def build_notification_data(notification_type, parent_id, enrollment_id=None ):
    util.trace()
    parent_data = { "parent_id" : parent_id,
                    "enrollment_id" : enrollment_id,
                    "notification_type" : notification_type,
                    "created_at" : datetime.now() ,
                    "created_id" : current_user.id ,
                    "status" : 0,
                    "retry_count" : 0,
                    "last_updated_at" : datetime.now() ,
                    "last_updated_id" : current_user.id
                    }

    return parent_data

def add_notification(notification_type, rows):
    util.trace()
    notify_mapping = []
    if notification_type == 'ClassAssignment' :
        for row in rows :
            parent_data = build_notification_data(notification_type, row.parent_id, row.enrollment_id )
            notify_mapping.append( parent_data )

    else :
        parent_list_all = list(set([user.id for user in rows]))

        for parent_id in parent_list_all :
            last_notification = get_last_notification(parent_id, notification_type)
            if last_notification and abs(datetime.now() - last_notification).days <=  int(db_util.get_config("NOTIFICATION_THRESHOLD" )) :
                print( "Last notification %s sent with in %d days for %d" %(notification_type, abs(datetime.now() - last_notification).days, parent_id ))
                continue

            parent_data = build_notification_data(notification_type, parent_id  )
            notify_mapping.append( parent_data )

#    print( notify_mapping )
    try:
        if notify_mapping :
            db.session.bulk_insert_mappings(Notification, notify_mapping )
            db.session.commit()
        return len(notify_mapping)
    except Exception as e:
        db.session.rollback()
        flash('Error while adding notification data', 'error')
        print(e)

def get_last_notification(parent_id, notification_type):
    util.trace()
    return db.session.query(func.max(Notification.last_updated_at)) \
            .filter(Notification.parent_id == parent_id) \
            .filter(Notification.notification_type == notification_type).scalar()


@comm_blueprint.route('/trigger_notification')
@login_required
@roles_required('admin')

def trigger_notification() :
    util.trace()
    notification_data = get_notification_data()
    loop_count = 0
    success = True
    sleep_sec = int(db_util.get_config( "NOTIFICATION_SLEEP_SEC" ))
    max_retry = int(db_util.get_config( "NOTIFICATION_MAX_RETRY" ))
    while notification_data and len(notification_data) > 0 :
        loop_count += 1
        print("Retry Count %d " %loop_count )
        if loop_count > max_retry :
            flash("Pending %d notifications, reached loop count and exiting, try later...." %len(notification_data), "success" )
            print("Pending %d notifications, reached loop count, exiting...." %len(notification_data) )
            success = False
            break

        result = email.send_notification(db, Notification, mail, notification_data )
        if result == 0 :
            sleep( sleep_sec )

        notification_data = get_notification_data()
    if success :
        flash('Notifications sent successfully...', 'success')
    return redirect('/')


def get_notification_data() :
    util.trace()
    try :
        reminder_data = get_notification_data_reminder()
        class_data = get_notification_data_class()
#        print("class_data")
        return reminder_data + class_data
    except Exception as e:
        flash('Error while fetching class notification data', 'error')
        print(e)
        return redirect('/')


def get_notification_data_class() :
    util.trace()
    try :

        U1 = aliased(User)
        U2 = aliased(User)

        query = db.session.query(Student.student_id, Student.parent_id, Student.student_name, Student.student_name_tamil, Student.sex, Student.start_year,
                         Notification.id, Notification.notification_type,
                         User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, Enrollment.enrollment_id, Enrollment.last_year_class,
                         Enrollment.school_grade, Enrollment.nilai, Enrollment.section, UIConfig.category_value.label("enrollment_status"), Enrollment.payment_status, Enrollment.paid_amount,
                         Enrollment.discount_amount, Enrollment.previous_balance, Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Nilai.name.label("nilai_name"),
                         Section.room,Section.teacher1_id, U1.father_name.label("teacher1"), U2.father_name.label("teacher2") ) \
                .join(User, Enrollment) \
                .join(Section, and_(Section.section == Enrollment.section, Section.academic_year == Enrollment.academic_year )) \
                .join(Nilai, Nilai.nilai_id == Enrollment.nilai) \
                .join(Notification, Enrollment.enrollment_id == Notification.enrollment_id ) \
                .filter(Notification.status != 2 ) \
                .outerjoin(U1, U1.id == Section.teacher1_id  ) \
                .outerjoin(U2, U2.id == Section.teacher2_id  ) \
                .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
                .filter( Notification.notification_type == 'ClassAssignment' )

        results = query.order_by(Notification.notification_type, Enrollment.nilai, Enrollment.section, Student.student_name ).all()
#        print(" Results :%s " %len(results) )
        pay_dict = {'Y':'Paid', 'N':'Unpaid', 'P':'Partially Paid', 'O':'Over Paid'   }

        mail_mapping = []
        for row in results:
            recipients = [row.email, row.email2 ] if row.email2 else [row.email ]

            enroll = {  "student_name" : row.student_name, "start_year" : row.start_year, "book_status" : "Yes" if row.book_status == 'Y' else "No",
                        "enrollment_status" : row.enrollment_status,  "nilai_name" : row.nilai_name, "section" : row.section, "room" : row.room,
                        "teacher1" : row.teacher1 or "TBD", "teacher2" : row.teacher2 or "TBD", "payment_status" : pay_dict.get(row.payment_status)  }
            enroll_data = { "notification_id" : row.id,
                            "notification_type" : row.notification_type,
                            "parent_primary" :  row.father_name or "Parents",
                            "parent_secondary" : row.mother_name ,
                            "recipients" : recipients if cache.get_value("PROD_MODE") else "",
                            "enroll" : enroll }

            mail_mapping.append( enroll_data )
        return mail_mapping
    except Exception as e:
        flash('Error while fetching class notification data', 'error')
        print(e)
        raise e

def get_notification_data_reminder() :
    util.trace()
    try :
        query = db.session.query(Student.parent_id, Student.student_name, Student.start_year, Notification.id, Notification.notification_type,
                 User.father_name, User.mother_name, User.email, User.email2, UIConfig.category_value.label("enrollment_status"),
                 Enrollment.payment_status, Enrollment.due_amount, Enrollment.paid_amount,
                 Enrollment.paid_date, Enrollment.check_no, Enrollment.book_status, Enrollment.nilai, Nilai.name.label("nilai_name") ) \
                .join(User, Enrollment).join( Nilai, Enrollment.nilai == Nilai.nilai_id )\
                .join(Notification, User.id == Notification.parent_id ) \
                .filter(Notification.status != 2 ) \
                .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                .filter(Enrollment.academic_year == session["ACADEMIC_YEAR"]) \
                .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
                .filter( Notification.notification_type != 'ClassAssignment' )


        results = query.order_by(Notification.notification_type, Student.parent_id, Enrollment.nilai, Enrollment.section, Student.student_name ).all()
#        print(" Results :%s " %len(results) )
        mail_mapping = []
        parents=[]
        parent_id = -1
        notify_type = ''
        for row in results:
            if row.parent_id == parent_id and row.notification_type == notify_type:
                parents.append( row )
            else :
                if len(parents) > 0 :
                    recipients = [parents[0].email, parents[0].email2 ] if parents[0].email2 else [parents[0].email ]

                    enroll = [{ "notification_type" : enroll.notification_type,  "student_name" : enroll.student_name, "start_year" : enroll.start_year,
                                "enrollment_status" : enroll.enrollment_status,  "nilai_name" : enroll.nilai_name, "due_amount" : enroll.due_amount,
                                "paid_amount" : enroll.paid_amount  } for enroll in parents ]
                    enroll_data = { "notification_id" : parents[0].id,
                                    "notification_type" : parents[0].notification_type,
                                    "parent_primary" :  parents[0].father_name or "Parents",
                                    "parent_secondary" : parents[0].mother_name ,
                                    "recipients" : recipients if cache.get_value("PROD_MODE") else "",
                                    "enroll" : enroll }

                    mail_mapping.append( enroll_data )
                parents = [row]
                parent_id = row.parent_id
                notify_type = row.notification_type
        if len(parents) > 0 :
            recipients = [parents[0].email, parents[0].email2 ] if parents[0].email2 else [parents[0].email ]
            enroll = [{"student_name" : enroll.student_name, "start_year" : enroll.start_year, "enrollment_status" : enroll.enrollment_status,
                        "nilai_name" : enroll.nilai_name , "due_amount" : enroll.due_amount, "paid_amount" : enroll.paid_amount} for enroll in parents ]
            enroll_data = { "notification_id" : parents[0].id,
                            "notification_type" : parents[0].notification_type,
                            "parent_primary" :  parents[0].father_name or "Parents",
                            "parent_secondary" : parents[0].mother_name ,
                            "recipients" : recipients if cache.get_value("PROD_MODE") else "",
                            "enroll" : enroll }

            mail_mapping.append( enroll_data )

#        print(len(mail_mapping) )
        return mail_mapping
    except Exception as e:
        flash('Error while fetching notification data', 'error')
        print(e)
        raise e


