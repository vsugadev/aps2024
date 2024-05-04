from flask import Blueprint, flash, redirect, request, render_template
from datetime import date
from sqlalchemy import func

from flask_user import login_required, roles_required
from common import util

from models.orm_models import db, UIConfig
from views.forms import UIConfigForm
from views.tables import Results_CategoryList, Results_CategoryDetail

setting_blueprint = Blueprint('setting', __name__ )

@setting_blueprint.route('/category_list' )
@login_required
@roles_required('admin')

def category_list():
    util.trace()
    try:
        query = db.session.query( UIConfig.category ).distinct()
        rows = query.order_by( UIConfig.category ).all()

#        if not rows:
#            flash('No results found!', 'success')
#            return redirect('/')

        table = Results_CategoryList(rows )
        table.border = True
        return render_template('main/generic.html', table=table, mode='category_list', rowcount=len(rows) , title ='Config Category')
    except Exception as e:
        flash('Error while searching for Config Category', 'error')
        print(e)
        return redirect('/')


@setting_blueprint.route('/category_detail/<string:name>' )

@login_required
@roles_required('admin')

def category_detail(name):
    util.trace()
    try:
#        query = UIConfig.query.filter( UIConfig.category == name )
#        rows = query.order_by( UIConfig.order_by, UIConfig.category_key ).all()

        query = db.session.query( UIConfig.category, UIConfig.category_key, UIConfig.category_value, UIConfig.order_by, UIConfig.active , \
                    func.concat(UIConfig.category, '|',  UIConfig.id, '|', func.unix_timestamp(date.today())).label("link_id") ) \
                   .filter( UIConfig.category == name )
        rows = query.order_by( UIConfig.order_by, UIConfig.category_key ).all()

        for u in rows :
            print( u._asdict() )

        table = Results_CategoryDetail(rows )
        table.border = True
        return render_template('main/generic.html', table=table, mode='category_detail', rowcount=len(rows), title ='Config for %s' %name, name=name )
    except Exception as e:
        flash('Error while searching for config details', 'error')
        print(e)
        return redirect('/')


@setting_blueprint.route('/category_edit', defaults={'id': None }, methods=['GET', 'POST'] )  ##
@setting_blueprint.route('/category_edit/<string:id>' ,  methods=['GET', 'POST'] )

@login_required
@roles_required('admin')
def category_edit( id=None):
    util.trace()
    link_id = id
    id_list = link_id.split('|')
    name = id_list[0]
    id = int(id_list[1])

    if id == -1 :
        config_obj = UIConfig()
        config_obj.category = name
        config_obj.active = True
        config_obj.order_by = 0
    else :
        config_obj = UIConfig.query.filter( UIConfig.id == id ).first()

    print("Category %s - %s " %( name, id ) )
    form = UIConfigForm(request.form, obj=config_obj )
    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to class fields
        form.populate_obj(config_obj)
        try:
            if id == -1 :
                db.session.add(config_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Config Update Failed..', 'error')
            print(e)
            return redirect('/category_detail/%s' %name )
        flash('Config successfully Updated..', 'success')
        return redirect('/category_detail/%s' %name )

    # Process GET or invalid POST
    return render_template('main/config_edit.html', form=form, name=name )

