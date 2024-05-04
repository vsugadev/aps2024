from flask_user import  UserMixin
from sqlalchemy.sql import func

#from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy

class SQLAlchemy(_BaseSQLAlchemy):
    def apply_pool_defaults(self, app, options):
        super(SQLAlchemy, self).apply_pool_defaults(app, options)
        options["pool_pre_ping"] = True

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
#    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    father_name = db.Column(db.String(50), nullable=False, server_default='')
    mother_name = db.Column(db.String(50), nullable=False, server_default='')
    email2 = db.Column(db.String(50), nullable=False, server_default='')
    phone1 = db.Column(db.String(15), nullable=False, server_default='')
    phone2 = db.Column(db.String(15), nullable=False, server_default='')
    parents_street_address = db.Column(db.String(32), nullable=True, server_default='')
    parents_street_address2 = db.Column(db.String(32), nullable=True, server_default='')
    parents_city = db.Column(db.String(32), nullable=True, server_default='')
    parents_state = db.Column(db.String(32), nullable=True, server_default='')
    parents_country = db.Column(db.String(32), nullable=True, server_default='')
    parents_zipcode = db.Column(db.String(32), nullable=True, server_default='')
    reference = db.Column(db.String(32), nullable=True, server_default='')

    teaching_volunteer = db.Column(db.String(1), nullable=False, server_default='N' )
    teaching_dayntime = db.Column(db.String(32), nullable=True, server_default='' )
    teaching_grade = db.Column(db.String(32), nullable=True, server_default='' )
    class_parent = db.Column(db.String(1), nullable=False, server_default='N' )

    last_updated = db.Column(db.DateTime(), nullable=True,  onupdate=func.now())

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_role')

    def __repr__(self):
        return '<User %r>' % (self.father_name)

class SchoolYear(db.Model):
    __tablename__ = 'school_year'
    academic_year = db.Column(db.Integer(), primary_key=True )
    academic_year_label = db.Column(db.String(10), nullable=False )
    start_date = db.Column(db.Date(), nullable=False )
    end_date = db.Column(db.Date(), nullable=False )
    school_day = db.Column(db.String(12), nullable=False )
    school_start_time = db.Column(db.Time(), nullable=True )
    rollover_status = db.Column(db.Integer(), nullable=False, default=0 )

    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRole association table
class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id' ))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id' ))


# Define the Student association table
class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer(), primary_key=True, autoincrement=True )  ## , autoincrement=True
    parent_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    student_first_name = db.Column(db.String(50), nullable=False)
    student_last_name = db.Column(db.String(50), nullable=False)
    student_name = db.Column(db.String(50), nullable=False)
    student_name_tamil = db.Column(db.String(50), nullable=True, server_default='')
    age = db.Column(db.String(8), nullable=True, server_default='')
    student_email = db.Column(db.String(50), nullable=True, server_default='')
    birth_year  = db.Column(db.Integer(), nullable=False )
    birth_month = db.Column(db.Integer(), nullable=False )
    start_year = db.Column(db.Integer(), nullable=False )
    sex = db.Column(db.String(1), nullable=False)
    active = db.Column(db.Integer(), nullable=False, default=1 )
    note = db.Column(db.String(255), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default = func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )
    preferred_dayntime = db.Column(db.String(32), nullable=True )
    preferred_grade = db.Column(db.String(32), nullable=True )
    skill_level_joining = db.Column(db.String(50), nullable=True )
    prior_tamil_school = db.Column(db.String(255), nullable=True )


