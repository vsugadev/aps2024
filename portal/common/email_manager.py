
from threading import Thread
from flask_mail import Message
from flask import current_app as app
from flask import render_template
from datetime import datetime
from flask_user import current_user
from common import util
from common.cache import Cache as cache

#def send_async_email_(app, msg):
#    with app.app_context():
#        mail.send(msg)

def send_async_email(mail, msg):
    util.trace()
    with app.app_context():
        mail.send(msg)

def send_email(mail, subject, recipients, html_body):
    util.trace()
    print("Print Recipients Email Address :",recipients)
    with app.app_context():
        sender = (app.config['MAIL_SENDER_NAME'], app.config['MAIL_DEFAULT_SENDER'] )
        reply_to = app.config['MAIL_DEFAULT_SENDER']
        if not app.config['USER_PROD_MODE'] :
            print("Non-Prod Mode, email will be sending out to test recipients")
            recipients = app.config['TEST_RECIPIENTS']

    msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to)
#    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
    # Thread(target=send_async_email, args=(mail, msg)).start()

def send_email_with_cc(mail, subject, recipients, cc_email, html_body):
    util.trace()
    with app.app_context():
        sender = (app.config['MAIL_SENDER_NAME'], app.config['MAIL_DEFAULT_SENDER'] )
        reply_to = app.config['MAIL_DEFAULT_SENDER']
        if not app.config['USER_PROD_MODE'] :
            print("Non-Prod Mode, email will be sending out to test recipients")
            recipients = app.config['TEST_RECIPIENTS']

    msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to, cc = cc_email)
#    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
    # Thread(target=send_async_email, args=(mail, msg)).start()

def get_sender_info() :
    util.trace()
    with app.app_context():
        sender = (app.config['MAIL_SENDER_NAME'], app.config['MAIL_DEFAULT_SENDER'] )
        reply_to = app.config['MAIL_DEFAULT_SENDER']
        if app.config['USER_PROD_MODE'] :
            is_prod = True
            recipients = []
        else:
            print("Non-Prod Mode, email will be sending out to test recipients")
            recipients = app.config['TEST_RECIPIENTS']
            is_prod = False

    return sender, reply_to, is_prod, recipients

def send_payment_confirmation(mail, users, emails,  parent_main, parent_second  ) :
    util.trace()
    year_label = cache.get_value("ACADEMIC_YEAR_LABEL")
    subject = "Payment Confirmation (%s)" %year_label
#    print("Sending payment confirmation to "+ ', '.join(emails))
    html_body=render_template('email/payment_confirmation.html', users=users, parent_main=parent_main, parent_second = parent_second, academic_year_label = year_label )
#    print(html_body)
    send_email(mail,
               subject,
               recipients= emails,
               html_body=html_body )

def send_event_consent_confirmation(mail, event, emails ) :
    util.trace()
    subject = "Virtual Event Signup Confirmation (%s)" %cache.get_value("ACADEMIC_YEAR_LABEL")
#    print("Sending event confirmation to "+ ', '.join(emails))
    html_body=render_template('email/event_consent.html', event=event  )
#    print(html_body)
    send_email(mail,
               subject,
               recipients= emails,
               html_body=html_body )

def send_enroll_confirmation(mail, enrolls, emails, parent1, parent2, is_new ) :
    util.trace()
    year_label = cache.get_value("ACADEMIC_YEAR_LABEL")
    subject = "Enrollment Acknowledgement (%s)" %year_label
#    print("Sending enroll confirmation to %s & %s ..." %(parent1, parent2))

    school_name = cache.get_value("SCHOOL_NAME")
    html_body=render_template('email/enroll_confirmation.html', enrolls=enrolls, parent_primary=parent1,
                            parent_secondary=parent2, is_new = is_new, school_name = school_name, academic_year_label = year_label )
#    print(html_body)
# adding admin DL in recipients.
    emails = str(emails + ";admin@avvaiyarpadasalai.org")
    send_email(mail,
               subject,
               recipients= emails,
               html_body=html_body )

def send_class_confirmation(mail, users) :
    util.trace()
    sender, reply_to, is_prod, recipients = get_sender_info()
    with mail.connect() as conn:
        for user in users:
            if is_prod :
                recipients = [user.email, user.email2 ] if user.email2 else [user.email ]

            subject = "Class Update for %s " %user.student_name
#            print("Sending Class confirmation for %s" %user.student_name )
            html_body=render_template('email/class_confirmation.html', user=user  )
        #    print(html_body)
            msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to)
            msg.html = html_body
            conn.send(msg)

def send_unpaid_reminder(mail, users) :
    util.trace()
    sender, reply_to, is_prod, recipients = get_sender_info()
    with mail.connect() as conn:
        parents=[]
        parent_id = -1
        for user in users:
            if user.id == parent_id :
                parents.append( user )
            else :
                if len(parents) > 0 :
                    if is_prod :
                        recipients = [parents[0].email, parents[0].email2 ] if parents[0].email2 else [parents[0].email ]
                    unpaid_reminder(conn, parents, sender, reply_to, recipients )
                parents = [user]
                parent_id = user.id
        if len(parents) > 0 :
            unpaid_reminder(conn, parents, sender, reply_to, recipients )  ## For the last parent

def unpaid_reminder(conn, parents, sender, reply_to, recipients ) :
    util.trace()
    year_label = cache.get_value("ACADEMIC_YEAR_LABEL")
    subject = "Payment Reminder for %s" %year_label
