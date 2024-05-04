from threading import Thread

from flask import Blueprint, flash, redirect, request, render_template, session, current_app
from datetime import date, datetime
from sqlalchemy import and_, func, case, desc

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.mail import mail

from models.orm_models import db, Student, User
from views.tables import  Results_APSian
from views.forms import TheduForm
from flask_paginate import Pagination, get_page_parameter, get_page_args

from werkzeug.utils import secure_filename
import os

thedu_blueprint = Blueprint('thedu', __name__ )

@thedu_blueprint.route('/thedu_view_page', methods=['GET', 'POST'])
@login_required
# @roles_required('admin', 'hr')
def view_page():
    util.trace()
    # return redirect('/')
    try:
        form = TheduForm(request.form, obj=current_user)

        # Process valid POST
        if request.method == 'POST' and form.validate():
            try:
                name = request.form.get("name")
                apsian = Student()
                apsian.student_name = name
                apsian_new = db.session.query(Student).distinct().filter(Student.student_name == apsian.student_name).first()
                if apsian_new.parent_id:
                    # details = db.session.query(User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, User.parents_city, User.parents_state ).distinct().filter(User.id == apsian_new.parent_id).first()
                    apsian_query = db.session.query(User).distinct().filter(User.id == apsian_new.parent_id)
                    apsian_rows = apsian_query.all()
                    apsian_table = Results_APSian(apsian_rows)
                    apsian_table.border = True
                    return render_template('main/thedu.html', form=form, table = apsian_table, rowcount=len(apsian_rows))
                if not apsian_new.parent_id:
                    flash('Student details for %s not found'  %(name), 'error');
                #apsian_query = details.order_by( User.father_name )
                #apsian_rows = apsian_query.all()

            except Exception as e:
                db.session.rollback()
                flash('Searching APSians Failed.', 'error')
                flash(str(e), 'error')
                print(e)

        return render_template( 'main/thedu.html', form=form, rowcount=0)

    except Exception as e:
        #flash('Error while launching find APSians', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')


    '''
    try:
        form = TheduForm(request.form, obj=current_user)

        # select father_name, mother_name, email, email2, phone1, phone2, parents_city, parents_state, parents_country
        # from user where id = (
        # select parent_id from
        # student where student_email like '%_aps487%');

        # Process valid POST
        if request.method == 'POST' and form.validate():
            try:
                Student_Find_obj = FindMe()
                name = request.form.get("name")
                Prize_obj.winner_name = winner_name
                winner_email = request.form.get("student_email")
                Prize_obj.winner_email = winner_email

                myprize = db.session.query(Prize).distinct().filter(Prize.winner_place == Prize_obj.winner_place ).first()
                if myprize:
                    myprize.winner_name = Prize_obj.winner_name
                    myprize.winner_email = Prize_obj.winner_email
                    myprize.winner_place = Prize_obj.winner_place
                    myprize.prize_amount = Prize_obj.prize_amount
                    myprize.created_at = Prize_obj.created_at
                    myprize.last_updated_at = Prize_obj.last_updated_at
                    myprize.last_updated_id = Prize_obj.last_updated_id
                else:
                    db.session.add(Prize_obj)
                db.session.commit()

                flash('Prize Distribution Request Submitted Successfully.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Prize Distribution Request Submission Failed.', 'error')
                print(e)
                return redirect('/')

        return render_template('main/prize.html', form=form, prize_table = prize_table, prize_rowcount=len(prize_rows))

    except Exception as e:
        #flash('Error while fetching Prize Add Form()', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')

@thedu_blueprint.route('/prize_distribution_page', methods=['GET', 'POST'])
@thedu_required
@roles_required('admin')
def distribution_page():
    util.trace()
    try:
        prize_query = db.session.query( Prize.id, Prize.winner_name, Prize.winner_email, Prize.winner_place, Prize.prize_amount, Prize.created_at)
        prize_query = prize_query.order_by( Prize.id )
        prize_rows = prize_query.all()

        prize_table = Results_Prize(prize_rows)
        prize_table.border = True

        return render_template('main/prize_view.html', prize_table = prize_table, prize_rowcount=len(prize_rows))

    except Exception as e:
        # flash('Error while fetching Winner Details', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')

        '''


