import calendar
from datetime import date
from flask import session
from flask_wtf import FlaskForm
from wtforms import Form, StringField, DecimalField, IntegerField, RadioField, BooleanField, SubmitField, DateField as Date_Field # TimeField
from wtforms import FieldList, FormField, HiddenField,  TextAreaField, SelectField, SelectMultipleField #, validators
from wtforms.widgets import CheckboxInput, ListWidget, TextArea
from wtforms.validators import InputRequired, Optional, Required, DataRequired, NumberRange, Email
from wtforms.fields.html5 import DateField, TimeField, EmailField, TelField

from models.orm_models import Nilai, UIConfig, User, Role, UserRole, SchoolCalendar, SchoolYear, Section, Lesson, ServiceRequests, ServiceRequestAnnualDay

class SearchForm(Form):
    notification_type = SelectField('Notification Type:', validators=[ DataRequired("Type is required")] )
    name = StringField('Name :')
    section = StringField('Class :')
    nilai = SelectField('Nilai :')
    paid = SelectField('Paid Status :', choices= [("", "ALL"), ('Y','Paid' ), ('N', 'Unpaid'), ('P', 'Partial'), ('O', 'OverPaid')] )
    enrollment = SelectField('Enrollment :' )
    new = BooleanField('New Students Only? :')
    inactive = BooleanField('Include InActive Students ? :')
    to_csv = BooleanField('To CSV :')
    to_email = BooleanField('To Email :')
    role = SelectField('Role :')

    mode = HiddenField()

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.nilai.choices = [ ("", "ALL")]+ [(c.nilai_id, c.name) for c in Nilai.query.all()]
        self.enrollment.choices = [ ("", "ALL")]+ [(c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'ENROLLMENT_STATUS' ).all()]
        self.notification_type.choices = [ ("", "")] + [(c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'EMAIL_NOTIFICATION').all()]
        self.role.choices = [ ("", "ALL")]+ [(row.id, row.name) for row in Role.query.all()]

class SearchExamForm(Form):
    term = SelectField('Trimester :')

    def __init__(self, *args, **kwargs):
        super(SearchExamForm, self).__init__(*args, **kwargs)
        self.term.choices = [ (c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'EXAM_TERM' ).all()]


class MailSearchForm(Form):
    type = SelectField('Notification Type :')
    name = StringField('Name :')
    section = StringField('Class :')
    nilai = SelectField('Nilai :')
    paid = SelectField('Paid Status :', choices= [("", "ALL"), ('Y','Paid' ), ('N', 'Unpaid')] )
    enrollment = SelectField('Enrollment :' )
    new = BooleanField('New Students Only? :')
    inactive = BooleanField('Include InActive Students ? :')
    to_csv = BooleanField('To CSV :')
    to_email = BooleanField('To Email :')

    mode = HiddenField()

    def __init__(self, *args, **kwargs):
        super(MailSearchForm, self).__init__(*args, **kwargs)
        self.nilai.choices = [ ("", "ALL")]+ [(c.nilai_id, c.name) for c in Nilai.query.all()]
        self.enrollment.choices = [ (None, "ALL")]+ [(c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'ENROLLMENT_STATUS' ).all()]


# Define the User profile form
class UserProfileForm(FlaskForm):
#    id = HiddenField()
    father_name = StringField("Primary Parent/Guardian's Full Name(*) :", validators=[ DataRequired("Primary Parent/Guardian's Full Name is required")])
    mother_name = StringField("Secondary Parent/Guardian's Full Name(*) :", validators=[ DataRequired("Secondary Parent/Guardian's Full Name is required")])
    email = EmailField('Primary Email(*) :', validators=[ DataRequired('Primary email is required')])
    email2 = EmailField('Alternate Email(*) :', validators=[ DataRequired('Alternate email is required')])
    phone1 = TelField('Primary Contact Number(*) :', validators=[ DataRequired('Parmary Contact Number is required')])
    phone2 = TelField('Secondary Contact Number(*) :', validators=[ DataRequired('Secondory Contact Number is required')])
    parents_street_address = StringField("Parent/Guardian's Street Address(*) :", validators=[ DataRequired("Parent/Guardian's Street Address is required")])
    parents_street_address2 = StringField("Parent/Guardian's Street Address Line2(Apartment, Suite, Unit etc) :")
    parents_city = StringField("Parent/Guardian's Current City(*) :", validators=[ DataRequired("Parent/Guardian's Current City is required")])
    parents_state = StringField("Parent/Guardian's Current State(*) :", validators=[ DataRequired("Parent/Guardian's Current State is required")])
    parents_country = StringField("Parent/Guardian's Current Country(*) :", validators=[ DataRequired("Parent/Guardian's Current Country is required")])
    parents_zipcode = StringField("Parent/Guardian's Zip Code(*) :", validators=[ DataRequired("Parent/Guardian's Zip Code is required")])

    teaching_volunteer = SelectField('Are you interested in volunteering for teaching? No prior experience required :', default = 'No'  )
    teaching_dayntime = SelectField('Please select your preferred day and time :', default = 'No'  )
    teaching_grade = SelectField('Please select your preferred grade :', default = 'No'  )
    class_parent = SelectField("Are you interested to be a class parent for your child's class?", default = 'No' )
    reference = SelectField('How did you hear about us?(*) ', validators=[InputRequired()])
#    roles = SelectMultipleField('Role :', option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False), coerce = int )
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.teaching_volunteer.choices =  self.class_parent.choices = [('Y', 'Yes'), ('N', 'No') ]
        self.teaching_dayntime.choices =  self.class_parent.choices = [ ('NO', 'No'), ('Friday 6:30 PM EST', 'Friday 6:30 PM EST'), ('Saturday 12:00 PM EST', 'Saturday 12:00 PM EST'), ('Saturday 3:00 PM EST', 'Saturday 3:00 PM EST') ]
        self.teaching_grade.choices =  self.class_parent.choices = [ ('NO', 'No'), ('MUN MAZHALAI - MAZHALAI', 'MUN MAZHALAI - MAZHALAI'), ('GRADE 1 - GRADE 3', 'GRADE 1 - GRADE 3'), ('GRADE 4 - GRADE 8', 'GRADE 4 - GRADE 8') ]
        self.reference.choices = [ (c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'REFERENCE').all()]
#        self.roles.choices =  [(row.id, row.name) for row in Role.query.all()]


