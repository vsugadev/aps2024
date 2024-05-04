from threading import Thread

from flask import Blueprint, flash, redirect, request, render_template, session, current_app
from datetime import date, datetime
from sqlalchemy import and_, func, case, desc

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons, email_manager as email
from common.mail import mail

from models.orm_models import db, Prize
from views.tables import  Results_Prize
from views.forms import PrizeAddForm
from flask_paginate import Pagination, get_page_parameter, get_page_args

from werkzeug.utils import secure_filename
import os

prize_blueprint = Blueprint('prize', __name__ )

@prize_blueprint.route('/prize_add_page', methods=['GET', 'POST'])
@login_required
# @roles_required('admin', 'hr')
def add_page():
    util.trace()
    # return redirect('/')
    try:
        form = PrizeAddForm(request.form, obj=current_user)

        # get Prize Request(s) Summary
        prize_query = db.session.query( Prize.id, Prize.winner_name, Prize.winner_email, Prize.winner_place, \
                                            Prize.status, Prize.parent_email, Prize.prize_amount, Prize.created_at)
        prize_query = prize_query.order_by( Prize.id )
        prize_rows = prize_query.all()

        prize_table = Results_Prize(prize_rows)
        prize_table.border = True

        # Process valid POST
        if request.method == 'POST' and form.validate():
            try:
                Prize_obj = Prize()
                winner_name = request.form.get("winner_name")
                Prize_obj.winner_name = winner_name
                winner_email = request.form.get("winner_email")
                Prize_obj.winner_email = winner_email
                winner_place = request.form.get("winner_place")
                Prize_obj.winner_place = winner_place
                parent_email = request.form.get("parent_email")
                Prize_obj.parent_email = parent_email
                prize_amount = request.form.get("prize_amount")
                Prize_obj.prize_amount = prize_amount
                Prize_obj.created_at = datetime.now()
                Prize_obj.last_updated_at = datetime.now()
                Prize_obj.last_updated_id = current_user.id
                Prize_obj.status = 0 # 0-open

                myprize = db.session.query(Prize).distinct().filter(Prize.winner_place == Prize_obj.winner_place ).first()
                if myprize:
                    myprize.winner_name = Prize_obj.winner_name
                    myprize.winner_email = Prize_obj.winner_email
                    myprize.winner_place = Prize_obj.winner_place
                    myprize.parent_email = Prize_obj.parent_email
                    myprize.prize_amount = Prize_obj.prize_amount
                    myprize.created_at = Prize_obj.created_at
                    myprize.last_updated_at = Prize_obj.last_updated_at
                    myprize.last_updated_id = Prize_obj.last_updated_id
                    Prize_obj.status = 0 # 0-open
                else:
                    db.session.add(Prize_obj)
                db.session.commit()

                flash('Prize Distribution Request Submitted Successfully.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(str(e), 'error')
                flash('Prize Distribution Request Submission Failed.', 'error')
                print(e)
                return redirect('/')

        return render_template('main/prize.html', form=form, prize_table = prize_table, prize_rowcount=len(prize_rows))

    except Exception as e:
        #flash('Error while fetching Prize Add Form()', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')

@prize_blueprint.route('/prize_distribution_page/<int:view>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def distribution_page(view=0):
    util.trace()
    try:
        if view == 0:
            title = 'Distribution Request: AnnualDay(2022-23)'
            prize_query = db.session.query( Prize.id, Prize.winner_name, Prize.winner_email, Prize.winner_place, \
                Prize.status, Prize.parent_email, Prize.prize_amount, Prize.created_at).filter(Prize.winner_place.contains('AnnualDay-2023-%'))
        if view == 1:
            title = 'Distribution Request: Volunteer Discount(2022-23)'
            prize_query = db.session.query( Prize.id, Prize.winner_name, Prize.winner_email, Prize.winner_place, \
                Prize.status, Prize.parent_email, Prize.prize_amount, Prize.created_at).filter(Prize.winner_place == 'AcademicYear-2022-23-Volunteer-discount')

        prize_query = prize_query.order_by( Prize.id )
        prize_rows = prize_query.all()

        prize_table = Results_Prize(prize_rows)
        prize_table.border = True

        return render_template('main/prize_view.html', title=title, prize_table = prize_table, prize_rowcount=len(prize_rows))

    except Exception as e:
        # flash('Error while fetching Winner Details', 'error')
        flash(str(e), 'error')
        print(e)
        return redirect('/')

