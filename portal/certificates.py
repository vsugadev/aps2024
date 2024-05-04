from threading import Thread

from flask import Blueprint, flash, redirect, request, render_template, session, current_app
from datetime import date, datetime
from sqlalchemy import and_, func, case, desc

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.mail import mail

from models.orm_models import db, ServiceRequests, ServiceRequestAnnualDay, ServiceRequestAnnualDay_Uploads
from views.tables import Results_ServiceRequests, Results_ServiceRequests_Admin, Results_ServiceRequestAnnualDay, Results_ServiceRequestAnnualDay_Uploads
from views.forms import ServiceRequestNewForm, ServiceRequestAnnualDayForm, ServiceRequestAdminForm, ServiceRequestUpdateForm, ServiceRequestAnnualDaySignupForm
from flask_paginate import Pagination, get_page_parameter, get_page_args

from werkzeug.utils import secure_filename
import os

certificates_blueprint = Blueprint('certificates', __name__ )


@certificates_blueprint.route('/my_certs', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def my_certs():
    flash('certificate(s) would be availbale soon', 'success')
    return redirect('/')

