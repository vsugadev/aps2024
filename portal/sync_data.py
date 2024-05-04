from flask import Blueprint, flash, redirect

from io import BytesIO
import pandas as pd
import requests
from flask_user import current_user, login_required, roles_required
from models.orm_models import db

sync_data_blueprint = Blueprint('sync_data', __name__ )

#from pandas.io import sql
#from sqlalchemy import create_engine
#import pymysql

data_dict = {
        'APS2020_2021':'https://docs.google.com/spreadsheets/d/e/2PACX-1vRsc6ai6yKNTW7IkHomqhqmybEoxN3QgqcKWOrWWKp8dVtZ7Am6yPZyCCysEGJtohBPLTmBtyVLUfbs/pub?gid=0&single=true&output=csv'
        }

def get_data(location) :
    r = requests.get(location)
    data = r.content
    df = pd.read_csv(BytesIO(data))
    return df

def load_data(engine, table, location):
    df = get_data(location)
    df.to_sql(con=engine, name=table, if_exists='replace')

def sync_new(conn):
    try :
        table_name = 'APS2020_2021'
        location = data_dict[table_name]
        load_data(conn, table_name, location)
#        correct_data(conn)
        return update_data_new(conn)

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        raise

def update_data_new(connection)  :
    user_add = """insert into user ( is_active, email, password, email_confirmed_at, father_name, mother_name, email2, phone1, phone2, parents_street_address, parents_street_address2, parents_city, parents_state, parents_country, parents_zipcode, reference, last_updated)  select distinct  1, lower(email_address), '????', now(), concat(parent_first_name , " " , parent_last_name) , '', '', '', '' , '', '', now() from APS2020_2021 where lower(email_address) not in (select lower(u.email) from user u ) """
    student1_add = """insert into student (parent_id, student_id, student_name, student_email, birth_year, birth_month, start_year, sex, last_updated_at, last_updated_id, skill_level_joining, prior_tamil_school, note ) select u.id, right(e.temp_student_id, 3),  concat(student_first_name , " " , student_last_name), student_email_address, 2015, 1,  2020 , '' , now(), %s, '',  '', e.class_name_eng from APS2020_2021 e, user u where lower(u.email) = lower(e.email_address) and lower(concat(student_first_name , " " , student_last_name)) not in ( select lower(s.student_name) from student s ) """ %current_user.id
    enroll1_add = """insert into enrollment (student_id, academic_year, note, nilai, school_grade, last_updated_at , last_updated_id, enrollment_status  ) select s.student_id, 2020, e.class_name_eng, 99, 99, now(), %s, 'ENROLLED ONLINE' from APS2020_2021 e, student s where lower(concat(e.student_first_name , " " , e.student_last_name)) = lower(s.student_name) and lower(s.student_name) not in (select lower(ss.student_name ) from  student ss , enrollment ee where ss.student_id = ee.student_id )""" %current_user.id
    trans = connection.begin()

    try :
        print( "Inserting Users")
        results = connection.execute( user_add )
        users_count = results.rowcount
        print( "Inserting Student 1")
        results = connection.execute( student1_add )
        student_1_count = results.rowcount
        print( "Inserting Enrollment 1")
        results = connection.execute( enroll1_add )
        enroll_1_count = results.rowcount
        print( "Committing...")
        trans.commit()
        print(users_count, student_1_count,  enroll_1_count )
        return users_count, student_1_count,  enroll_1_count
    except Exception as e:
        trans.rollback()
        print( "Rolling back...")
        print(e.message if hasattr(e, 'message') else e)
        raise


## Moved from main. Not needed now
@sync_data_blueprint.route('/sync_data_new')
@login_required
@roles_required('admin')

def sync_data_new():
    conn = db.engine.connect()
    try :
        u,s,e = sync_new(conn)
        flash('%s Parents %s Students & %s Enrollments successfully added into portal' %(u,s,e) , 'success')
        return redirect('/')

    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        flash('Error while Syncing New Students', 'error')
        return redirect('/')

