from flask import Blueprint, flash, jsonify, redirect, request, render_template, session, url_for
from flask_user import login_required, roles_required, current_user
from datetime import datetime

import paypalrestsdk

from common import db_util, util, constant as cons, email_manager as email
from common.cache import Cache as cache
from common.mail import mail

from models.orm_models import db,  Enrollment, Payment, RateCard, Student, User, UIConfig
from views.forms import PaymentMainForm, PaymentForm
from views.tables import Results_MyPayment

payment_blueprint = Blueprint('payment', __name__ )

def payment_init() :
    paypalrestsdk.configure({
      "mode": cache.get_value("PAYPAL_MODE"),
      "client_id": cache.get_value("PAYPAL_CLIENT_ID") ,
      "client_secret": cache.get_value("PAYPAL_CLIENT_SECRET") })


@payment_blueprint.route('/payment/<string:id_str>' )
@login_required    # Use of @login_required decorator
@roles_required('admin')

def student_payment_view(id_str):
    util.trace()
    id_list = id_str.split('|')
    id = int(id_list[0])

    query = db.session.query(Student.student_name, Student.start_year, Enrollment.nilai, Enrollment.section, \
                UIConfig.category_value.label("enrollment_status"), Enrollment.payment_status, \
                Enrollment.due_amount, Enrollment.discount_amount, Enrollment.previous_balance, Enrollment.paid_amount, \
                Enrollment.check_no, Enrollment.enrollment_id) \
                .join(Enrollment, Enrollment.student_id == Student.student_id).filter(Student.parent_id == id ) \
                .join( UIConfig, UIConfig.category_key == Enrollment.enrollment_status )  \
                .filter( UIConfig.category == 'ENROLLMENT_STATUS' ) \
                .filter( Enrollment.enrollment_status != 3 ).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
    results = query.order_by(Enrollment.nilai, Enrollment.section, Student.student_name ).all()
    parentform = PaymentMainForm()

    rates =  RateCard.query.with_entities(RateCard.rate_type, RateCard.rate).filter(RateCard.academic_year == session["ACADEMIC_YEAR"]).all()
    rate_dict = {}
    for rate in rates :
        rate_dict.update( {rate.rate_type : rate.rate } )

    count = len(results)
    if count == 2 :
        discount = rate_dict.get("SIBLING_DISCOUNT_FOR_2", 0)
    elif count == 3 :
        discount = rate_dict.get("SIBLING_DISCOUNT_FOR_3", 0)
    else :
        discount = 0

    for student in results:
        studentform = PaymentForm()
        studentform.enrollment_id = student.enrollment_id
        studentform.student_name = student.student_name
        studentform.enrollment_status = student.enrollment_status
        studentform.payment_status = student.payment_status
        studentform.section = student.section
        studentform.start_year = student.start_year
        studentform.nilai = student.nilai
        studentform.paid_amount = student.paid_amount
        studentform.new_amount = 0
        studentform.discount_amount = student.discount_amount
        studentform.previous_balance = student.previous_balance
        studentform.check_no = ""
        if student.nilai == -1 :
            studentform.due = rate_dict["ENROLLMENT_ARUMBU"] - discount - student.discount_amount
        elif student.nilai == 11 :
            studentform.due = rate_dict["ENROLLMENT_ADULT_NEW"] - discount - student.discount_amount
        elif student.start_year == session["ACADEMIC_YEAR"] :
            studentform.due = rate_dict["ENROLLMENT_NEW"] - discount - student.discount_amount
        else :
            studentform.due = rate_dict["ENROLLMENT_EXISTING"] - discount - student.discount_amount

        parentform.students.append_entry(studentform)
    return render_template('main/student_payment.html', title='Main', form=parentform, count=len(results), mode="payment")

@payment_blueprint.route('/payment_update', methods=['POST'])
@login_required    # Use of @login_required decorator
@roles_required('admin')

