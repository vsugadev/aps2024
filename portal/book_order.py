from flask import Blueprint, flash, redirect, request, render_template, session
from sqlalchemy.sql.expression import literal
from datetime import datetime, date

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons

from models.orm_models import db, BookOrder, Enrollment
from views.forms import OrderTrackingEditForm
from views.tables import Results_BookOrder

book_blueprint = Blueprint('book_order', __name__ )

@book_blueprint.route('/book_update', methods=['POST'])
@login_required    # Use of @login_required decorator
@roles_required('admin')

def book_update():
    util.trace()
    try :
        on_commit = False
        data = request.form.to_dict()
        count = util.count( data.keys() )
        enroll_list =  []

        #TODO: Do not update enrollment info if sectiom is not changed. Need to compare amount from DB

        for row in range(count) :
            book_status = data.get("students-%s-book_status" %row)
            book_shipped_date = data.get("students-%s-book_shipped_date" %row)
            book_tracking_number = data.get("students-%s-book_tracking_number" %row)
            book_delivered_date = data.get("students-%s-book_delivered_date" %row)
            enroll_data = {'enrollment_id': data.get("students-%s-enrollment_id" %row) ,
                            'book_shipped_date' : book_shipped_date,
                            'book_tracking_number' : book_tracking_number,
                            'book_delivered_date' : book_delivered_date,
                            'book_status' : 'Y' if book_status else 'N' ,
                            'last_updated_at' : datetime.now(),
                            'last_updated_id' : current_user.id
                            }

            enroll_list.append( enroll_data )
        on_commit = True
        db.session.bulk_update_mappings(Enrollment, enroll_list )
        db.session.commit()
        on_commit = False
#        print( enroll_list )
        if len(enroll_list) > 0 :
            flash('Book distribution Status successfully updated for %s students' %len(enroll_list) , 'success')

        return redirect('/search?mode=book')

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating book distribution status', 'error')
        print(e)
        return redirect('/search?mode=book')


@book_blueprint.route('/book_order')
@login_required
@roles_required('admin')

def book_order():
    util.trace()
    try:
        query_enrolled = db.session.query( literal(0).label("order_id"), literal("ENROLLMENTS").label("type"), literal("ESTIMATED").label("status"),
                literal( "" ).label("order_date"), literal("").label("note"), db_util.get_query_confirmed(-1).label("nilai_A"), db_util.get_query_confirmed(0).label("nilai_0"),
                db_util.get_query_confirmed(1).label("nilai_1"), db_util.get_query_confirmed(2).label("nilai_2"), db_util.get_query_confirmed(3).label("nilai_3"),
                db_util.get_query_confirmed(4).label("nilai_4"), db_util.get_query_confirmed(5).label("nilai_5"), db_util.get_query_confirmed(6).label("nilai_6"),
                db_util.get_query_confirmed(7).label("nilai_7"), db_util.get_query_confirmed(8).label("nilai_8") )

        query_ordered = db.session.query( BookOrder.order_id, BookOrder.type, BookOrder.order_status, BookOrder.order_date, BookOrder.note,
                BookOrder.nilai_A, BookOrder.nilai_0, BookOrder.nilai_1, BookOrder.nilai_2, BookOrder.nilai_3, BookOrder.nilai_4, BookOrder.nilai_5,
                BookOrder.nilai_6, BookOrder.nilai_7, BookOrder.nilai_8 ).filter( BookOrder.academic_year == session["ACADEMIC_YEAR"] )

        query_balance = db.session.query( literal(10000).label("order_id"), literal("TO BE ORDERED").label("type"),
                literal("NOT ORDERED").label("status"), literal( "" ).label("order_date"), literal("").label("note"),
                literal( db_util.get_required_count(-1 )).label("nilai_A") ,
                literal( db_util.get_required_count( 0 )).label("nilai_0") ,
                literal( db_util.get_required_count( 1 )).label("nilai_1") ,
                literal( db_util.get_required_count( 2 )).label("nilai_2") ,
                literal( db_util.get_required_count( 3 )).label("nilai_3") ,
                literal( db_util.get_required_count( 4 )).label("nilai_4") ,
                literal( db_util.get_required_count( 5 )).label("nilai_5") ,
                literal( db_util.get_required_count( 6 )).label("nilai_6") ,
                literal( db_util.get_required_count( 7 )).label("nilai_7") ,
                literal( db_util.get_required_count( 8 )).label("nilai_8") )

        rows = query_enrolled.union(query_ordered, query_balance ).order_by(BookOrder.order_id).all()

        results = []
        for row in rows:
            row_dict = {}
            row_dict = row._asdict()
            total = 0
            for key, value in row_dict.items() :
                if isinstance(value, bytes ) :
                    row_dict.update({key : value.decode() })
                    total += int(value.decode())
                else :
                    row_dict.update({key : value })

            row_dict.update({"total" : total })
            results.append(row_dict)

        table = Results_BookOrder( results )
        table.border = True
        return render_template('main/book_tracking.html', table=table, rowcount=len(rows) )

    except Exception as e:
        flash('Error while processing book order', 'error')
        print(e.message if hasattr(e, 'message') else e)
        return redirect('/')