# Define the User profile form
class UserParentProfileForm( UserProfileForm ):
    roles = SelectMultipleField('Role :', option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False), coerce = int )

    def __init__(self, *args, **kwargs):
        super(UserParentProfileForm, self).__init__(*args, **kwargs)
        self.roles.choices =  [(row.id, row.name) for row in Role.query.all()]


class PaymentForm(Form):
    enrollment_id = HiddenField()
    student_name = StringField("Student Name",  render_kw={'readonly': True})
    nilai = StringField("Nilai",  render_kw={'readonly': True, "data-size": "mini"})
    section = StringField("Section",  render_kw={'readonly': True, "data-size": "mini"})
    enrollment_status = StringField("Enrollment Status", render_kw={'readonly': True })
    payment_status = StringField("Payment", render_kw={'readonly': True })
    start_year = IntegerField("Start Year", render_kw={'readonly': True})
    paid_amount = DecimalField("Amount", render_kw={'readonly': True})
    new_amount = DecimalField("Amount")
    check_no = StringField("Check No")
    due = DecimalField("Due",  render_kw={'readonly': True})
    discount_amount = DecimalField("Discount",  render_kw={'readonly': True})
    previous_balance = DecimalField("Previous Balance",  render_kw={'readonly': True})

class PaymentMainForm(Form):
    students = FieldList(FormField(PaymentForm), min_entries=0, max_entries=10)
    submit = SubmitField('Confirm')

# For books Delivery Tracking
class StudentForm(Form):
    enrollment_id = HiddenField()
    student_name = StringField("Student Name",  render_kw={'readonly': True})
    enrollment_status = StringField("Enrollment Status",  render_kw={'readonly': True })
    payment_status = StringField("Payment Status",  render_kw={'readonly': True })
    start_year = IntegerField("Start Year",  render_kw={'readonly': True})
    sex = StringField("Gender",  render_kw={'readonly': True})
    last_year_class = StringField("Last Year",  render_kw={'readonly': True})
    school_grade = IntegerField("School Grade",  render_kw={'readonly': True})
    nilai = StringField("Nilai",  render_kw={'readonly': True, "data-size": "mini"})
    section = StringField("Section")
    book_shipment_preference = StringField("Book Shipment Preference",  render_kw={'readonly': True})
    book_shipped_date = StringField("Book Shipped Date: ", default="MM-DD-YYYY")
    book_tracking_number = StringField("Book Tracking Number: ", default="MM-DD-YYYY")
    book_delivered_date = StringField("Book Delivered Date: ", default="MM-DD-YYYY")
    book_status = BooleanField("Book Delivered", false_values= ('false', '')  )


class StudentListForm(Form):
    students = FieldList(FormField(StudentForm), min_entries=0, max_entries=400)
    submit = SubmitField('Confirm')

class SelfEnrollForm(Form):
    enrollment_id = HiddenField()
    student_first_name = StringField("Student First Name",  render_kw={'readonly': True})
    student_last_name = StringField("Student Last Name",  render_kw={'readonly': True})
    student_name = StringField("Student Name",  render_kw={'readonly': True})
    student_name_tamil = StringField("Student Name in Tamil",  render_kw={'readonly': True} )
    age = StringField("Student Age",  render_kw={'readonly': True} )
    sex = StringField("Gender",  render_kw={'readonly': True})
    start_year = IntegerField("Start Year",  render_kw={'readonly': True})
    school_grade = StringField("School Grade",  render_kw={'readonly': True})
    enrollment_status = SelectField("Enrollment Status" )

    def __init__(self, *args, **kwargs):
        super(SelfEnrollForm, self).__init__(*args, **kwargs)
        self.enrollment_status.choices = [ (1, "ENROLL for 2024-25"), (3, "DISCONTINUE") ]


class SelfEnrollListForm(Form):
    students = FieldList(FormField(SelfEnrollForm), min_entries=0, max_entries=100)
    submit = SubmitField('Confirm Enrollment')

class StudentEditForm(Form):

    student_id = HiddenField()
    start_year = HiddenField()
    student_first_name = StringField("Student First Name (As in Birth Certificate) : *", validators=[ InputRequired("Student First Name is required")] )
    student_last_name = StringField("Student Last Name (As in Birth Certificate) : *", validators=[ InputRequired("Student Last Name is required")] )
    student_name = StringField("Student First and Last Name (As in Birth Certificate) : *", validators=[ InputRequired("Student First and last Name is required")] )
    student_name_tamil = StringField("Student Full Name in Tamil (You may use https://www.google.com/intl/ta/inputtools/try/ to get Tamil text) :")
    age = StringField("Student Age) :")
    student_email = EmailField("Student Email (Required for Google Classroom setup) :")
    sex = RadioField('Gender : *', choices = [ ('F','Female' ), ('M', 'Male') ], validators=[ InputRequired(message="Choose Male or Female")])
    birth_year = SelectField("Birth Year : *", coerce=int, validators=[ InputRequired("Birth Year is required")] )
    birth_month = SelectField("Birth Month : *", coerce=int, validators=[ InputRequired("Birth Month is required")] )
    school_grade = SelectField("School Grade : *", coerce=int, validators=[ InputRequired("Grade is required")])
    skill_level_joining = SelectMultipleField(
        'Skill Level While joining :',
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False))

    book_shipment_preference = SelectField('Please select your book shipment preference :', default = 'Group Shipment' )
    preferred_dayntime = SelectField('Please select your preferred day and time :', default = 'Friday 6:30 PM EST' )
    preferred_grade = SelectField('Please select your preferred grade :', default = 'MUN MAZHALAI'  )
    prior_tamil_school = TextAreaField('Prior Tamil School Experience :', widget=TextArea())
    submit = SubmitField('Confirm')

    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__( *args, **kwargs)
        self.academic_year = kwargs.get('academic_year')
        self.birth_month.choices = [ (0, "")] + [(month_idx, calendar.month_name[month_idx]) for month_idx in range(1, 13) ]
        self.birth_year.choices = [ (0, "")] + [(year, year) for year in range(self.academic_year - 40 , self.academic_year - 2) ]
        self.school_grade.choices = [ (99, "")] + [(int(c.category_key), c.category_value) for c in UIConfig.query.filter_by(category = 'SCHOOL_GRADE' ).all()]
        self.skill_level_joining.choices = [ ('Speak','Speak'), ('Read', 'Read'), ('Write','Write' ) ]
        self.book_shipment_preference.choices = [ ('Group','Group Shipment'), ('Individual', 'Individual Shipment') ]
        self.preferred_dayntime.choices =  self.preferred_dayntime.choices = [ ('Friday 6:30 PM EST', 'Friday 6:30 PM EST'), ('Saturday 12:00 PM EST', 'Saturday 12:00 PM EST'), ('Saturday 3:00 PM EST', 'Saturday 3:00 PM EST') ]
        self.preferred_grade.choices =  self.preferred_grade.choices = [ ('MUN MAZHALAI', 'MUN MAZHALAI'), ('MAZHALAI', 'MAZHALAI'),
                                                                      ('Nilai 1', 'Nilai 1'), ('Nilai 2', 'Nilai 2'),
                                                                      ('Nilai 3', 'Nilai 3'), ('Nilai 4', 'Nilai 4'),
                                                                      ('Nilai 5', 'Nilai 5'), ('Nilai 6', 'Nilai 6'),
                                                                      ('Nilai 7', 'Nilai 7'), ('Nilai 8', 'Nilai 8') ]


