from flask import Blueprint, flash, redirect, request, render_template, session
from datetime import date, datetime
from sqlalchemy import func

from flask_user import login_required, roles_required, current_user
from common import db_util, util, constant as cons

from models.orm_models import db, Enrollment, Student, User, UserRole
from views.forms import SearchForm, StudentNameForm, StudentNameMainForm, UserParentProfileForm, UserProfileForm
from views.tables import Results_Profile

profile_blueprint = Blueprint('profile', __name__ )

@profile_blueprint.route('/search_profile', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def search_profile():
    util.trace()
    mode = 'profile'
    search = SearchForm( request.form, mode = mode )

    if request.method == 'POST':
        return results_profile(search)

    title = 'Profile Lookup'
    return render_template('main/search.html', form=search, title = title, mode = mode )

@profile_blueprint.route('/results_profile')
@login_required
@roles_required('admin')

def results_profile(search):
    util.trace()
    try:
        name_string = search.data['name'].strip()
        role = search.data['role']
#        inactive = search.data['inactive']
        to_csv = search.data['to_csv']
        mode = search.data['mode']

        query = db.session.query(User.id, User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2, User.parents_city, \
                    User.parents_state, User.parents_country, func.concat(User.id, '|', func.unix_timestamp(date.today())).label("parent_id"),
                    func.group_concat(UserRole.role_id, ",").label("roles")  ) \
            .outerjoin(UserRole, UserRole.user_id == User.id ) \
            .filter((User.father_name.like("%" + name_string + "%")| User.mother_name.like("%" + name_string + "%")| User.email.like("%" + name_string + "%") | User.email2.like("%" + name_string + "%") ))

        if role:
            query_role = UserRole.query.filter(UserRole.role_id == role )
            user_list = [ row.user_id for row in query_role.all() ]

            if not user_list  :
                flash('No User Matching!', 'success')
                return redirect('/search_profile')

            query = query.filter( User.id.in_( user_list ))

        rows = query.group_by(User.id, User.father_name, User.mother_name, User.email, User.email2, User.phone1, User.phone2) \
                    .order_by( User.father_name ).all()

        if not rows:
            flash('No results found!', 'success')
            return redirect('/search_profile')

#        for u in rows:
#            print( u._asdict() )
        if not to_csv :
            table = Results_Profile(rows )
            table.border = True
            title = "Profile Update"
            return render_template('main/generic.html', table=table, title=title , mode=mode, rowcount=len(rows) )
        else :
            return util.download( rows, '%s_report.csv' %mode, query)

    except Exception as e:
        flash('Error while fetching role', 'error')
        print(e)
        return redirect('/search_profile')


@profile_blueprint.route('/parent_profile/<string:id_str>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def parent_profile(id_str):
    util.trace()
    # Initialize form
    id_list = id_str.split('|')
    id = int(id_list[0])
    user_obj = User.query.get(id)
    form = UserParentProfileForm(request.form, obj=user_obj)

    query_role = UserRole.query.filter(UserRole.user_id == user_obj.id )
    form.roles.data = [ row.role_id for row in query_role.all() ]

    # Process valid POST
    if request.method == 'POST' and form.validate():
        roles = request.form.getlist("roles")
        user_data = request.form.to_dict()
        user_data.pop("roles", None)
        user_data.pop("submit")
        user_data['id']=id

        # Copy form fields to user_profile fields
        try:
            db.session.bulk_update_mappings(User, [user_data] )
            set_roles( id, roles )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Profile Update Failed..', 'error')
            print(e)
            return redirect('/')
        flash('Profile Updated..', 'success')

        return redirect('/')

    # Process GET or invalid POST
    return render_template('main/parent_profile.html', form=form)

@profile_blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    util.trace()

    # Initialize form

    form = UserProfileForm(request.form, obj=current_user)

    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to user_profile fields
        form.populate_obj(current_user)
        try:
            role = 'parent'
            db_util.find_or_create_user_roles( current_user.id, role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Profile Failed..', 'error')
            print(e)
            return redirect('/')
#        db.session.remove()
        flash('Profile Updated..', 'success')
        # Redirect to home page
        if db_util.enrollment_count(current_user.id) > 0 or db_util.is_user_role(current_user.id, 'teacher') or db_util.is_user_role(current_user.id, 'admin') :
            return redirect('/')
        else :
            return redirect('/myenrollment')

    # Process GET or invalid POST
    return render_template('main/user_profile.html', form=form)


@profile_blueprint.route('/name_list')
@profile_blueprint.route('/name_list/<int:section>')
@login_required
@roles_required('teacher')

def name_list( section=None ):
    util.trace()
    try:
        sections = db_util.get_teacher_sections( current_user.id )
        if not sections  :
            flash('No Class assigned yet!', 'success')
            return redirect('/')

        if section and len(sections) > section :
            current_section = [ sections[section] ]
        else :
            current_section =  [ sections[0] ]

        query_enroll = db.session.query(Student.student_id, Student.student_name, Student.student_name_tamil, Student.student_email, Enrollment.section ) \
                            .join(Enrollment, Enrollment.student_id == Student.student_id) \
                            .filter( Enrollment.enrollment_status.notin_( cons._ENROLL_DISCONTINUED )) \
                            .filter( Enrollment.academic_year == session["ACADEMIC_YEAR"] ) \
                            .filter( Enrollment.section.in_( current_section ))
        rows = query_enroll.order_by( Enrollment.section, Student.student_name ).all()

        main_form = StudentNameMainForm()
        for row in rows:
            student_form = StudentNameForm()
            student_form.student_id = row.student_id
            student_form.section = row.section
            student_form.student_name = row.student_name
            student_form.student_name_tamil = row.student_name_tamil
            student_form.student_name_previous = row.student_name_tamil
            student_form.student_email = row.student_email
            student_form.student_email_previous = row.student_email

            main_form.students.append_entry(student_form)

        title="Student Details Update"
        section_dict = {}
        if len(sections) > 1 :
            section_dict = {k: v for k, v in enumerate(sections)}
            title = title + " - %s" %current_section[0]

        return render_template('main/student_name_update.html', title=title, form=main_form, count=len(rows), section_dict=section_dict )

    except Exception as e:
        flash('Error while getting student list', 'error')
        print(e)
        return redirect('/' )

@profile_blueprint.route('/name_update', methods=['POST'])
@login_required
@roles_required('teacher')

def name_update():
    util.trace()
    try :
        on_commit = False

        data = request.form.to_dict()
        count = util.count( data.keys() )
#        print(data)
#        print( "data %s , count %s" %(len(data), count ) )
        list_update =  []

        for row in range(count) :
            student_id = data.get("students-%s-student_id" %row)
            student_name_tamil = data.get("students-%s-student_name_tamil" %row)
            student_email = data.get("students-%s-student_email" %row)
            student_name_previous = data.get("students-%s-student_name_previous" %row)
            student_email_previous = data.get("students-%s-student_email_previous" %row)

            if student_name_tamil != student_name_previous or student_email != student_email_previous :
                student_data = { 'student_id' : student_id ,
                                'student_name_tamil' : student_name_tamil ,
                                'student_email' : student_email ,
                                'last_updated_at' : datetime.now() ,
                                'last_updated_id' : current_user.id
                              }
                list_update.append( student_data )

        if list_update :
            on_commit = True
            db.session.bulk_update_mappings(Student, list_update )
            db.session.commit()
            on_commit = False
            flash('Student Details successfully updated for %d students' % (len(list_update)) , 'success')
        else :
            flash('Nothing changed', 'success')

        return redirect('/name_list' )

    except Exception as e:
        if on_commit :
            db.session.rollback()
        flash('Error while updating student name', 'error')
        print(e)
        return redirect('/name_list' )

def set_roles( user_id, role_new ):
    util.trace()
    try :
        role_new = set ( [int(role)  for role in role_new ] )
        role_existing = set( [row.role_id for row in UserRole.query.filter( UserRole.user_id == user_id).all()] )
        role_add = role_new - role_existing
        role_delete = list(role_existing - role_new )

        role_new_data = []
        for role in  role_add :
            role_new_data.append( {'user_id': user_id , 'role_id' : role  } )

        if role_new_data :
            db.session.bulk_insert_mappings( UserRole, role_new_data )
        if role_delete :
            user_role_delete = UserRole.query.filter((UserRole.role_id.in_(role_delete)) & (UserRole.user_id == user_id) ).all()
            for ur in user_role_delete :
#                print( ur.user_id, ur.role_id )
                db.session.delete( ur )
    except Exception as e:
        flash('User Role Update failed..', 'error')
        print(e)
        raise e
