
from flask import Blueprint
from sqlalchemy import func
from sqlalchemy.sql.expression import literal
from flask import flash, redirect, render_template, session

from flask_user import login_required, roles_required
from common import util
from models.orm_models import db, Nilai, Enrollment
from views.tables import Results_Dashboard

dashboard_blueprint = Blueprint('dashboard', __name__ )

@dashboard_blueprint.route('/dashboard', methods=['GET'])
@login_required    # Use of @login_required decorator
@roles_required('admin')
def dashboard():
    util.trace()
    try:
        query = db.session.query( Nilai.nilai_id, Nilai.name.label('nilai'),
                        func.IF(Enrollment.section == '', literal('Unassigned-New'), func.ifnull(Enrollment.section, literal('Unassigned'))).label("section"),
                        func.count(Enrollment.enrollment_id).label("count")) \
                    .join(Enrollment, Nilai.nilai_id == Enrollment.nilai ) \
                    .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
                    .filter( Enrollment.enrollment_status.notin_((0,3,4)) ) \
                    .group_by( Nilai.nilai_id, Nilai.name, Enrollment.section )
        rows = query.all()
        if not rows:
            flash('No results found!', 'success')
            return redirect('/')
        table = Results_Dashboard(rows )
        table.border = True
        #flash('%s students enrolled' %len(rows))
        total = sum([row.count for row in rows ])
        return render_template('main/dashboard.html', table=table, total=total, title = "Class Dashboard" )
    except Exception as e:
        flash('Error while processing class dashboard', 'error')
        print(e)
        return redirect('/')