class EnrollmentEditForm(Form):
    enrollment_id = HiddenField()
    student_first_name = StringField("Student First Name",  render_kw={'readonly': True})
    student_last_name = StringField("Student Last Name",  render_kw={'readonly': True})
    student_name = StringField("Student Name",  render_kw={'readonly': True})
    start_year = IntegerField("Start Year",  render_kw={'readonly': True})
    last_year_class = StringField("Last Year Class",  render_kw={'readonly': True})
    school_grade = IntegerField("School Grade" )
    payment_status = StringField("Paid",  render_kw={'readonly': True }  )
    skill_level_joining = StringField("Skill Level While joining",  render_kw={'readonly': True})
    prior_tamil_school = TextAreaField('Prior Tamil School Experience', widget=TextArea(), render_kw={'readonly': True})
#    prior_tamil_school = StringField("Prior Tamil School Experience",  render_kw={'readonly': True})
    nilai = SelectField('Nilai',  coerce=int )
    enrollment_status = SelectField('Enrollment Status' )
    section = StringField("Class")
    discount_amount =  DecimalField("Discount Amount")
#    note =  StringField("Note")
#    note = TextAreaField('Note', widget=TextArea(), render_kw={'readonly': True})
    note = TextAreaField('Note', widget=TextArea() )

    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(EnrollmentEditForm, self).__init__(*args, **kwargs)
        self.nilai.choices = [ (c.nilai_id, c.name) for c in Nilai.query.all()]
        self.enrollment_status.choices = [ (c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'ENROLLMENT_STATUS' ).all()]

class ClassEditForm(Form):
    academic_year = HiddenField()
    section = StringField("Class :", validators=[ DataRequired("Section is required")])
    nilai_id = SelectField('Nilai :',  coerce=int )
    room = StringField("Room # :")
    teacher1_id = SelectField('Teacher 1 :',  coerce=int )
    teacher2_id = SelectField('Teacher 2 :',  coerce=int )
    teacher3_id = SelectField('Teacher 3 :',  coerce=int )
    class_day   = SelectField('Day of Class :' )
    class_start_time = TimeField("Class Start Time :", validators=[ InputRequired("Input Required")])
    class_email = StringField("Class Email :")
    teacher_view = RadioField('Teacher View :', default = 'No', coerce=int )
    parent_view  = RadioField('Parent View :' , default = 'No', coerce=int )

    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(ClassEditForm, self).__init__(*args, **kwargs)
        self.nilai_id.choices = [ (c.nilai_id, c.name) for c in Nilai.query.all()]
        self.teacher1_id.choices = [(-1, "")]+[ (u.id, u.father_name) for u in User.query.join(UserRole, Role).
                                                      filter(Role.name =='teacher').order_by(User.father_name ).all()]
        self.teacher3_id.choices = self.teacher2_id.choices = self.teacher1_id.choices
        self.teacher_view.choices = self.parent_view.choices = [(1, 'Yes'), (0, 'No') ]
        self.class_day.choices = [ (day, day) for day in weekday_list("Monday") ]


class CalendarForm(Form):
    school_date = DateField("Week Date",  render_kw={'readonly': True})
    is_session = BooleanField("In Session", false_values= ('false', 0)  )
    attendance_required = BooleanField("Attendence Required", false_values= ('false', 0)  )
    note = StringField("Note")

class CalendarMainForm(Form):
    calendar = FieldList(FormField(CalendarForm), min_entries=0, max_entries=50)
    submit = SubmitField('Confirm')

class AttendanceForm(Form):
    school_date = HiddenField()
    enrollment_id = HiddenField()
    attendance_status_previous = HiddenField()
    note_previous = HiddenField()
    section = HiddenField()

    student_name = StringField("Student Name", render_kw={'readonly': True})
    attendance_status = RadioField('Attendance', default = None,
                     choices = [ (2,'Present' ), (3, 'Tardy-Informed'), (4, 'Tardy-UnInformed'), (0, 'Absent-Informed'), (1, 'Absent-Uninformed') ], validators=[ Required(message="Attendance is required")])
    note = StringField("Note")

class AttendanceMainForm(Form):
    attendance = FieldList(FormField(AttendanceForm), min_entries=0, max_entries=30)
    submit = SubmitField('Confirm')

class HomeworkForm(Form):
    lesson_no = HiddenField()
    enrollment_id = HiddenField()
    homework_type = HiddenField()
    homework_status_previous = HiddenField()
    homework_score_previous = HiddenField()
    note_previous = HiddenField()
    section = HiddenField()

    student_name = StringField("Student Name", render_kw={'readonly': True})
    homework_status = BooleanField("status", false_values= ('false', 0)  )
    note = StringField("Note")

class HomeworkMainForm(Form):
    homework_date =  SelectField("", coerce = str)
    homework_date_previous = HiddenField()
    homework = FieldList(FormField(HomeworkForm), min_entries=0, max_entries=30)
    submit = SubmitField('Confirm')

    def __init__(self, *args, **kwargs):
        super(HomeworkMainForm, self).__init__(*args, **kwargs)
        self.homework_date.choices = [(c.school_date.strftime('%Y-%m-%d'), c.school_date.strftime('%Y-%m-%d') ) for c in SchoolCalendar.query.filter(SchoolCalendar.is_session == 1)
                .filter(SchoolCalendar.school_date <= date.today()).order_by(SchoolCalendar.school_date.desc()).all()]