def student_payment_update():
    util.trace()
    try :

        on_commit = False
        data = request.form.to_dict()
        count = util.count( data.keys() )
        enroll_list =  []
        enroll_mappings = []
        payment_mappings = []
        mail_data_all = []

        for row in range(count) :
            enrollment_id = data.get("students-%s-enrollment_id" %row)
            paid_amount = float(data.get("students-%s-paid_amount" %row, 0 ))
            new_amount = float(data.get("students-%s-new_amount" %row, 0))
            due_amount = float(data.get("students-%s-due" %row, 0))

            if new_amount == 0 :
                continue
            else :
                payment_status = 'Y' if new_amount + paid_amount >= due_amount else "P"
                paid_date = datetime.today()
                enrollment_status = cons._ENROLL_CONFIRMED

            enroll_list.append(enrollment_id)
            enroll_data = {'enrollment_id': enrollment_id ,
                            'paid_amount' : paid_amount + new_amount ,
                            'check_no' : data.get("students-%s-check_no" %row),
                            'payment_status' : payment_status ,
                            'paid_date' : paid_date,
                            'enrollment_status' : enrollment_status,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }

            payment_data = {'enrollment_id': enrollment_id ,
                            'paid_amount' : paid_amount + new_amount ,
                            'reference' : data.get("students-%s-check_no" %row),
                            'payment_mode' : "CHECK",
                            'paid_date' : paid_date,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }


            mail_data = {'student_name': data.get("students-%s-student_name" %row),
                            'paid_amount' : paid_amount + new_amount ,
                            'due_amount' : due_amount,
                            'balance' : due_amount - (paid_amount + new_amount) ,
                            'payment_mode' : "CHECK",
                            'check_no' : data.get("students-%s-check_no" %row),
                            'paid_date' : paid_date,
                            'payment_status' : payment_status ,
                            'enrollment_status' : 'CONFIRMED'
                        }

            enroll_mappings.append( enroll_data )
            payment_mappings.append( payment_data )
            mail_data_all.append( mail_data )
        if payment_mappings :
            on_commit = True
            db.session.bulk_update_mappings(Enrollment, enroll_mappings)
            db.session.bulk_insert_mappings(Payment, payment_mappings)
            db.session.commit()
            on_commit = False
#            print( payment_mappings )
            emails, parent_main, parent_second = db_util.get_email_for_enroll(enroll_list[0] )
            email.send_payment_confirmation(mail, mail_data_all, emails, parent_main, parent_second )
            flash('Payment info successfully updated', 'success')
        else:
            flash('No Payment info updated', 'success')
        return redirect('/search?mode=payment')
    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating payment info', 'error')
        print(e)
        return redirect('/search?mode=payment')

@payment_blueprint.route('/mypayment' )
@login_required
@roles_required('parent')

def mypayment():
    util.trace()
    try:
        rows = db_util.get_payment_info( current_user.id )

        if not rows:
            flash('No Enrollments Found!', 'success')
            return redirect('/')
        unconfirmed_count = db_util.enrollment_count(current_user.id, cons._NOT_ENROLLED )
#        print("unconfirmed_count : %s" %unconfirmed_count)
        balance = 0
        for row in rows :
            balance += row.balance

        table = Results_MyPayment(rows )
        table.border = True
        mode = cache.get_value("PAYPAL_MODE")
        env = 'production' if mode == 'live' else mode
        return render_template('main/payment.html', table=table, balance = balance, rowcount=len(rows), unconfirmed = unconfirmed_count, env = env )
    except Exception as e:
        flash('Error while fetching Payments', 'error')
        print(e)
        return redirect('/')


@payment_blueprint.route('/update_due' )
@login_required    # Use of @login_required decorator
@roles_required('admin')

def update_due():
    util.trace()
    return update_due_amount()

def update_due_amount(parent_id = None ):
    util.trace()
    if parent_id :
        users = User.query.filter( User.id == parent_id ).all()
    else :
        users = User.query.filter().all()

    rates =  RateCard.query.with_entities(RateCard.rate_type, RateCard.rate).filter(RateCard.academic_year == session["ACADEMIC_YEAR"]).all()
    rate_dict = {}
    for rate in rates :
        rate_dict.update( {rate.rate_type : rate.rate } )
#    print(rate_dict)
    enroll_data = []

