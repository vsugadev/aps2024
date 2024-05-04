from threading import Thread

from flask import Blueprint, flash, redirect, request, render_template, session, current_app
from datetime import date, datetime
from sqlalchemy import and_, func, case, desc

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.mail import mail

from models.orm_models import db, ServiceRequests, ServiceRequestAnnualDay, ServiceRequestAnnualDay_Uploads, Feedback
from views.tables import Results_ServiceRequests, Results_ServiceRequests_Admin, Results_ServiceRequestAnnualDay
from views.tables import Results_ServiceRequestAnnualDay_Uploads, Results_Feedback
from views.forms import ServiceRequestNewForm, ServiceRequestAnnualDayForm, ServiceRequestAdminForm, ServiceRequestUpdateForm, ServiceRequestAnnualDaySignupForm, ServiceRequestFeedbackForm
from flask_paginate import Pagination, get_page_parameter, get_page_args

from werkzeug.utils import secure_filename
import os

service_request_blueprint = Blueprint('service_request', __name__ )

@login_required
@roles_required('admin')
def get_annualday2022_registrations(page, reqs, offset, per_page):
    offset = ((page-1) * per_page)
    return reqs[offset: offset + per_page]

@login_required
@roles_required('admin')
def get_service_requests(page, reqs, offset, per_page):
    offset = ((page-1) * per_page)
    return reqs[offset: offset + per_page]