class ExamForm(Form):
    enrollment_id = HiddenField()
    trimester_id = HiddenField()
    exam_score_previous = HiddenField()
    written_score_previous = HiddenField()
    oral_score_previous = HiddenField()
    listening_eval_previous = HiddenField()
    speaking_eval_previous  = HiddenField()
    reading_eval_previous   = HiddenField()
    writing_eval_previous   = HiddenField()
    note_previous = HiddenField()
    is_ptm_completed_previous = HiddenField()
    ptm_completed_date_previous = HiddenField()
    academic_year = HiddenField()

    section = StringField("Section", render_kw={'readonly': True})
    student_name = StringField("Student Name", render_kw={'readonly': True})
    written_score = DecimalField("Written", validators=[NumberRange(min=0, max=100, message='Only in numeric and score cannot exceed 100')] )
    oral_score = DecimalField("Oral", validators=[NumberRange(min=0, max=100, message='Only in numeric and score cannot exceed 100')] )
    exam_score = DecimalField("Score", render_kw={'readonly': True}, validators=[NumberRange(min=0, max=100, message='Only in numeric and score cannot exceed 100')] )
    listening_eval = SelectField('', render_kw={'rows': 1, 'cols': 30 }, coerce=int)
    speaking_eval = SelectField('', render_kw={'rows': 1, 'cols': 30 }, coerce=int)
    reading_eval = SelectField('', render_kw={'rows': 1, 'cols': 30 }, coerce=int)
    writing_eval = SelectField('', render_kw={'rows': 1, 'cols': 30 }, coerce=int)
#    note = StringField("Note")
    note = TextAreaField('Note', widget=TextArea())
    is_ptm_completed = BooleanField("", false_values= ('false', 0)  )
    ptm_completed_date =  SelectField("",  render_kw={'rows': 1, 'cols': 30 }, coerce = str)

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        self.listening_eval.choices = [ (c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'EVALUATION_LEVEL' ).all()]
        self.speaking_eval.choices = self.reading_eval.choices = self.writing_eval.choices = self.listening_eval.choices
        self.ptm_completed_date.choices = [ ("", "")] + [(c.school_date.strftime('%Y-%m-%d'), c.school_date.strftime('%Y-%m-%d') ) for c in SchoolCalendar.query.filter(SchoolCalendar.is_session == 1)
            .filter(SchoolCalendar.academic_year == session["ACADEMIC_YEAR"]).filter(SchoolCalendar.school_date <= date.today()).order_by(SchoolCalendar.school_date.desc()).all()]


class ExamMainForm(Form):
    exam_date = SelectField("", coerce = str)
    exam_date_previous = HiddenField()
    exam = FieldList(FormField(ExamForm), min_entries=0, max_entries=30)
    submit = SubmitField('Confirm')

    def __init__(self, *args, **kwargs):
        super(ExamMainForm, self).__init__(*args, **kwargs)
        self.exam_date.choices = [(c.school_date.strftime('%Y-%m-%d'), c.school_date.strftime('%Y-%m-%d') ) for c in SchoolCalendar.query.filter(SchoolCalendar.is_session == 1)
            .filter(SchoolCalendar.academic_year == session["ACADEMIC_YEAR"]).filter(SchoolCalendar.school_date <= date.today()).order_by(SchoolCalendar.school_date.desc()).all()]


class StudentNameForm(Form):
    student_id = HiddenField()
    student_name_previous = HiddenField()
    student_email_previous = HiddenField()
    section = StringField("Section", render_kw={'readonly': True})
    student_name = StringField("Student Name", render_kw={'readonly': True})
    student_name_tamil = StringField("Student Name in Tamil")
    age = StringField("Student Age")
    student_email = EmailField("Student's Email")

class StudentNameMainForm(Form):
    students = FieldList(FormField(StudentNameForm), min_entries=0, max_entries=30)
    submit = SubmitField('Confirm')

class EmailListForm(Form):
    primary_emails = TextAreaField('Primary Emails', render_kw={'readonly': True, 'rows': 10, 'cols': 80})
    secondary_emails = TextAreaField('Secondary Emails', render_kw={'readonly': True, 'rows': 10, 'cols': 80})

class EnrollConfirmationForm(Form):
    enroll_ids = HiddenField()
    enroll_statuses = HiddenField()
    start_years = HiddenField()
    student_names = HiddenField() # StringField("Student Name(s) : ", render_kw={'readonly': True})
    waiver = TextAreaField('Waiver Policy :', render_kw={'readonly': True, 'rows': 5, 'cols': 100, 'style':'white-space:pre-wrap;' } )
    agreement = TextAreaField('Terms and Conditions :', render_kw={'readonly': True, 'rows': 12, 'cols': 100, 'style':'white-space:pre-wrap;' } )
    consent_signed_by = StringField("Parent/Guardian's Full Name : *",  validators=[ InputRequired("Parent/Guardian name is required")] )
    consent_dated = StringField("Date Submitted : ", render_kw={'readonly': True})
    is_consent_signed = BooleanField("I understand and agree the above Terms and Conditions *", false_values= ('false', 0) ,  validators=[ InputRequired("Click to proceed")] )
    is_waiver_signed = BooleanField("I understand and agree the above Waiver Policy *", false_values= ('false', 0) ,  validators=[ InputRequired("Click to proceed")] )
    submit = SubmitField('Confirm')

class ProfileForm(FlaskForm):
    id = HiddenField()
    role_previous = HiddenField()

    father_name = StringField("", render_kw={'readonly': True})
    mother_name = StringField("", render_kw={'readonly': True})
    email = StringField("", render_kw={'readonly': True})
    email2 = StringField("", render_kw={'readonly': True})
    phone1 = StringField("", render_kw={'readonly': True})
    phone2 = StringField("", render_kw={'readonly': True})
    role = SelectMultipleField( option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False), coerce = int )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.role.choices =  [(row.id, row.name) for row in Role.query.all()]

class ProfileMainForm(Form):
    profile = FieldList(FormField(ProfileForm), min_entries=0, max_entries=300)
    submit = SubmitField('Confirm')

class OrderTrackingEditForm(Form):
    order_id = HiddenField()