#    print("Sending Payment Reminder for %s - %s" %(parents[0].id, ', '.join( p.student_name for p in parents )))
    html_body=render_template('email/payment_reminder.html', users=parents , academic_year_label = year_label )
    msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to)
    msg.html = html_body
    conn.send(msg)


def send_notification(db, Notification, mail, notification_data ) :
    util.trace()
    template_dict= { "UnPaid" : "email/payment_reminder.html" ,
                     "EnrollmentReminder" : "email/enrollment_reminder.html",
                     "ClassAssignment" : "email/class_confirmation.html"
                    }
    try :
        sender, reply_to, is_prod, recipients = get_sender_info()
        year_label = cache.get_value("ACADEMIC_YEAR_LABEL")
        with mail.connect() as conn:
            for data in notification_data :
#                print("Sending notification")
#                print(data)
#                print("Sending notification for %d" %data['notification_id']  )
                mail_recipients = recipients or data['recipients']
                notification_type = data["notification_type"]
                mail_template = template_dict[notification_type ]
                if notification_type == 'ClassAssignment' :
                    subject = "Class Details for %s " %data["enroll"].get("student_name")
                else :
                    subject = "%s Reminder for %s" %( "Payment " if notification_type == "UnPaid" else "Enrollment" , year_label )
                html_body=render_template(mail_template , users= data["enroll"], parent_primary = data["parent_primary"], parent_secondary = data["parent_secondary"], academic_year_label = year_label )
                msg = Message(subject, sender=sender, recipients=mail_recipients, reply_to = reply_to)
                msg.html = html_body
                conn.send(msg)
#                print(subject)
#                print( html_body)
                result = update_notification_status( db, Notification, data['notification_id'], data["notification_type"]  )
                if result == 1 :
                    print("Notification status successfully updated for %d" %data['notification_id'] )
                else :
                    print("Failed while updating status for %d" %data['notification_id'] )
        return 1
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        print('Error while sending notification email')
        return 0


def update_notification_status( db, Notification, notification_id, notification_type ) :
    util.trace()
    try :
#        print("Updating status for %d" %notification_id  )
        notify_obj = Notification.query.filter(Notification.id == notification_id ).first()
        notify_obj.status = 2
        notify_obj.last_updated_at = datetime.now()
        notify_obj.last_updated_id = current_user.id
        db.session.commit()
        return 1
    except Exception as e:
        db.session.rollback()
        print(e.message if hasattr(e, 'message') else e)
        print('Error while sending notification email')
        raise e


def send_class_progress(mail, from_email, to_email, cc_email, section, school_date, class_date, teachers, tracking_row ) :
    util.trace()
    try :
        sender, reply_to, is_prod, recipients = get_sender_info()
        reply_to = from_email
        sender = ("Mazhalai" if section == "MA" else "Nilai %s" %section , from_email)
        with mail.connect() as conn:
            recipients = recipients or to_email
#            print("recipients : %s " %recipients )
#            print( "to_email : %s " %to_email )
#            print( "cc_email : %s " %cc_email )
#            print( sender )
            cc = cc_email if is_prod else None
            subject = "%s Class Update for the week of %s" %(section, school_date )
#            print("Sending %s ..." %(subject) )
            html_body=render_template('email/class_progress.html', teachers = teachers, tracking = tracking_row, class_date = class_date, section = section )
        #    print(html_body)
            msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to, cc = cc)
            msg.html = html_body
            conn.send(msg)

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        print('Error while sending class updates')
        raise e

def send_service_request_created(mail, subject, from_email, to_email, cc_email, service_id, created_for, type, description, response=None) :
    util.trace()
    try :
        html_body = render_template('email/service_request.html', service_for=created_for, service_type = type, service_description = description, response = response )
        # subject = "Service Request[%d] Created" %(service_id )
        # send_email(mail,
        #       subject,
        #       recipients= to_email,
        #       html_body=html_body )
        send_email_with_cc(mail, subject, recipients= to_email, cc_email=cc_email, html_body=html_body)

        # debug below. not working
        # reply_to = from_email
        # with mail.connect() as conn:
        #    cc= cc_email
        #    html_body = render_template('email/service_request.html', service_type = type, service_description = description )
        #    subject = "Service Request Created: #(%d)" %(service_id )
        #    msg = Message(subject, sender=from_email, recipients=to_email, reply_to = reply_to, cc = cc)
        #    msg.html = html_body
        #    conn.send(msg)

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        print('Error while sending service request created email')
        # raise e

def send_annualday_registration(mail, from_email, to_email, cc_email, registration_id, student_email, events, comments) :
    util.trace()
    try :
        html_body = render_template('email/service_request_annualday.html', student_email = student_email, events = events, comments = comments )
        subject = "Annual Day 2022 Registration[#AnnualDay2022-%d] completed successfully." %(registration_id )
        send_email(mail,
               subject,
               recipients= to_email,
               html_body=html_body )
        # send_email_with_cc(mail,
        #       subject,
        #       recipients= to_email,
        #       cc_email = cc_email,
        #       html_body=html_body )
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        print('Error while sending annual day registration email')
        # raise e

def send_login_info(mail, to_email, user_email) :
    util.trace()
    try :
        events = ['']
        comments = ['']
        html_body = render_template('email/service_request_annualday.html', student_email = user_email, events = events, comments = comments )
        subject = "User %s logged in successfully." %(user_email )
        send_email(mail,
               subject,
               recipients= to_email,
               html_body=html_body )
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        print('Error while sending login info email')