@book_blueprint.route('/order_tracking', defaults={'id': 0, 'mode':'edit'} ,  methods=['GET', 'POST'] )
@book_blueprint.route('/order_tracking/<int:id>/<string:mode>', methods=['GET', 'POST'])
@book_blueprint.route('/order_tracking/<int:id>', methods=['GET', 'POST'])

@login_required
@roles_required('admin')
def order_tracking(id, mode="edit"):
    util.trace()
    if mode == 'edit' and (id == 0 or id == 10000 ) :
        flash('This entry cannot be edited', 'error')
        return redirect('/book_order')

    # Initialize form
    if mode == 'new' :
        order_obj = BookOrder()
    else :
        order_obj = BookOrder.query.get(id)

    form = OrderTrackingEditForm(request.form, obj=order_obj  )

    # Process valid POST
    if request.method == 'POST' :  ## and form.validate():
        form.populate_obj( order_obj )
        try:
            order_obj.last_updated_at = datetime.now()
            order_obj.last_updated_id = current_user.id
            if mode == 'new' :
                order_obj.academic_year = session["ACADEMIC_YEAR"]
                order_obj.order_status = "ESTIMATED" if order_obj.order_type in ["TEACHERS_COPY" , "BUFFER" ] else order_obj.order_status
                db.session.add(order_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Book Order info update Failed..', 'error')
            print(e)
            return redirect('/book_order')
        flash('Book Order info sucessfully Updated..', 'success')
        # Redirect to home page
        return redirect('/book_order')

    # Process GET or invalid POST
    return render_template('main/book_tracking_edit.html', form=form)

@book_blueprint.route('/create_book_order')
@login_required
@roles_required('admin')
def create_book_order():
    util.trace()
    try :
        nilai_count = {}
        total = 0
        nilai_list = range(-1, 9)
        for nilai in nilai_list :
            count = db_util.get_required_count( nilai )
            if count > 0 :
                nilai_count.update({nilai : count })
                total += count
            else :
                nilai_count.update({nilai : 0 })

        if total == 0:
            flash('No order required..', 'success')
            return redirect('/book_order')

        order_obj = BookOrder()
        order_obj.academic_year = session["ACADEMIC_YEAR"]
        order_obj.type = "BOOK_ORDER"
        order_obj.order_status = "ORDERED"
        order_obj.order_date = date.today()
        order_obj.note = "Auto Generated"
        order_obj.last_updated_at = datetime.now()
        order_obj.last_updated_id = current_user.id
        order_obj.nilai_A = nilai_count[-1]
        order_obj.nilai_0 = nilai_count[0]
        order_obj.nilai_1 = nilai_count[1]
        order_obj.nilai_2 = nilai_count[2]
        order_obj.nilai_3 = nilai_count[3]
        order_obj.nilai_4 = nilai_count[4]
        order_obj.nilai_5 = nilai_count[5]
        order_obj.nilai_6 = nilai_count[6]
        order_obj.nilai_7 = nilai_count[7]
        order_obj.nilai_8 = nilai_count[8]

        db.session.add(order_obj)
        db.session.commit()
        order_id = order_obj.order_id
        update_enroll_with_order(order_id)

    except Exception as e:
        db.session.rollback()
        flash('Book Order creation Failed..', 'error')
        print(e)
        return redirect('/book_order')
    flash('Book Order created sucessfully..', 'success')
    # Redirect to home page
    return redirect('/book_order')

def update_enroll_with_order(order_id) :
    util.trace()
    try :
        db.session.query(Enrollment).filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
            .filter( Enrollment.enrollment_status.in_( [cons._ENROLLED_ONLINE, cons._ENROLL_CONFIRMED ] )) \
            .filter( Enrollment.nilai != 99 ) \
            .filter( Enrollment.order_id == None ) \
            .update({'order_id': order_id, 'last_updated_at' : datetime.now(), 'last_updated_id' : current_user.id }, synchronize_session='fetch' )

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('Book Order Update for enrollment Failed..')
        print(e)
        raise e

def check_book_order_exists(year):
    util.trace()
    query = db.session.query(BookOrder.type).filter( BookOrder.academic_year == year ).filter( BookOrder.type.in_(["TEACHERS_COPY" , "BUFFER" ]))
    type_list = [row.type for row in query.all()]
    return [ type for type in ("TEACHERS_COPY" , "BUFFER" ) if type not in type_list ]

def create_book_order_template(year) :
    util.trace()
    type_add = check_book_order_exists(year)
    order_list = []
    for type in type_add :
        order_data = { "academic_year" : year,
                        "type" : type,
                        "order_status" : "ESTIMATED",
                        "last_updated_at" : datetime.now(),
                        "last_updated_id" : current_user.id
                    }
        order_list.append( order_data )

    if order_list :
        db.session.bulk_insert_mappings(BookOrder, order_list )
        db.session.commit()
#        print("Created book order template for %s " % type_add )
    return type_add