#    type = SelectField('Type')
    type = StringField("Type :", render_kw={'readonly': True})

    order_status = SelectField('Order Status :')
    order_date = DateField('Order Date :')
    nilai_A = IntegerField("Mun Mazhalai :" )
    nilai_0 = IntegerField("Mazhalai :" )
    nilai_1 = IntegerField("Nilai 1 :" )
    nilai_2 = IntegerField("Nilai 2 :" )
    nilai_3 = IntegerField("Nilai 3 :" )
    nilai_4 = IntegerField("Nilai 4 :" )
    nilai_5 = IntegerField("Nilai 5 :" )
    nilai_6 = IntegerField("Nilai 6 :" )
    nilai_7 = IntegerField("Nilai 7 :" )
    nilai_8 = IntegerField("Nilai 8 :" )
    note =  StringField("Note :")
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(OrderTrackingEditForm, self).__init__(*args, **kwargs)
#        self.type.choices = [ (c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'BOOK_ORDER_TYPE').all()]
        self.order_status.choices = [ (c.category_key, c.category_value) for c in UIConfig.query.filter_by(category = 'BOOK_ORDER_STATUS').all()]


class AcademicYearForm(Form):
    year = RadioField('Academic Year :', coerce=int )
    submit = SubmitField('Confirm')

    def __init__(self, *args, **kwargs):
        super(AcademicYearForm, self).__init__(*args, **kwargs)
        self.year.choices = [ (c.academic_year, c.academic_year_label) for c in SchoolYear.query.all()]

class ClassTrackingForm(FlaskForm):
    academic_year = HiddenField()
    school_date = HiddenField()
    section = HiddenField()
    mode = HiddenField()
    class_date = DateField("Actual Class Date : *", format='%Y-%m-%d' , validators=[ InputRequired("Input Required")])
    class_start_time = TimeField("Class Start Time :" , validators=[ InputRequired("Input Required")])
    class_end_time = TimeField("Class End Time :" , validators=[ InputRequired("Input Required")])
    teacher1_id = SelectField('Teacher 1 : *', coerce=int )
    teacher2_id = SelectField('Teacher 2 : *', coerce=int )
    substitute_teacher = StringField("Substitute Teacher(s) :" )
    lesson_no = SelectField("Lesson # Completed : " , coerce=int)
    class_activities = TextAreaField('Class Activities : *', widget=TextArea() , validators=[ InputRequired("Input Required")] )
    homework_paper = TextAreaField('Homework Assigned : *', widget=TextArea() , validators=[ InputRequired("Input Required")] )
    homework_audio = TextAreaField('Project  Assigned : *', widget=TextArea() , validators=[ InputRequired("Input Required")] )

#    homework_paper = StringField("Homework Assigned : *" , validators=[ InputRequired("Input Required")] )
#    homework_audio = StringField("Project  Assigned : *" , validators=[ InputRequired("Input Required")] )

    note_to_parents = TextAreaField('Note To Parent(s) :', widget=TextArea())
    note_to_admin = TextAreaField('Note To Admin Team :', widget=TextArea())
    note_from_admin = TextAreaField('Response From Admin Team :', widget=TextArea(), render_kw={'readonly': True})
    volunteers_present = StringField("Volunteer Name(s) :" )
    volunteers_activities = TextAreaField('Volunteer(s) Activities :', widget=TextArea())
    is_email_sent = BooleanField("Email sent to Parent(s)? ", false_values= ('false', 0) ,  render_kw={'readonly': True} )

    email_sent_date = Date_Field("Email Sent Date : ",  render_kw={'readonly': True},  format='%m-%d-%Y', validators=[Optional()] )

    save = SubmitField('Save')
    email = SubmitField('Publish')

    def __init__(self, *args, **kwargs):
        super(ClassTrackingForm, self).__init__(*args, **kwargs)
        self._section = kwargs.get('section')
        self._academic_year = kwargs.get('academic_year')

        self.lesson_no.choices = [ (-1, "")]+ [(c.lesson_no, c.lesson_no) for c in Lesson.query.filter(Lesson.academic_year == self._academic_year ).all() ]
        section_row = Section.query.filter(Section.section == self._section).filter(Section.academic_year == self._academic_year ).first()
        teacher_list = [ section_row.teacher1_id]
        if section_row.teacher2_id :
            teacher_list.append( section_row.teacher2_id )
        if section_row.teacher3_id :
            teacher_list.append( section_row.teacher3_id )

        self.teacher1_id.choices = [ (u.id, u.father_name) for u in User.query.join(UserRole, Role).
                                                      filter(Role.name =='teacher').filter(User.id.in_( teacher_list )).order_by(User.father_name ).all()]
        self.teacher2_id.choices = [(-1, "")] + self.teacher1_id.choices


class UIConfigForm(FlaskForm):
    id = HiddenField()
    category = StringField("Category", render_kw={'readonly': True })
    category_key = StringField("Category Key:", validators=[ DataRequired("Category Key is required")])
    category_value = StringField("Category Value:", validators=[ DataRequired("Category Value is required")])
    order_by  = IntegerField("Display Order" )
    active = RadioField('Is Active ?', default = 'Yes', coerce=int,  choices = [ (1,'Yes' ), (0, 'No') ] )

    submit = SubmitField('Save')

def weekday_list(weekday_start):
    start = [d for d in calendar.day_name].index(weekday_start)
    return [calendar.day_name[(i+start) % 7] for i in range(7)]


class SchoolYearForm(FlaskForm):
    academic_year =  IntegerField("Academic Year" )
    academic_year_label =  StringField("Academic Year Label" )
    start_date = DateField("School Start Date : *", format='%Y-%m-%d' , validators=[ InputRequired("Input Required")])
    end_date = DateField("Tentative School End Date : *", format='%Y-%m-%d' , validators=[ InputRequired("Input Required")])
    school_start_time = TimeField("Class Start Time :" , validators=[ InputRequired("Input Required")])
    school_day   = SelectField('Day of Class :' )

    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(SchoolYearForm, self).__init__(*args, **kwargs)
        self.school_day.choices = [ (day, day) for day in weekday_list("Monday") ]

# Define the Service Request New form
class ServiceRequestUpdateForm(FlaskForm):
    record = HiddenField()
    email = EmailField('APS Admin Team Email(*) :')
    created_by = EmailField('Submitted By Email(*) :')
    created_for = EmailField('This Service Request for(email id) :')
    service_type = StringField("Service Type : ")
    service_id = StringField('Service Request #:')
    service_description = TextAreaField('Description :', render_kw={'rows': 3, 'cols': 60 })
    response = TextAreaField('Admin Team Response :', render_kw={'rows': 3, 'cols': 60 })
    close = BooleanField('Close the Service Request :')
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ServiceRequestUpdateForm, self).__init__(*args, **kwargs)