#    print( "User Count : %s" %( len(users) ) )
    for user in users :
        if not user.is_active :
            continue
        query = db.session.query(Student.start_year, Enrollment.enrollment_id, Enrollment.nilai, Enrollment.due_amount, \
                Enrollment.discount_amount, Enrollment.previous_balance ) \
                .join(Enrollment, Enrollment.student_id == Student.student_id) \
                .filter(Student.parent_id == user.id ).filter(Enrollment.academic_year == session["ACADEMIC_YEAR"] )
        results = query.filter( Enrollment.enrollment_status != 3 ).all()

        count = len(results)
#        print( "Student Count : %s" %( count ) )
        if count == 0 :
            continue
        elif count == 2 :
            discount = rate_dict.get("SIBLING_DISCOUNT_FOR_2", 0)
        elif count == 3 :
            discount = rate_dict.get("SIBLING_DISCOUNT_FOR_3", 0)
        else :
            discount = 0

        for student in results:
            enrollment_id = student.enrollment_id
            start_year = student.start_year
            nilai = student.nilai
            due_amount = student.due_amount
            late_discount = student.discount_amount
            if nilai == -1 :
                due_new = rate_dict["ENROLLMENT_ARUMBU"] - discount - late_discount
            elif nilai == 11 :
                due_new = rate_dict["ENROLLMENT_ADULT_NEW"] - discount - late_discount
            elif start_year == session["ACADEMIC_YEAR"] :
                due_new = rate_dict["ENROLLMENT_NEW"] - discount - late_discount
            else :
                due_new = rate_dict["ENROLLMENT_EXISTING"] - discount - late_discount

            if due_amount != due_new :
                due_data = {'enrollment_id': enrollment_id,
                            'due_amount' : due_new,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }
                enroll_data.append(due_data)
#    print( "Total due updates %s" %len(enroll_data) )

    try :
        db.session.bulk_update_mappings(Enrollment, enroll_data)
        db.session.commit()
        if not parent_id :
            update_payment_status(session["ACADEMIC_YEAR"])
            flash('Due Amount successfully updated for %s students' %(len(enroll_data)) , 'success')
            return redirect('/')
    except Exception as e :
        db.session.rollback()
        flash('Error while updating Due Amount', 'error')
        print(e)
        return redirect('/')


def update_payment_status(academic_year)  :
    util.trace()
    sql_update_unpaid = """update enrollment set payment_status = 'N' where paid_amount = 0 and academic_year = %s """
    sql_update_partial = """update enrollment set payment_status = 'P' where paid_amount < due_amount + previous_balance and paid_amount > 0 and academic_year = %s """
    sql_update_paid = """update enrollment set payment_status = 'Y' where paid_amount = due_amount + previous_balance and paid_amount > 0 and academic_year = %s """
    sql_update_overpaid = """update enrollment set payment_status = 'O' where paid_amount > due_amount + previous_balance and paid_amount > 0 and academic_year = %s """

    try :
        conn = db.engine.connect()
        conn.execute( sql_update_paid , ( academic_year ))
        conn.execute( sql_update_unpaid, ( academic_year ))
        conn.execute( sql_update_partial, ( academic_year ))
        conn.execute( sql_update_overpaid, ( academic_year ))
        conn.close()
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        raise


@payment_blueprint.route('/confirm_payment', methods=['GET', 'POST'])
@login_required
@roles_required('parent')

def confirm_payment():
    util.trace()
    flash("Processed payments sucessfully" , 'success')
    return redirect('/mypayment')

def get_outstanding_payment_info():
    util.trace()
    try:
        rows = db_util.get_payment_info( current_user.id )
        item_list = []
        balance = 0
        count = 1
        for row in rows :
            if row.balance + row.previous_balance != 0 and row.academic_year == session["ACADEMIC_YEAR"]  :
                item_data = {'name': "Enrollment for Student # %d" %count ,
                            'sku' : "%d-%s" %(row.academic_year, str(row.enrollment_id).zfill(4)),
                            'price' : str(row.balance + row.previous_balance),
                            "currency": "USD",
                            "quantity": "1"
                            }

                item_list.append( item_data )
                balance += row.balance + row.previous_balance
                count += 1

        transactions =  [{
                "item_list": {
                    "items": item_list
                        },
                "amount": {
                    "total": str(balance),
                    "currency": "USD"},
                "description": "Enrollment fee for %s" %session["ACADEMIC_YEAR"] }]

        payment_mapping = { "intent": "sale",
                            "payer":
                                {
                                    "payment_method": "paypal"
                                },
                            "redirect_urls":
                                {
                                    "return_url": url_for("payment.confirm_payment", _external=True),
                                    "cancel_url": url_for("payment.mypayment", _external=True)
                                },
                            "transactions": transactions
                            }