@service_request_blueprint.route('/service_request_admin_page/<int:view>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
# view = 0, Open View = 1 Closed Issues
def admin_page(view=0):
    util.trace()
    form = ServiceRequestAdminForm(request.form, obj=current_user)

    # service request(s) - open
    query = db.session.query( ServiceRequests.service_id, ServiceRequests.created_by, ServiceRequests.created_for, ServiceRequests.service_type, \
                                ServiceRequests.service_description, ServiceRequests.created_at, \
                                ServiceRequests.status).filter(ServiceRequests.status==view)
    query = query.order_by( desc(ServiceRequests.service_id), ServiceRequests.created_at )
    rows = query.all()

    # Process valid POST
    if request.method == 'POST':
        # and form.validate():
        to_csv = request.form.get("to_csv_service")
        try:
            if to_csv == 'y':
                timenow = date.today().strftime('%Y%m%d')
                filename = 'Service_Requests_%s.csv' %(timenow)
                flash('downloading file %s' %(filename), 'success')
                return util.download_requests( rows, filename, query)
        except Exception as e:
                flash('Error downloading file %s' %(filename), 'error')
                print(e)
                return redirect('/')

    # Set the pagination configuration
    ROWS_PER_PAGE = 10
    search = False
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    pagination = Pagination(page=page, search=search, per_page=ROWS_PER_PAGE, total=len(rows), record_name='service request(s)')

    requests = get_service_requests(page=page, reqs=rows, offset=0, per_page=ROWS_PER_PAGE)
    return render_template('main/service_request_summary_admin.html', form=form, view = view, pagination=pagination, requests=requests, rowcount=len(rows))

@service_request_blueprint.route('/annualday2022_admin_page', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def annualday2022_admin_page():
    util.trace()
    form = ServiceRequestAdminForm(request.form, obj=current_user)
    try:
        # annual day 2022 registration(s)
        # annualday_query = db.session.query( ServiceRequestAnnualDay).distinct()
        annualday_query = db.session.query( ServiceRequestAnnualDay.registration_id, ServiceRequestAnnualDay.email, \
                                            ServiceRequestAnnualDay.student_email, ServiceRequestAnnualDay.events, \
                                            ServiceRequestAnnualDay.created_at, ServiceRequestAnnualDay.comments).distinct()
        annualday_query = annualday_query.order_by( desc(ServiceRequestAnnualDay.registration_id), ServiceRequestAnnualDay.created_at )
        annualday_rows = annualday_query.all()

        # filter(ServiceRequestAnnualDay.events.in_([ "AD04-THAMIZHIL-URAIYADU-TEACHERS-ONLY" ]))
        ad07_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD07-"))
        ad07_rows = ad07_query.all()
        ad07_count = len(ad07_rows)

        ad06_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD06-"))
        ad06_rows = ad06_query.all()
        ad06_count = len(ad06_rows)

        ad05_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD05-"))
        ad05_rows = ad05_query.all()
        ad05_count = len(ad05_rows)

        ad04_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD04-"))
        ad04_rows = ad04_query.all()
        ad04_count = len(ad04_rows)

        ad03_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD03-"))
        ad03_rows = ad03_query.all()
        ad03_count = len(ad03_rows)

        ad02_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD02-"))
        ad02_rows = ad02_query.all()
        ad02_count = len(ad02_rows)

        ad01_query = db.session.query(ServiceRequestAnnualDay.registration_id).filter(ServiceRequestAnnualDay.events.contains("AD01-"))
        ad01_rows = ad01_query.all()
        ad01_count = len(ad01_rows)
        # flash(ad07_count, 'success')


        # Process valid POST
        if request.method == 'POST':
            # and form.validate():
            to_csv = request.form.get("to_csv")
            to_csv_service = request.form.get("to_csv_service")
            try:
                if to_csv == 'y':
                    timenow = date.today().strftime('%Y%m%d')
                    filename = 'AnnualDay2022_Registrations_%s.csv' %(timenow)
                    flash('downloading file %s' %(filename), 'success')
                    return util.download_registrations( annualday_rows, filename, annualday_query)
            except Exception as e:
                    flash('Error downloading file %s' %(filename), 'error')
                    print(e)
                    return redirect('/')

        # annualday_table = Results_ServiceRequestAnnualDay(annualday_rows )
        # annualday_table.border = True
        ROWS_PER_PAGE = 10
        search = False
        annualday_page, annualday_per_page, annualday_offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        annualday_pagination = Pagination(page=annualday_page, search=search, per_page=ROWS_PER_PAGE, total=len(annualday_rows), record_name='annual day 2022 registrations(s)')

        registrations = get_annualday2022_registrations(page=annualday_page, reqs=annualday_rows, offset=0, per_page=ROWS_PER_PAGE)

        return render_template('main/annualday2022_admin_view.html', form=form, annualday_pagination=annualday_pagination, \
                                            registrations=registrations, annualday_rowcount=len(annualday_rows), \
                                            ad01_count=ad01_count, ad02_count=ad02_count, ad03_count=ad03_count, ad04_count=ad04_count, \
                                            ad05_count=ad05_count, ad06_count=ad06_count, ad07_count=ad07_count)

    except Exception as e:
        # flash('Error while fetching AnnualDay 2022 registration(s) list', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')

@service_request_blueprint.route('/service_request_summary_page/<int:view>', methods=['GET', 'POST'])
@login_required
def summary_page(view=0):
    util.trace()
    try:
        # annual day 2022
        annualday_query = db.session.query( ServiceRequestAnnualDay).distinct() \
                .filter( ServiceRequestAnnualDay.user_id == current_user.id )
        annualday_rows = annualday_query.all()
        annualday_table = Results_ServiceRequestAnnualDay(annualday_rows )
        annualday_table.border = True

        # service requests
        query = db.session.query( ServiceRequests).distinct() \
                    .filter( ServiceRequests.user_id == current_user.id )

        rows = query.all()
        table = Results_ServiceRequests(rows )
        table.border = True

        if view == 1:
            return render_template('main/my_requests.html', table=table, rowcount=len(rows))
        else:
            return render_template('main/service_request_summary.html', table=table, rowcount=len(rows), annualday_table = annualday_table, annualday_rowcount=len(annualday_rows))

    except Exception as e:
        flash('Error while fetching Service Request(s) Summary Page List', 'error')
        # flash(str(e), 'error')
        print(e)
        return redirect('/')



# @service_request_blueprint.route('/service_request_update', methods=['GET', 'POST'])
# @login_required
# @roles_required('admin')
# @service_request_blueprint.route('/service_request_update', methods=['GET', 'POST'])
# @service_request_blueprint.route('/service_request_update/<int:id>/<string:type>/<string:description>/<string:created_by>', methods=['GET', 'POST'])
@service_request_blueprint.route('/service_request_update/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
# def update_page(type, id, description, created_by ):
def update_page(id):
    util.trace()

    myservice = db.session.query( ServiceRequests).distinct().filter(ServiceRequests.service_id == id ).first()
    # rows = query.all()
    # table = Results_ServiceRequests(rows )

    ServiceRequests_obj = ServiceRequests()
    # Process GET or invalid POST
    if request.method == 'POST':
        close = request.form.get("close")
        subject = None

        if close == 'y':
            myservice.closed = 1
            myservice.open = 1
            myservice.status = 1
            subject = "Service Request[SR-%d] - Closed" %(id )
        else: # update
            myservice.closed = 0
            myservice.open = 0
            if myservice.service_type == "Enrollment:2023-24":
                myservice.status = 2
            else:
                myservice.status = 0
            subject = "Service Request[SR-%d] - Updated" %(id )

        myservice.response = request.form.get("response")
        myservice.last_updated_at = datetime.now()
        myservice.last_updated_id = current_user.id
        # add to database
        # db.session.add(ServiceRequests_obj)
        db.session.commit()
        # send notification email
        notify_service_request(subject, myservice.created_by, myservice.created_for, myservice.service_id, myservice.service_type,  myservice.service_description, myservice.response)
        flash('%s' %(subject), 'success')

        #return redirect('main/service_request_summary_admin.html')
    else:
        ServiceRequests_obj.service_id = myservice.service_id
        ServiceRequests_obj.created_by = myservice.created_by
        ServiceRequests_obj.created_for = myservice.created_for
        ServiceRequests_obj.service_type = myservice.service_type
        ServiceRequests_obj.service_description = myservice.service_description
        if myservice.response != None:
            ServiceRequests_obj.response = myservice.response

    form = ServiceRequestUpdateForm(request.form, obj=ServiceRequests_obj)
    form.created_by.render_kw = {'readonly': True}
    form.created_for.render_kw = {'readonly': True}
    form.service_id.render_kw = {'readonly': True}
    form.service_type.render_kw = {'readonly': True}
    form.service_description.render_kw = {'readonly': True}

    return render_template('main/service_request_update.html', form = form)

@service_request_blueprint.route('/service_request_create', methods=['GET', 'POST'])
@login_required
def create_page():
    util.trace()

    form = ServiceRequestNewForm(request.form, obj=current_user)

    service_type = None
    service_description = None
    # Process valid POST
    if request.method == 'POST' and form.validate():
        try:
            ServiceRequests_obj = ServiceRequests()
            ServiceRequests_obj.user_id = current_user.id
            requestor_email = request.form.get("email")
            ServiceRequests_obj.created_by = requestor_email
            requesting_for = request.form.get("created_for")
            ServiceRequests_obj.created_for = requesting_for
            service_type = request.form.get("service_type")
            ServiceRequests_obj.service_type = service_type
            service_description = request.form.get("service_description")
            ServiceRequests_obj.service_description = service_description
            ServiceRequests_obj.created_at = datetime.now()
            ServiceRequests_obj.last_updated_at = datetime.now()
            ServiceRequests_obj.last_updated_id = current_user.id
            ServiceRequests_obj.open = 0
            ServiceRequests_obj.closed = 0
            if service_type == "Enrollment:2023-24":
                ServiceRequests_obj.status = 2
            else:
                ServiceRequests_obj.status = 0

            db.session.add( ServiceRequests_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Service Request Submission Failed.', 'error')
            print(e)
            return redirect('/')

        service_id = db_util.get_service_request_id(current_user.id)
        subject = "Service Request[SR-%d] - Created" %(service_id )
        notify_service_request(subject, requestor_email, requesting_for, service_id, service_type,  service_description)
        flash('Service Request submitted Successfully.', 'success')

    # Process GET or invalid POST
    return render_template('main/service_request_create.html', form=form)

@login_required
def notify_service_request( subject, requestor_email, requesting_for, service_id, service_type,  service_description, response=None) :
    util.trace()
    try:
        # send_service_request_created(mail, from_email, to_email, cc_email, section, service_id, type, description) :
        from_email = ['apsportal100@gmail.com']
        # to_email = ['thiruvalarabdul_aps515@avvaiyarpadasalai.org']
        to_email = [requestor_email]
        cc_email = ['admin@avvaiyarpadasalai.org']
        email.send_service_request_created(mail, subject, from_email, to_email, cc_email, service_id, requesting_for, service_type, service_description, response)
    except Exception as e:
        flash('Error while publishing service request email', 'error')
        print(e)
        raise e

@service_request_blueprint.route('/service_request_annualday_signup', methods=['GET', 'POST'])
@login_required
def annualday_signup_page() :
    util.trace()
    form = ServiceRequestAnnualDaySignupForm(request.form, obj=current_user)
    # Process GET or invalid POST

    return render_template('main/service_request_annualday_signup.html', form=form)


@service_request_blueprint.route('/service_request_pongal', methods=['GET', 'POST'])
@login_required
def pongal_page() :
    util.trace()
    form = ServiceRequestAnnualDayForm(request.form, obj=current_user)
    return render_template('main/service_request_pongal.html', form=form)


@service_request_blueprint.route('/service_request_annualday', methods=['GET', 'POST'])
@login_required
def annualday_page() :
    util.trace()
    form = ServiceRequestAnnualDayForm(request.form, obj=current_user)

    if request.method == 'POST' and form.validate():
        try:
            Annualday_obj = ServiceRequestAnnualDay()
            Annualday_obj.user_id = current_user.id
            Annualday_obj.created_at = datetime.now()
            Annualday_obj.last_updated_at = datetime.now()
            Annualday_obj.last_updated_id = current_user.id
            Annualday_obj.comments = request.form.get("comments")
            Annualday_obj.email = request.form.get("email")
            Annualday_obj.student_email = request.form.get("student_email")
            Annualday_obj.events =  util.list_to_str( request.form.getlist("events"))
            # Annualday_obj.events =  request.form.getlist("events")

            db.session.add( Annualday_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Annual Day 2022 Registration Failed.', 'error')
            print(e)
            return redirect('/')

        registration_id = db_util.get_annualday_registration_id(current_user.id)
        notify_annualday_registration(Annualday_obj.email, registration_id, Annualday_obj.student_email, Annualday_obj.events, Annualday_obj.comments)
        flash('Annual Day 2022 registration submitted Successfully.', 'success')

    # Process GET or invalid POST
    return render_template('main/service_request_annualday.html', form=form)

@login_required
def notify_annualday_registration( requester_email, registration_id, student_email, events, comments) :
    util.trace()
    try:
        from_email = ['apsportal100@gmail.com']
        to_email = [requester_email, student_email]
        # to_email = ['thiruvalarabdul_aps515@avvaiyarpadasalai.org']
        cc_email = ['admin@avvaiyarpadasalai.org']
        email.send_annualday_registration(mail, from_email, to_email, cc_email, registration_id, student_email, events, comments)
    except Exception as e:
        flash('Error while publishing annual day 2022 registration email', 'error')
        print(e)
        raise e

@service_request_blueprint.route('/service_request_annualday_rules', methods=['GET', 'POST'])
@login_required
def annualday_rules_page() :
    # Process GET or invalid POST
    return render_template('main/service_request_annualday_rules.html')

@login_required
def file_upload(file) :
    util.trace()
    path = os.path.join(current_app.instance_path, 'uploads', secure_filename(file.filename))
    file.save(path)

@service_request_blueprint.route('/service_request_annualday_upload_video', methods=['GET', 'POST'])
@login_required
def annualday_upload_video_page() :
    # annual day 2022 - Uploads
    query = db.session.query( ServiceRequestAnnualDay_Uploads).distinct() \
            .filter( ServiceRequestAnnualDay_Uploads.user_id == current_user.id )
    rows = query.all()

    # Process GET or invalid POST
    if request.method == "POST":
        flash('please wait while uploading the file... ', 'success')
        file = request.files['uploaded_file']
        filename = secure_filename(file.filename)
        if filename == '':
            flash('No selected file', 'error')
        else: # if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
                flash('The File extension is not supported. Supported formats are MP4 and MOV', 'error')
            else:
                # flash('File upload(s) are restricted now. It will be available soon!', 'success')
                # comment start
                # store files in database
                try:
                    #t=Thread(target=file_upload, args=(f))
                    #t.start()
                    #t.join()
                    path = os.path.join(current_app.instance_path, 'uploads', secure_filename(file.filename))
                    file.save(path)

                    upload = ServiceRequestAnnualDay_Uploads()
                    upload.filename = filename
                    upload.data_size = os.path.getsize(path)
                    upload.user_id = current_user.id
                    upload.created_at = datetime.now()
                    upload.last_updated_at = datetime.now()
                    upload.last_updated_id = current_user.id

                    db.session.add( upload)
                    db.session.commit()

                    flash('File: %s uploaded successfully' %(path), 'success')

                    '''
                    upload = ServiceRequestAnnualDay_Uploads()
                    upload.filename = filename
                    # data = file.read()
                    # upload.data = file.read()
                    upload.data_size = os.path.getsize(name)
                    # upload.data_size = 0
                    # len(data)
                    # upload.data_size = len(data)
                    upload.user_id = current_user.id
                    upload.created_at = datetime.now()
                    upload.last_updated_at = datetime.now()
                    upload.last_updated_id = current_user.id

                    db.session.add( upload)
                    db.session.commit()

                    # store files in pythonanywhere
                    # dest_dir = os.path.expanduser('~')
                    # dest_path = os.path.join(dest_dir, filename)
                    # file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    # file.save(dest_path)
                    # file.save(secure_filename(f.filename))
                    '''
                except Exception as e:
                    flash('Error while uploading the file %s' %(filename), 'error')
                    print(e)
                    raise e
                # comment end
    return render_template('main/service_request_annualday_upload_video.html', rows=rows, rowcount=len(rows))


@login_required
@roles_required('admin')
def admin_page_old():
    util.trace()
    form = ServiceRequestAdminForm(request.form, obj=current_user)
    try:
        # annual day 2022 registration(s)
        # annualday_query = db.session.query( ServiceRequestAnnualDay).distinct()
        annualday_query = db.session.query( ServiceRequestAnnualDay.registration_id, ServiceRequestAnnualDay.email, \
                                            ServiceRequestAnnualDay.student_email, ServiceRequestAnnualDay.events, \
                                            ServiceRequestAnnualDay.created_at, ServiceRequestAnnualDay.comments).distinct()
        annualday_rows = annualday_query.all()
        # annualday_table = Results_ServiceRequestAnnualDay(annualday_rows )
        # annualday_table.border = True
        ROWS_PER_PAGE = 10
        search = False
        annualday_page, annualday_per_page, annualday_offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        annualday_pagination = Pagination(page=annualday_page, search=search, per_page=ROWS_PER_PAGE, total=len(annualday_rows), record_name='annual day 2022 registrations(s)')

        registrations = get_annualday2022_registrations(page=annualday_page, reqs=annualday_rows, offset=0, per_page=ROWS_PER_PAGE)

        # service request(s)
        query = db.session.query( ServiceRequests.service_id, ServiceRequests.created_by, ServiceRequests.created_for, ServiceRequests.service_type, \
                                    ServiceRequests.service_description, ServiceRequests.created_at, \
                                    ServiceRequests.open, ServiceRequests.closed).distinct()
        rows = query.all()
        # Set the pagination configuration
        search = False
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        pagination = Pagination(page=page, search=search, per_page=ROWS_PER_PAGE, total=len(rows), record_name='service request(s)')

        requests = get_service_requests(page=page, reqs=rows, offset=0, per_page=ROWS_PER_PAGE)

        # table = Results_ServiceRequests_Admin(rows )
        # table.border = True
        # return render_template('main/service_request_admin_view.html', pagination=pagination, requests=rows, table=table, rowcount=len(rows), annualday_table = annualday_table, annualday_rowcount=len(annualday_rows))

        # Process valid POST
        if request.method == 'POST':
            # and form.validate():
            to_csv = request.form.get("to_csv")
            to_csv_service = request.form.get("to_csv_service")
            try:
                if to_csv == 'y':
                    timenow = date.today().strftime('%Y%m%d')
                    filename = 'AnnualDay2022_Registrations_%s.csv' %(timenow)
                    flash('downloading file %s' %(filename), 'success')
                    return util.download_registrations( annualday_rows, filename, annualday_query)
                if to_csv_service == 'y':
                    timenow = date.today().strftime('%Y%m%d')
                    filename = 'Service_Requests_%s.csv' %(timenow)
                    flash('downloading file %s' %(filename), 'success')
                    return util.download_requests( rows, filename, query)
            except Exception as e:
                    flash('Error downloading file %s' %(filename), 'error')
                    print(e)
                    return redirect('/')

        # return render_template('main/service_request_admin_view.html', form=form, pagination=pagination, requests=requests, rowcount=len(rows), annualday_table = annualday_table, annualday_rowcount=len(annualday_rows))
        return render_template('main/service_request_admin_view.html', form=form, pagination=pagination, requests=requests, rowcount=len(rows), \
                                    annualday_pagination=annualday_pagination, registrations=registrations, annualday_rowcount=len(annualday_rows))

    except Exception as e:
        # flash('Error while fetching Service Request(s) Admin List', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')

@service_request_blueprint.route('/service_request_feedback_view', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def feedback_view():
    util.trace()
    try:
        feedback_query = db.session.query( Feedback.id, Feedback.email, Feedback.teach_experience, \
                                           Feedback.teach_continue, Feedback.teach_grade, \
                                           Feedback.teach_rec, Feedback.teach_ref_student, \
                                           Feedback.comments, Feedback.last_updated_at).distinct()
        # feedback_query = feedback_query.order_by( Feedback.last_updated_at )
        feedback_query = feedback_query.order_by( Feedback.id )
        feedback_rows = feedback_query.all()
        feedback_table = Results_Feedback(feedback_rows)
        feedback_table.border = True

        return render_template('main/feedback_view.html', feedback_table = feedback_table, feedback_rowcount=len(feedback_rows))

    except Exception as e:
        flash('Error while fetching FeebackForm(Teacher)', 'error')
        # flash(str(e), 'error')
        print(e)
        return redirect('/')


@service_request_blueprint.route('/feedback2022-23', methods=['GET', 'POST'])
@login_required
def feedback_create_page(view=0):
    util.trace()

    form = ServiceRequestFeedbackForm(request.form, obj=current_user)

    if request.method == 'POST' and form.validate():
        try:
            fdb_obj = Feedback()
            fdb_obj.email = request.form.get("email")
            fdb_obj.created_at = datetime.now()
            fdb_obj.last_updated_at = datetime.now()
            fdb_obj.last_updated_id = current_user.id
            fdb_obj.comments = request.form.get("comments")
            fdb_obj.teach_experience =  util.list_to_str( request.form.getlist("teach_exp"))
            fdb_obj.teach_continue =  util.list_to_str( request.form.getlist("teach_cont"))
            fdb_obj.teach_grade =  util.list_to_str( request.form.getlist("teach_grade"))
            fdb_obj.teach_rec =  util.list_to_str( request.form.getlist("teach_rec"))
            fdb_obj.teach_ref_student =  util.list_to_str( request.form.getlist("teach_ref_stud"))
            # Annualday_obj.events =  request.form.getlist("events")

            myfdb = db.session.query( Feedback).distinct().filter(Feedback.last_updated_id == current_user.id ).first()
            if myfdb:
                myfdb.email = fdb_obj.email
                myfdb.created_at = fdb_obj.created_at
                myfdb.last_updated_at = fdb_obj.last_updated_at
                myfdb.comments = fdb_obj.comments
                myfdb.teach_experience = fdb_obj.teach_experience
                myfdb.teach_continue = fdb_obj.teach_continue
                myfdb.teach_grade = fdb_obj.teach_grade
                myfdb.teach_rec = fdb_obj.teach_rec
                myfdb.teach_ref_student = fdb_obj.teach_ref_student
            else:
                db.session.add( fdb_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Teacher(s) Feedback submission Failed.', 'error')
            print(e)
            return redirect('/')

        # registration_id = db_util.get_annualday_registration_id(current_user.id)
        # notify_annualday_registration(Annualday_obj.email, registration_id, Annualday_obj.student_email, Annualday_obj.events, Annualday_obj.comments)
        flash('Your feedback submitted successfully. Thank you.', 'success')
    # Process GET or invalid POST
    try:

        return render_template('main/feedback_teacher.html', form=form)

    except Exception as e:
        flash('Error while fetching FeebackForm(Teacher)', 'error')
        # flash(str(e), 'error')
        print(e)
        return redirect('/')