# Define the Service Request New form
class ServiceRequestNewForm(FlaskForm):
    email = EmailField('Submitter Email(*) :', render_kw={'readonly': True })
    # created_for = EmailField('This Service Request for (student APS email id) :', render_kw={'readonly': True })
    created_for = TextAreaField('This Service Request for (student APS email id) :', widget=TextArea())
    service_type = SelectField("Service Type : ")
    service_description = TextAreaField('Description :', widget=TextArea(), validators=[ DataRequired('Description is required')])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ServiceRequestNewForm, self).__init__(*args, **kwargs)
        self.service_type.choices = [ ("Others", 'Others'), ('Enrollment:2023-24', 'Enroll student for 2023-2024'), \
                                      ("Payment", 'Payment Issues'), ("Leave - Teacher", 'Leave Notification - Teacher'),  ("Leave - Student", 'Leave Notification - Student'), \
                                      ("Volunteer-Teacher", 'Volunteer(Teacher) - Enrollment'), ("Volunteer-Admin", 'Volunteer(Admin) - Enrollment'), \
                                      ("Volunteer-Discount", 'Claim 40% Discount - Volunteer(Teacher)'), \
                                      ("Discontinue", 'Discontinue'), ("Class Time Change", 'Class time change request'), \
                                      ("Books", 'Regarding Books'), \
                                      ("Google Class Room/Meet", 'Google Class Room/Meet Issue(s)'), \
                                      ("MyAPS", 'MyAPS Issues/Improvements')]

# Define the Annual Day Signup form
class ServiceRequestAnnualDaySignupForm(FlaskForm):
    email = EmailField('Email(*) :', validators=[ DataRequired('Email is required'), Email()])
    student_email = EmailField('APS Student Email(*) :', validators=[ DataRequired('APS email is required'), Email()])
    # email = EmailField('APS Email(*) :', [InputRequired("Please enter your email address."), Email("This field requires a valid email address")])
    time_slot = SelectField("TimeSlot : ")
    events = SelectField("Event : ")
    # events = SelectMultipleField(
    #                    'Events(*) : ',
    #                    option_widget=CheckboxInput(),
    #                    widget=ListWidget(prefix_label=False),
    #                    validators=[ InputRequired("Input Required")])
    comments = TextAreaField('Comment(s) :', widget=TextArea())
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ServiceRequestAnnualDaySignupForm, self).__init__(*args, **kwargs)
        self.time_slot.choices = [("1", "6:00-6:15 PM"), ("2", "6:15-6:30 PM"), ("3", "6:30-6:45 PM"),]
        # myevents = ServiceRequestAnnualDay.query(ServiceRequestAnnualDay.events).filter_by(ServiceRequestAnnualDay.user_id)
        # self.events.choices = [ (row.events, row.events) for row in ServiceRequestAnnualDay.query.filter_by(user_id == User.id) ]
        self.events.choices = [("AD01-MAATHIYOSI","MaaththiYosi (மாத்தியோசி)"),\
                               ("AD02-ORUSOL","Oru Vaarthai Oru Sol (வார்த்தை/ சொல் விளையாட்டு)"), \
                               ("AD03-THIRUKURAL-AATHICHUDI","Thirukural Aathichudi Picture Competition (திருக்குறள் ஆத்திச்சூடி படப் போட்டி)"), \
                               ("AD04-THAMIZHIL-URAIYADU-TEACHERS-ONLY", "Thamizhil Uraiyadu (தமிழில் உரையாடு - ஆசிரியர்களுக்கான போட்டி)"), \
                               ("AD06-THAMIZHODU_VILAYAADU", "Thamizhodu Vilayaadu (தமிழோடு விளையாடு)")]

# Define the Annual Day Registration form
class ServiceRequestAnnualDayForm(FlaskForm):
    email = EmailField('Email(*) :', validators=[ DataRequired('Email is required'), Email()])
    student_email = EmailField('APS Student Email(*) :', validators=[ DataRequired('APS email is required'), Email()])
    # email = EmailField('APS Email(*) :', [InputRequired("Please enter your email address."), Email("This field requires a valid email address")])
    events = SelectMultipleField(
                        'Events(*) : ',
                        option_widget=CheckboxInput(),
                        widget=ListWidget(prefix_label=False),
                        validators=[ InputRequired("Input Required")])
    comments = TextAreaField('Comment(s) :', widget=TextArea())
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ServiceRequestAnnualDayForm, self).__init__(*args, **kwargs)
        # self.skill_level_joining.choices = [ ('Speak','Speak'), ('Read', 'Read'), ('Write','Write' ) ]
        self.events.choices = [("AD01-MAATHIYOSI","MaaththiYosi (மாத்தியோசி)"),\
                               ("AD02-ORUSOL","Oru Vaarthai Oru Sol (வார்த்தை/ சொல் விளையாட்டு)"), \
                               ("AD03-THIRUKURAL-AATHICHUDI","Thirukural Aathichudi Picture Competition (திருக்குறள் ஆத்திச்சூடி படப் போட்டி)"), \
                               ("AD04-THAMIZHIL-URAIYADU-TEACHERS-ONLY", "Thamizhil Uraiyadu (தமிழில் உரையாடு - ஆசிரியர்களுக்கான போட்டி)"),\
                               ("AD05-FANCYDRESS","Fancy Dress Competition (மாறுவேடப் போட்டி)"),\
                               ("AD06-THAMIZHODU_VILAYAADU", "Thamizhodu Vilayaadu (தமிழோடு விளையாடு)"),\
                               ("AD07-CLASS-EVENT", "Class Participation (ஓர் வகுப்பு - ஓர் நிகழ்ச்சி)")]

# Define the admin form
class ServiceRequestAdminForm(FlaskForm):
    to_csv = BooleanField('To CSV :')
    to_csv_service = BooleanField('To CSV :')
    filter_by = SelectField('Filter By')
    refresh = SelectField('refresh')
    submit = SubmitField('Download Service Request(s)')
    submit_registrations = SubmitField('Download Registration(s)')

    def __init__(self, *args, **kwargs):
        super(ServiceRequestAdminForm, self).__init__(*args, **kwargs)
        self.filter_by.choices = [ ("Others", 'Others'), ('Enrollment:2023-24', 'Enroll student for 2023-2024'), \
                                      ("Payment", 'Payment Issues'), ("Leave - Teacher", 'Leave Notification'),  ("Leave - Student", 'Leave Notification'), \
                                      ("Volunteer-Teacher", 'Volunteer(Teacher) - Enrollment'), ("Volunteer-Admin", 'Volunteer(Admin) - Enrollment'), \
                                      ("Volunteer-Discount", 'Claim 40% Discount - Volunteer(Teacher)'), \
                                      ("Discontinue", 'Discontinue'), ("Class Time Change", 'Class time change request'), \
                                      ("Books", 'Regarding Books'), \
                                      ("Google Class Room/Meet", 'Google Class Room/Meet Issue(s)'), \
                                      ("MyAPS", 'MyAPS Issues/Improvements')]