#        print( payment_mapping )
        return payment_mapping

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        raise e

@login_required
@payment_blueprint.route('/paypal_payment', methods=['POST'])
def paypal_payment():
    util.trace()
    try :
        payment_mapping = get_outstanding_payment_info()
        payment = paypalrestsdk.Payment(payment_mapping)

        if payment.create():
            print('Payment success!')
#            print(request.form)
        else:
            print(payment.error)

        return jsonify({'paymentID' : payment.id})

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)


@login_required
@payment_blueprint.route('/execute', methods=['POST'])
def execute():
    util.trace()
#    success = False

    payment = paypalrestsdk.Payment.find(request.form['paymentID'])
    result = payment.execute({'payer_id' : request.form['payerID']})
    if result :
#        print('Execute success!')
#        print(request.form)
        print(payment)
        process_paypal_payment(payment )

#        print(result)
#        success = True
    else:
        print(payment.error)

#    return jsonify({'success' : success})
    return redirect('/confirm_payment')

def process_paypal_payment( payment ) :
    util.trace()
    try:
        on_commit = False
        payment_mappings, enroll_mappings, mail_mappings = get_paypal_payment_info( payment )
#        print( payment_mappings )
#        print( enroll_mappings )
#        print( mail_mappings )

        if payment_mappings :
            on_commit = True
            db.session.bulk_update_mappings( Enrollment, enroll_mappings )
            db.session.bulk_insert_mappings( Payment, payment_mappings )
            db.session.commit()
            on_commit = False
            emails, parent_main, parent_second = db_util.get_email_for_enroll( payment_mappings[0].get("enrollment_id") )
            email.send_payment_confirmation(mail, mail_mappings, emails, parent_main, parent_second  )
            print('Payment info successfully updated', 'success')
        else:
            print('No Payment info updated', 'success')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating payment info', 'error')
        print(e.message if hasattr(e, 'message') else e)
        raise e

def get_paypal_payment_info( payment ) :
    util.trace()
    try :
#        print( payment["id"] )
        payment_mappings = []
        enroll_mappings = []
        mail_mappings = []

        trans =  payment["transactions"]
        for tran in trans :
            for item in tran["item_list"]["items"] :
                enroll_id = item["sku"].split("-")[-1]
                paid_date = datetime.today()
                new_amount = float(item["price"])
                payment_status = 'Y'
                payment_data = { "enrollment_id" : enroll_id ,
                                 "paid_amount" : item["price"] ,
                                 "paid_date" : paid_date,
                                 "payment_mode" : "PAYPAL" ,
                                 "reference" : payment["id"] ,
                                 "note" : payment["cart"] ,
                                 "last_updated_at" : datetime.now(),
                                 "last_updated_id" : current_user.id
                                }
#                print( payment_data )
                student_name, _, due_amount, paid_amount, discount_amount, previous_balance = db_util.get_enroll_info ( enroll_id )

                enroll_data = {'enrollment_id': enroll_id ,
                                'paid_amount' : paid_amount + new_amount ,
                                'check_no' : payment["id"],
                                'payment_status' : payment_status ,
                                'paid_date' : paid_date,
                                'enrollment_status' : cons._ENROLL_CONFIRMED,
                                'last_updated_at' : datetime.now(),
                                'last_updated_id' : current_user.id
                                }

                mail_data = {'student_name': student_name,
                                'paid_amount' : new_amount ,
                                'due_amount' : due_amount + previous_balance ,
                                'balance' : (due_amount + previous_balance) - (paid_amount + new_amount) ,
                                'payment_mode' : "PAYPAL",
                                'check_no' : payment["id"],
                                'paid_date' : paid_date,
                                'payment_status' : payment_status ,
                                'enrollment_status' : 'CONFIRMED'
                            }
                payment_mappings.append( payment_data )
                enroll_mappings.append( enroll_data )
                mail_mappings.append( mail_data )

        return payment_mappings, enroll_mappings, mail_mappings

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        raise e