# Define the Enrollment association table
class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    enrollment_id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    student_id = db.Column(db.Integer(), db.ForeignKey('student.student_id'), nullable=False)
    academic_year = db.Column(db.Integer(), db.ForeignKey('school_year.academic_year'), nullable=False )
    nilai  = db.Column(db.Integer(), db.ForeignKey('nilai.nilai_id'), nullable=False )
    section = db.Column("class", db.String(24), nullable=True )
    school_grade  = db.Column(db.Integer(), nullable=False )
    last_year_class = db.Column(db.String(2), nullable=True )
    enrollment_status = db.Column(db.Integer(), nullable=False, default=0 )
    payment_status = db.Column(db.String(1), nullable=False, server_default='N' )
    previous_balance = db.Column(db.Numeric(10,2), nullable=False, default=0 )
    due_amount = db.Column(db.Numeric(10,2), nullable=True  )
    discount_amount = db.Column(db.Numeric(10,2), nullable=False, default=0 )
    paid_amount = db.Column(db.Numeric(10,2), nullable=False, default=0 )
    paid_date = db.Column(db.Date(), nullable=True)
    payment_status = db.Column(db.String(1), nullable=False, server_default='N' )
    check_no = db.Column(db.String(40), nullable=True)
    book_shipment_preference = db.Column(db.String(24), nullable=True)
    book_status = db.Column(db.String(1), nullable=False, server_default='N' )
    book_shipped_date = db.Column(db.String(24), nullable=True)
    book_tracking_number = db.Column(db.String(24), nullable=True)
    book_delivered_date = db.Column(db.String(24), nullable=True)
    book_delivered = db.Column(db.Date(), nullable=True)
    active = db.Column(db.Integer(), nullable=False, default=1 )
    note = db.Column(db.String(255), nullable=True )
    order_id = db.Column(db.Integer(), db.ForeignKey('book_order.order_id'), nullable=True )
    is_waiver_signed = db.Column(db.Integer(), nullable=True )
    is_consent_signed = db.Column(db.Integer(), nullable=True )
    consent_signed_by = db.Column(db.String(40), nullable=True )
    consent_dated   = db.Column(db.DateTime(), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default = func.now() )
    last_updated_id = db.Column(db.Integer(), nullable=False )


class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    enrollment_id = db.Column(db.Integer(), db.ForeignKey('enrollment.enrollment_id'), nullable=False)
    paid_amount = db.Column(db.Numeric(10,2), nullable=False )
    transaction_fee = db.Column(db.Numeric(10,2), nullable=False, default=0 )
    paid_date = db.Column(db.Date(), nullable=False,  default = func.now() )
    payment_mode = db.Column( db.String(12), nullable=False , server_default='CHECK' )
    reference = db.Column(db.String(50), nullable=True)
    note = db.Column(db.String(255), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default = func.now() )
    last_updated_id = db.Column(db.Integer(), nullable=False )


class Nilai(db.Model):
    __tablename__ = 'nilai'
    nilai_id = db.Column(db.Integer(), autoincrement=False, primary_key=True)
    name = db.Column(db.String(12), nullable=False )


class Section(db.Model):
    __tablename__ = 'class'
    section = db.Column("class", db.String(24), primary_key=True )
    academic_year = db.Column(db.Integer(), db.ForeignKey('school_year.academic_year'), primary_key=True )
    nilai_id = db.Column(db.Integer(), db.ForeignKey('nilai.nilai_id'), nullable=False )
    room = db.Column(db.String(12), nullable=True )
    teacher1_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True )
    teacher2_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True )
    teacher3_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True )
    class_day = db.Column(db.String(12), nullable=False )
    class_start_time = db.Column(db.Time(), nullable=True )
    class_email = db.Column(db.String(40), nullable=True)
    teacher_view = db.Column(db.Integer(), nullable=False, default=0 )
    parent_view = db.Column(db.Integer(), nullable=False, default=0 )

# Define the UI Config
class UIConfig(db.Model):
    __tablename__ = 'ui_config'
    id = db.Column(db.Integer(), primary_key=True)
    category = db.Column(db.String(32), nullable=False, server_default='')
    category_key = db.Column(db.String(32), nullable=False, server_default='')
    category_value = db.Column(db.String(32), nullable=False, server_default='')
    active = db.Column(db.Integer(), nullable=False, default=1 )
    order_by = db.Column(db.Integer(), nullable=False, default=0 )

class RateCard(db.Model):
    __tablename__ = 'rate_card'
    academic_year = db.Column(db.Integer(), db.ForeignKey('school_year.academic_year'), primary_key=True)
    rate_type  = db.Column(db.String(40), primary_key=True )
    rate = db.Column(db.Numeric(10,2), nullable=False, default=0 )


class SchoolCalendar(db.Model):
    __tablename__ = 'school_calendar'
    school_date = db.Column(db.Date(), primary_key=True )
    academic_year = db.Column(db.Integer(),  db.ForeignKey('school_year.academic_year'), nullable=False )
    note = db.Column(db.String(100), nullable=True )
    is_session = db.Column(db.Integer(), nullable=False, default=1 )
    attendance_required = db.Column(db.Integer(), nullable=False, default=1 )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )


class Attendance(db.Model):
    __tablename__ = 'attendance'
    school_date = db.Column(db.Date(), db.ForeignKey('school_calendar.school_date'), nullable=False, primary_key=True )
    enrollment_id = db.Column(db.Integer(), db.ForeignKey('enrollment.enrollment_id'), nullable=False, primary_key=True )
    section = db.Column("class", db.String(24), nullable=False )
    attendance_status = db.Column(db.Integer(), nullable=False )
    attendance_score = db.Column(db.Integer(), nullable=False )
    note = db.Column(db.String(100), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

class Exam(db.Model):
    __tablename__ = 'exam'
    enrollment_id = db.Column(db.Integer(), db.ForeignKey('enrollment.enrollment_id'), nullable=False, primary_key=True )
    trimester_id = db.Column(db.Integer(), nullable=False, primary_key=True )
    academic_year = db.Column(db.Integer(),  db.ForeignKey('school_year.academic_year'), nullable=False )
    section = db.Column("class", db.String(24), nullable=False )
    written_score = db.Column(db.Numeric(4,1), nullable=False, default=0  )
    oral_score = db.Column(db.Numeric(4,1), nullable=False, default=0  )
    exam_score = db.Column(db.Numeric(4,1), nullable=False, default=0  )
    listening_eval = db.Column(db.Integer(), nullable=False, default=0 )
    speaking_eval = db.Column(db.Integer(), nullable=False, default=0 )
    reading_eval = db.Column(db.Integer(), nullable=False, default=0 )
    writing_eval = db.Column(db.Integer(), nullable=False, default=0 )
    is_ptm_completed = db.Column( db.Boolean(), nullable=False, default=0)
    ptm_completed_date = db.Column( db.Date(), nullable=True )
    exam_date = db.Column(db.Date(), nullable=False )
    note = db.Column(db.Text(), nullable=True )
    note_from_parents = db.Column(db.Text(), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

class Homework(db.Model):
    __tablename__ = 'homework'
    enrollment_id = db.Column(db.Integer(), db.ForeignKey('enrollment.enrollment_id'), nullable=False, primary_key=True )
    homework_type = db.Column(db.Integer(), nullable=False, primary_key=True )
    lesson_no = db.Column(db.Integer(), nullable=False, primary_key=True )
    academic_year = db.Column(db.Integer(),  db.ForeignKey('school_year.academic_year'), nullable=False )
    section = db.Column("class", db.String(24), nullable=False )
    homework_status = db.Column(db.Integer(), nullable=False )
    homework_score = db.Column(db.Numeric(4,1), nullable=False, default=0  )
    homework_date = db.Column(db.Date(), nullable=False )
    note = db.Column(db.String(100), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )


class Lesson(db.Model):
    __tablename__ = 'lesson'
    lesson_no = db.Column(db.Integer(), nullable=False, primary_key=True )
    academic_year = db.Column(db.Integer(),  db.ForeignKey('school_year.academic_year'), nullable=False, primary_key=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )


class BookOrder(db.Model):
    __tablename__ = 'book_order'
    order_id = db.Column(db.Integer(), autoincrement=True, nullable=False, primary_key=True )
    academic_year = db.Column(db.Integer(),  db.ForeignKey('school_year.academic_year'), nullable=False )
    type = db.Column(db.String(15), nullable=False  )
    order_date = db.Column(db.Date(), nullable=True )
    order_status = db.Column(db.String(10), nullable=True )
    nilai_A = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_0 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_1 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_2 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_3 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_4 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_5 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_6 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_7 = db.Column(db.Integer(), nullable=False, default=0 )
    nilai_8 = db.Column(db.Integer(), nullable=False, default=0 )
    note = db.Column(db.String(100), nullable=True )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )


class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer(), autoincrement=True, nullable=False, primary_key=True )
    parent_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    enrollment_id = db.Column(db.Integer(), db.ForeignKey('enrollment.enrollment_id'), nullable=True )
    notification_type = db.Column(db.String(32), nullable=False  )
    created_at = db.Column(db.DateTime(), nullable=False, default=func.now())
    created_id = db.Column(db.Integer(), nullable=False )
    status = db.Column(db.Integer(), nullable=False , default=0 )
    retry_count = db.Column(db.Integer(), nullable=False , default=0 )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )


class ClassTracking(db.Model):
    __tablename__ = 'class_tracking'
    school_date = db.Column(db.Date(), db.ForeignKey('school_calendar.school_date'), nullable=False, primary_key=True )
    section = db.Column("class", db.String(24), db.ForeignKey('class.class'), nullable=False, primary_key=True )
    academic_year = db.Column(db.Integer(),  db.ForeignKey('school_calendar.academic_year'), nullable=False, primary_key=True )
    teacher1_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False )
    teacher2_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True )
    substitute_teacher = db.Column(db.String(40), nullable=True )
    lesson_no = db.Column(db.Integer(), nullable=True )
    class_activities = db.Column(db.Text(), nullable=False )
    homework_paper = db.Column(db.Text(), nullable=False )
    homework_audio = db.Column(db.Text(), nullable=False )
    note_to_parents = db.Column(db.Text(), nullable=True )
    note_to_admin = db.Column(db.Text(), nullable=True )
    note_from_admin = db.Column(db.Text(), nullable=True )
    is_email_sent = db.Column( db.Boolean(), nullable=False, server_default='0')
    email_sent_date = db.Column(db.Date(), nullable=True )
    volunteers_present = db.Column(db.String(50), nullable=True )
    volunteers_activities = db.Column(db.Text(), nullable=True )
    class_date = db.Column(db.Date(), nullable=False )
    class_start_time = db.Column(db.Time(), nullable=False )
    class_end_time = db.Column(db.Time(), nullable=False )
    created_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

# Define the Service Requests association table
class ServiceRequests(db.Model):
    __tablename__ = 'service_requests'
    service_id = db.Column(db.Integer(), autoincrement=True, nullable=False, primary_key=True )
    created_by = db.Column(db.Text(), nullable=False )
    created_for = db.Column(db.Text(), nullable=False )
    service_type = db.Column(db.Text(), nullable=False )
    service_description = db.Column(db.Text(), nullable=False )

    response = db.Column(db.Text(), nullable=True )
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False )
    open = db.Column(db.Integer(), nullable=False )
    closed = db.Column(db.Integer(), nullable=False )
    status = db.Column(db.Integer(), nullable=False )
    created_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

# Define the Annual Day 2022 association table
class ServiceRequestAnnualDay(db.Model):
    __tablename__ = 'annualday_2022'
    registration_id = db.Column(db.Integer(), autoincrement=True, nullable=False, primary_key=True )
    comments = db.Column(db.Text(), nullable=False )
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False )
    events = db.Column(db.Text(), nullable=False )
    email = db.Column(db.Text(), nullable=False )
    student_email = db.Column(db.Text(), nullable=False )
    created_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

class ServiceRequestAnnualDay_Uploads(db.Model):
    __tablename__ = 'annualday_2022_uploads'
    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.Text(), nullable=False )
    data = db.Column(db.LargeBinary, nullable=False )
    data_size = db.Column(db.Integer(), nullable=False )
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False )
    created_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

# Define the Feedbackassociation table
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer(), nullable=False, primary_key=True )
    academic_year = db.Column(db.Integer(), nullable=False)
    email = db.Column(db.Text(), nullable=False)
    teach_experience = db.Column(db.Text(), nullable=True )
    teach_continue = db.Column(db.Text(), nullable=True )
    teach_grade = db.Column(db.Text(), nullable=True )
    teach_rec = db.Column(db.Text(), nullable=True )
    teach_ref_student = db.Column(db.Text(), nullable=True )
    comments = db.Column(db.Text(), nullable=True )
    created_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )

class Prize(db.Model):
    __tablename__ = 'prize'
    id = db.Column(db.Integer(), nullable=False, primary_key=True )
    winner_name = db.Column(db.Text(), nullable=False )
    winner_email = db.Column(db.Text(), nullable=False )
    parent_email = db.Column(db.Text(), nullable=False )
    prize_amount = db.Column(db.Text(), nullable=False )
    last_updated_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    last_updated_id = db.Column(db.Integer(), nullable=False )
    created_at = db.Column(db.DateTime(), nullable=False,  onupdate=func.now(), default=func.now())
    winner_place = db.Column(db.Text(), nullable=False)
    status = db.Column(db.Integer(), nullable=False )