# Define the FeedbackForm
class ServiceRequestFeedbackForm(FlaskForm):
    email = EmailField('Email(*) :', validators=[ DataRequired('Email is required'), Email()])
    # email = EmailField('APS Email(*) :', [InputRequired("Please enter your email address."), Email("This field requires a valid email address")])
    teach_exp = SelectField("1. How was your experience working as a volunteer teacher? (in a 10 number scale, 1 the lowest and 10 the highest)", default=10)
    teach_cont = SelectField("2. Would you continue to volunteer for next academic year 2024-25 for same grade/Nilai?")
    teach_grade = SelectField("3. what Grade/Nilai would you be comfortable handling for next academic year 2023-24")
    teach_rec = SelectField("4. How likely you recommend APS to your family or friends to volunteer as a teacher(s)?");
    teach_ref = TextAreaField("5. Have you referred any teacher volunteer(s) in the academic year 2023-24?. If yes please mention their name(s)", widget=TextArea())
    teach_ref_stud = SelectField("6. How likely you recommend APS to your family or friends as a student to enroll and study tamil?")
    # events = SelectMultipleField(
    #                    'Events(*) : ',
    #                    option_widget=CheckboxInput(),
    #                    widget=ListWidget(prefix_label=False),
    #                    validators=[ InputRequired("Input Required")])
    comments = TextAreaField('7. Any comments or feedback to APS Management team?:', widget=TextArea())
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ServiceRequestFeedbackForm, self).__init__(*args, **kwargs)
        self.teach_exp.choices = [("10", "10"), ("9", "9"), ("8", "8"),  ("7", "7"), ("6", "6"), ("5", "5"), ("4", "4"), ("3", "3"), ("2", "2"), ("1", "1")]
        self.teach_cont.choices = [("Yes", "Yes"),("No", "No"), ("Maybe", "Maybe")]
        self.teach_grade.choices = [("N/A", "N/A"), ("NotTeaching", "Not Teaching(2023-24)"), ("Mun Mazhalai", "Mun Mazhalai"), ("Mazhalai", "Mazhalai"), ("1", "Grade/Nilai 1"), ("2", "Grade/Nilai 2"), ("3", "Grade/Nilai 3"), ("4", "Grade/Nilai 4"), ("5", "Grade/Nilai 5"), ("6", "Grade/Nilai 6"), ("7", "Grade/Nilai 7"), ("8", "Grade/Nilai 8") ]
        self.teach_rec.choices = [("Yes.IRecommend", "Yes. I Recommend"), ("No.IDonotRecommend", "No. I donot Recommend"), ("Not Sure", "Not Sure"), ("Maybe", "Maybe")]
        self.teach_ref_stud.choices = [("Yes.IRecommend", "Yes. I Recommend"), ("No.IDonotRecommend", "No. I donot Recommend"), ("Not Sure", "Not Sure"), ("Maybe", "Maybe")]
        # myevents = ServiceRequestAnnualDay.query(ServiceRequestAnnualDay.events).filter_by(ServiceRequestAnnualDay.user_id)
        # self.events.choices = [ (row.events, row.events) for row in ServiceRequestAnnualDay.query.filter_by(user_id == User.id) ]

# Define the FeedbackForm
class PrizeAddForm(FlaskForm):
    winner_name = StringField('Full Name(*) : ')
    winner_email = EmailField('APS Email(*) : ', validators=[ DataRequired('Email is required'), Email()])
    winner_place = SelectField("Event(*) : ")
    parent_email = EmailField('Personal Email(*) : ', validators=[ DataRequired('Email is required'), Email()])
    prize_amount = StringField("Amount(*) : ")
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PrizeAddForm, self).__init__(*args, **kwargs)
        # self.event.choices = [("AnnualDay-2023", "AnnualDay-2023"),("Pongal-2023", "Pongal-2023"), ("Other", "Other")]
        self.winner_place.choices = [("AcademicYear-2022-23-Volunteer-discount", "AcademicYear-2022-23-Volunteer-discount"), \
                                     ("AnnualDay-2023-Arumbu-Oviyam-1stPlace", "AnnualDay-2023-Arumbu-Oviyam-1stPlace"), \
                                     ("AnnualDay-2023-Arumbu-Oviyam-2ndPlace", "AnnualDay-2023-Arumbu-Oviyam-2ndPlace"), \
                                     ("AnnualDay-2023-Arumbu-Oviyam-3rdPlace", "AnnualDay-2023-Arumbu-Oviyam-3rdPlace"), \
                                     ("AnnualDay-2023-Arumbu-Kathai-1stPlace", "AnnualDay-2023-Arumbu-Kathai-1stPlace"), \
                                     ("AnnualDay-2023-Arumbu-Kathai-2ndPlace", "AnnualDay-2023-Arumbu-Kathai-2ndPlace"), \
                                     ("AnnualDay-2023-Arumbu-Kathai-3rdPlace", "AnnualDay-2023-Arumbu-Kathai-3rdPlace"), \
                                     ("AnnualDay-2023-Arumbu-MaruVedam-1stPlace", "AnnualDay-2023-Arumbu-MaruVedam-1stPlace"), \
                                     ("AnnualDay-2023-Arumbu-MaruVedam-2ndPlace", "AnnualDay-2023-Arumbu-MaruVedam-2ndPlace"), \
                                     ("AnnualDay-2023-Arumbu-MaruVedam-3rdPlace", "AnnualDay-2023-Arumbu-MaruVedam-3rdPlace"), \
                                     ("AnnualDay-2023-Arumbu-Oviyam-Consolation-I", "AnnualDay-2023-Arumbu-Oviyam-Consolation-I"), \
                                     ("AnnualDay-2023-Arumbu-Oviyam-Consolation-II", "AnnualDay-2023-Arumbu-Oviyam-Consolation-II"), \
                                     ("AnnualDay-2023-Arumbu-Oviyam-Consolation-III", "AnnualDay-2023-Arumbu-Oviyam-Consolation-III"), \
                                     ("AnnualDay-2023-Arumbu-Kathai-Consolation-I", "AnnualDay-2023-Arumbu-Kathai-Consolation-I"), \
                                     ("AnnualDay-2023-Arumbu-Kathai-Consolation-II", "AnnualDay-2023-Arumbu-Kathai-Consolation-II"), \
                                     ("AnnualDay-2023-Arumbu-Kathai-Consolation-III", "AnnualDay-2023-Arumbu-Kathai-Consolation-III"), \
                                     ("AnnualDay-2023-Arumbu-MaruVedam-Consolation-I", "AnnualDay-2023-Arumbu-MaruVedam-Consolation-I"), \
                                     ("AnnualDay-2023-Arumbu-MaruVedam-Consolation-II", "AnnualDay-2023-Arumbu-MaruVedam-Consolation-II"), \
                                     ("AnnualDay-2023-Arumbu-MaruVedam-Consolation-III", "AnnualDay-2023-Arumbu-MaruVedam-Consolation-III"), \
                                     ("AnnualDay-2023-Mottu-Song-1stPlace", "AnnualDay-2023-Mottu-Song-1stPlace"), \
                                     ("AnnualDay-2023-Mottu-Song-2ndPlace", "AnnualDay-2023-Mottu-Song-2ndPlace"), \
                                     ("AnnualDay-2023-Mottu-Song-3rdPlace", "AnnualDay-2023-Mottu-Song-3rdPlace"), \
                                     ("AnnualDay-2023-Mottu-Speech-1stPlace", "AnnualDay-2023-Mottu-Speech-1stPlace"), \
                                     ("AnnualDay-2023-Mottu-Speech-2ndPlace", "AnnualDay-2023-Mottu-Speech-2ndPlace"), \
                                     ("AnnualDay-2023-Mottu-Speech-3rdPlace", "AnnualDay-2023-Mottu-Speech-3rdPlace"), \
                                     ("AnnualDay-2023-Mottu-Dance-1stPlace", "AnnualDay-2023-Mottu-Dance-1stPlace"), \
                                     ("AnnualDay-2023-Mottu-Dance-2ndPlace", "AnnualDay-2023-Mottu-Dance-2ndPlace"), \
                                     ("AnnualDay-2023-Mottu-Dance-3rdPlace", "AnnualDay-2023-Mottu-Dance-3rdPlace"), \
                                     ("AnnualDay-2023-Mottu-Song-Consolation-I", "AnnualDay-2023-Mottu-Song-Consolation-I"), \
                                     ("AnnualDay-2023-Mottu-Song-Consolation-II", "AnnualDay-2023-Mottu-Song-Consolation-II"), \
                                     ("AnnualDay-2023-Mottu-Song-Consolation-III", "AnnualDay-2023-Mottu-Song-Consolation-III"), \
                                     ("AnnualDay-2023-Mottu-Speech-Consolation-I", "AnnualDay-2023-Mottu-Speech-Consolation-I"), \
                                     ("AnnualDay-2023-Mottu-Speech-Consolation-II", "AnnualDay-2023-Mottu-Speech-Consolation-II"), \
                                     ("AnnualDay-2023-Mottu-Speech-Consolation-III", "AnnualDay-2023-Mottu-Speech-Consolation-III"), \
                                     ("AnnualDay-2023-Mottu-Dance-Consolation-I", "AnnualDay-2023-Mottu-Dance-Consolation-I"), \
                                     ("AnnualDay-2023-Mottu-Dance-Consolation-II", "AnnualDay-2023-Mottu-Dance-Consolation-II"), \
                                     ("AnnualDay-2023-Mottu-Dance-Consolation-III", "AnnualDay-2023-Mottu-Dance-Consolation-III"), \
                                     ("AnnualDay-2023-Malar-Essay-1stPlace", "AnnualDay-2023-Malar-Essay-1stPlace"), \
                                     ("AnnualDay-2023-Malar-Essay-2ndPlace", "AnnualDay-2023-Malar-Essay-2ndPlace"), \
                                     ("AnnualDay-2023-Malar-Essay-3rdPlace", "AnnualDay-2023-Malar-Essay-3rdPlace"), \
                                     ("AnnualDay-2023-Malar-Speech-1stPlace", "AnnualDay-2023-Malar-Speech-1stPlace"), \
                                     ("AnnualDay-2023-Malar-Speech-2ndPlace", "AnnualDay-2023-Malar-Speech-2ndPlace"), \
                                     ("AnnualDay-2023-Malar-Speech-3rdPlace", "AnnualDay-2023-Malar-Speech-3rdPlace"), \
                                     ("AnnualDay-2023-Malar-Dance-1stPlace", "AnnualDay-2023-Malar-Dance-1stPlace"), \
                                     ("AnnualDay-2023-Malar-Dance-2ndPlace", "AnnualDay-2023-Malar-Dance-2ndPlace"), \
                                     ("AnnualDay-2023-Malar-Dance-3rdPlace", "AnnualDay-2023-Malar-Dance-3rdPlace"), \
                                     ("AnnualDay-2023-Malar-Essay-Consolation-I", "AnnualDay-2023-Malar-Essay-Consolation-I"), \
                                     ("AnnualDay-2023-Malar-Essay-Consolation-II", "AnnualDay-2023-Malar-Essay-Consolation-II"), \
                                     ("AnnualDay-2023-Malar-Essay-Consolation-III", "AnnualDay-2023-Malar-Essay-Consolation-III"), \
                                     ("AnnualDay-2023-Malar-Speech-Consolation-I", "AnnualDay-2023-Malar-Speech-Consolation-I"), \
                                     ("AnnualDay-2023-Malar-Speech-Consolation-II", "AnnualDay-2023-Malar-Speech-Consolation-II"), \
                                     ("AnnualDay-2023-Malar-Speech-Consolation-III", "AnnualDay-2023-Malar-Speech-Consolation-III"), \
                                     ("AnnualDay-2023-Malar-Dance-Consolation-I", "AnnualDay-2023-Malar-Dance-Consolation-I"), \
                                     ("AnnualDay-2023-Malar-Dance-Consolation-II", "AnnualDay-2023-Malar-Dance-Consolation-II"), \
                                     ("AnnualDay-2023-Malar-Dance-Consolation-III", "AnnualDay-2023-Malar-Dance-Consolation-III"), \
                                     ("Other", "Other")]


class TheduForm(FlaskForm):
    name = StringField('Full Name : ')
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        super(FlaskForm, self).__init__(*args, **kwargs)



