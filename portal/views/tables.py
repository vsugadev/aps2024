
from flask_table import Table, Col, LinkCol  #, BoolCol

align_center = {"style":"text-align:center" }

class Results_Payment(Table):
    student_id = Col('student_id', show=False)
    parent_id  = Col('parent_id', show=False)
    student_name = Col('Student Name')
    father_name = Col('Parent 1')
    mother_name = Col('Parent 2')
    start_year = Col('Start Year')
    last_year_class = Col('Last Year Class')
    nilai = Col('Nilai')
    section = Col('Class')
    enrollment_status = Col('Enroll Status')
    payment_status = Col('Paid?')
    previous_balance = Col('Pre. Bal')
    due_amount = Col('Due Amount')
    discount_amount = Col('Discount')
    paid_amount = Col('Paid Amount')
    paid_date = Col('Paid Date')
    check_no = Col('Reference')
    edit = LinkCol('Make Payment', 'payment.student_payment_view', url_kwargs=dict(id_str='parent_id'))

class Results_Enrollment(Table):
    enrollment_id = Col('enrollment_id', show=False)
    link_id = Col('link_id', show=False)
    parent_id  = Col('parent_id', show=False)
#    student_name = Col('Student Name')
    student_edit = LinkCol('Student Name', 'enrollment.student_edit', url_kwargs=dict(id_str='link_id'), url_kwargs_extra=dict(mode='edit'), attr='student_name' )
    profile_edit = LinkCol('Parent Name', 'profile.parent_profile', url_kwargs=dict(id_str='parent_id'), attr='father_name' )
    start_year = Col('Start Year')
    sex = Col('Gender')
    last_year_class = Col('Last Year Class')
    school_grade = Col('School Grade')
    nilai = Col('Nilai')
    section = Col('Class')
    enrollment_status = Col('Enrollment Status')
    payment_status = Col('Payment Status')
    edit = LinkCol('Enrollment', 'enrollment.enrollment_edit', url_kwargs=dict(id='enrollment_id'))

class Results_Student(Table):
    student_id = Col('student_id', show=False)
    link_id = Col('link_id', show=False)
    parent_id  = Col('parent_id', show=False)
#    student_name = Col('Student Name')
    student_edit = LinkCol('Student Name', 'enrollment.student_edit', url_kwargs=dict(id_str='link_id'), url_kwargs_extra=dict(mode='edit'), attr='student_name' )
    student_name_tamil = Col('மாணவர் பெயர்' )
    age = Col('Student Age')
    profile_edit = LinkCol('Parent 1', 'profile.parent_profile', url_kwargs=dict(id_str='parent_id'), attr='father_name' )
#    father_name = Col('Parent 1')
    mother_name = Col('Parent 2')
    roles = Col('Roles')
    email = Col('Email')
    email2 = Col('Email 2')
    student_email = Col('Student Email')
    phone1 = Col('Phone 1')
    phone2 = Col('Phone 2')
    sex = Col('Gender')
    start_year = Col('Start Year')
    last_year_class = Col('Last Year Class')
    school_grade = Col('School Grade')
    nilai = Col('Nilai')
    section = Col('Section')
    enrollment_status = Col('Enrollment Status')
    payment_status = Col('Payment Status')
    due_amount = Col('Due Amount')
    paid_amount = Col('Paid Amount')
    book_status = Col('Book Delivered')
    order_id = Col('Order #')
    parents_street_address = Col('Parents Street Address')
    parents_street_address2 = Col('Parents Street Address Line2')
    parents_city = Col('Parents City')
    parents_state = Col('Parents State')
    parents_country = Col('Parents Country')
    parents_zipcode = Col('Parents Zipcode')
    teaching_volunteer = Col('Teaching Volunteer?')
    teaching_dayntime = Col('Teaching Day Time?')
    teaching_grade = Col('Preferred Teaching Grade?')
    class_parent = Col('Class Parent?')
    skill_level_joining = Col('Skill Level While Joining')
    prior_tamil_school = Col('Prior Tamil School Experience')


class Results_StudentClass(Table):
    student_id = Col('student_id', show=False)
    parent_id  = Col('parent_id', show=False)
    student_name = Col('Student Name')
    student_name_tamil = Col('மாணவர் பெயர்' )
    age = Col('மாணவர் பெயர்' )
    father_name = Col('Parent 1')
    mother_name = Col('Parent 2')
    email = Col('Email')
    email2 = Col('Email 2')
    phone1 = Col('Phone 1')
    phone2 = Col('Phone 2')
    sex = Col('Gender')
    start_year = Col('Start Year')
    last_year_class = Col('Last Year Class')
    school_grade = Col('School Grade')
    nilai = Col('Nilai ID')
    nilai_name = Col('Nilai')
    section = Col('Section')
    enrollment_status = Col('Enrollment Status')
    payment_status = Col('Payment Status')
    book_status = Col('Book Delivered')
    room = Col('Room')
    teacher1 = Col('Teacher 1')
    teacher2 = Col('Teacher 2')

class Results_MyClass(Table):
    nilai = Col('Nilai')
    section = Col('Class')
    student_name = Col('Student Name')
    student_name_tamil = Col('மாணவர் பெயர்' )
    age = Col('Student Age')
    sex = Col('Gender')
    email = Col('Email')
    email2 = Col('Email 2')
    student_email = Col('Student Email')
    phone1 = Col('Phone 1')
    phone2 = Col('Phone 2')
    start_year = Col('Start Year')
    school_grade = Col('School Grade')
    enrollment_status = Col('Enrollment Status')
    payment_status = Col('Payment Status')
    book_status = Col('Book Delivered')
    room = Col('Room')
    teacher1 = Col('Teacher 1')
    teacher2 = Col('Teacher 2')

class Results_MyEnrollment(Table):
#    student_id = Col('student_id', show=False)
    link_id = Col('link_id', show=False)

    student_no = Col('Student ID')
    enrollment_no = Col('Enrollment ID')
    academic_year = Col('Academic Year')
    nilai = Col('Nilai')
    section = Col('Section')
#    student_edit = LinkCol('Student Name', 'student_edit', url_kwargs=dict(id='student_id'), url_kwargs_extra=dict(mode='_'), attr='student_name' )
    student_edit = LinkCol('Student Name', 'enrollment.student_edit', url_kwargs=dict(id_str='link_id'), url_kwargs_extra=dict(mode='_'), attr='student_name' )
    student_name_tamil = Col('மாணவர் பெயர்')
    age = Col('Student Age')
    sex = Col('Gender')
    start_year = Col('Start Year')
    school_grade = Col('School Grade')
    enrollment_status = Col('Enrollment Status')
    book_status = Col('Book Delivered')
    book_shipment_preference = Col('Book Shipment Preference')
    room = Col('Room')
    teacher1 = Col('Teacher 1')
    teacher2 = Col('Teacher 2')

class Results_MyPayment(Table):
    academic_year = Col('Academic Year')
    student_name = Col('Student Name')
    start_year = Col('Start Year')
    nilai = Col('Nilai')
    section = Col('Class')
    enrollment_status = Col('Enrollment Status')
    payment_status = Col('Payment Status')
    previous_balance = Col('Previous Balance')
    due_amount = Col('Fee')
    paid_amount = Col('Paid Amount')
    balance = Col('Balance')
    paid_date = Col('Paid Date')
    check_no = Col('Reference')


class Results_Dashboard(Table):
    nilai_id = Col('nilai_id', show=False)
    nilai = Col('Nilai', show=False)
    nilai_list = LinkCol('Nilai', 'class_management.nilai_list', url_kwargs=dict(id='nilai_id'), attr='nilai' )
    section = Col('Class', show=False)
    list = LinkCol('Class', 'class_management.class_list', url_kwargs=dict(section='section'), attr='section' )
    count = Col('Count')

class Results_Class(Table):
    nilai_id = Col('nilai_id', show=False)
    name = Col('Nilai')
    section = Col('Section')
    room = Col('Room #')
    teacher1 = Col('Teacher 1')
    teacher2 = Col('Teacher 2')
    teacher3 = Col('Teacher 3')
    class_day = Col('Day of Class')
    class_start_time = Col('Class Start Time')
    class_email = Col('Class Email')
    teacher_view = Col('Teacher View')
    parent_view = Col('Parent View')

    edit = LinkCol('Edit', 'class_management.class_edit', url_kwargs=dict(section='section') )

class Results_Attendance(Table):
    section = Col('Class')
    school_date = Col('Class Date' )
    take_attendance = LinkCol('Attendance Status', 'attendance.attendance', url_kwargs=dict(id='section_date'), attr='status' )
    locked = Col('Locked')

class Results_AttendanceDetail(Table):
    school_date = Col('Class Date' )
    attendance_status = Col('Status' )
    note = Col('Note')

class Results_Homework(Table):
    section = Col('Class')
    lesson_no = Col('Lesson / Week #' )
    take_homework = LinkCol('Status', 'homework.homework', url_kwargs=dict(id='section_lesson'), attr='status' )

class Results_HomeworkDetail(Table):
    lesson_no = Col('Lesson / Week #' )
    homework_date = Col('Date' )
    homework_status = Col('Status' )
    note = Col('Note' )

class Results_SummaryScore(Table):
    enrollment_id = Col('enrollment_id', show=False)
    link_id = Col('link_id', show=False)
    section = Col('Class')
    student_name = Col('Student Name')
    student_name_tamil = Col('மாணவர் பெயர்')
    age = Col('Student Age')
    exam_1 = Col('First Trimester', td_html_attrs = align_center)
    exam_2 = Col('Second Trimester', td_html_attrs = align_center)
    exam_3 = Col('Final Trimester', td_html_attrs = align_center)

    attendance_detail = LinkCol('Attendance', 'attendance.attendance_detail', url_kwargs=dict(id='link_id'), attr='attendance' )
    hw_audio_detail = LinkCol('Audio Homework', 'homework.homework_detail', url_kwargs=dict(id='link_id'), url_kwargs_extra=dict(type=1), attr='hw_audio' )
    hw_written_detail = LinkCol('Written Homework', 'homework.homework_detail', url_kwargs=dict(id='link_id'), attr='hw_written' )

#    attendance = Col('Attendance')
#    hw_audio = Col('Homework - Audio')
#    hw_written = Col('Homework - Written')


class Results_BookOrder(Table):
    order_id = Col('order_id', show=False)
    type = Col('Type')
    nilai_A = Col('Mun Mazhalai')
    nilai_0 = Col('Mazhalai')
    nilai_1 = Col('Nilai 1')
    nilai_2 = Col('Nilai 2')
    nilai_3 = Col('Nilai 3')
    nilai_4 = Col('Nilai 4')
    nilai_5 = Col('Nilai 5')
    nilai_6 = Col('Nilai 6')
    nilai_7 = Col('Nilai 7')
    nilai_8 = Col('Nilai 8')
    total   = Col('Total')
    order_date = Col('Order Date')
    status = Col('Order Status')
    note = Col('Note')
    edit = LinkCol('Edit', 'book_order.order_tracking', url_kwargs=dict(id='order_id') )


class Results_Profile(Table):
    parent_id  = Col('parent_id', show=False)
    profile_edit = LinkCol('Parent 1', 'profile.parent_profile', url_kwargs=dict(id_str='parent_id'), attr='father_name' )
    mother_name = Col('Parent 2')
    email = Col('Email')
    email2 = Col('Email 2')
    phone1 = Col('Phone 1')
    phone2 = Col('Phone 2')
    parents_street_address = Col('Parents Street Address')
    parents_street_address2 = Col('Parents Street Address Line2')
    parents_city = Col('Parents City')
    parents_state = Col('Parents State')
    parents_country = Col('Parents Country')
    parents_zipcode = Col('Parents Zipcode')
    roles = Col('Roles')

class Results_ClassTracking(Table):
    section = Col('Class')
    school_date = Col('Scheduled Date' )
    class_update = LinkCol('Status', 'class_tracking.class_tracking', url_kwargs=dict(id='section_date'), attr='status' )
    locked = Col('Locked' , td_html_attrs = align_center )

class Results_ClassTrackingMain(Table):
    section = Col('Class')
    school_date = Col('Scheduled Date' )
    class_date = Col('Class Date' )
    class_start_time = Col('Start Time' )
    class_end_time = Col('End Time' )
    lesson_no = Col('Lesson Completed' )
    class_activities = Col('Class Activities' )
    homework_paper = Col('HomeWork Assigned' )
    homework_audio = Col('Project Assigned' )
    note_to_parents = Col('Note To Parents' )

class Results_ClassTrackingAdmin(Results_ClassTrackingMain):
    note_to_admin = Col('Note To Admin' )
    note_from_admin = Col('Response From Admin' )
    admin_update = LinkCol('Admin Action', 'class_tracking.class_tracking', url_kwargs=dict(id='section_date'), url_kwargs_extra=dict(mode=1))

    volunteers_present = Col('HS Volunteers Present')
    volunteers_activities = Col('HS Volunteers Activities')
    teacher1_id = Col('Teacher 1')
    teacher2_id = Col('Teacher 2')
    substitute_teacher = Col('Substitute Teacher')

class Results_ClassTrackingDetails(Results_ClassTrackingMain):
    note_to_admin = Col('Note To Admin' )
    note_from_admin = Col('Response From Admin' )
    volunteers_present = Col('HS Volunteers Present')
    volunteers_activities = Col('HS Volunteers Activities')
    class_update = LinkCol('Status', 'class_tracking.class_tracking', url_kwargs=dict(id='section_date'), attr='status' )
    locked = Col('Locked' , td_html_attrs = align_center )

class Results_CategoryList(Table):
    edit = LinkCol('Config Category', 'setting.category_detail', url_kwargs=dict(name='category'), attr='category' )
#    category_order = Col('Display Order')
#    remove = LinkCol('Remove', 'event.program_delete', url_kwargs=dict(id='program_id') )

class Results_CategoryDetail(Table):
    category = Col('Config Category')
    edit = LinkCol('Category Key', 'setting.category_edit', url_kwargs=dict(id='link_id'), attr='category_key' )
#    category_key = Col('Category Key')
    category_value = Col('Category Value')
    order_by = Col('Display Order')
    active = Col('Active')
#    remove = LinkCol('Remove', 'setting.category_delete', url_kwargs=dict(id='id') )

class Results_SchoolYear(Table):
    academic_year = Col('Academic Year')
    edit = LinkCol('Academic Year Label', 'rollover.school_year_edit', url_kwargs=dict(id='academic_year'), attr='academic_year_label' )
    start_date = Col('School Start Date')
    end_date = Col('School Start Date')
    school_day = Col('School Day')
    school_start_time = Col('Class Start Time')
    rollover_status = Col('Rollover Status')

class Results_ServiceRequests(Table):
    service_id = Col('Service (#)')
    created_by = Col('Created By')
    created_for = Col('Created For')
    service_type = Col('Type')
    service_description = Col('Description')
    response = Col('Admin Team Response')
    # created_at = Col('Created On')
    # open = Col('Open' , td_html_attrs = align_center)
    # closed = Col('Closed' , td_html_attrs = align_center)
    # status = Col('Status' , td_html_attrs = align_center)

class Results_ServiceRequests_Admin(Table):
    service_id = Col('Service (#)')
    service_type = Col('Type')
    service_description = Col('Description')
    # user_id = Col('Created By', td_html_attrs = align_center)
    created_at = Col('Created On')
    # open = Col('Open' , td_html_attrs = align_center)
    # closed = Col('Closed' , td_html_attrs = align_center)
    status = Col('Status' , td_html_attrs = align_center)

class Results_ServiceRequestAnnualDay(Table):
    registration_id = Col('Reg (#)')
    email = Col('Email')
    student_email = Col('Student Email')
    events = Col('Registered Events')
    # user_id = Col('Created By', td_html_attrs = align_center)
    created_at = Col('Created On')
    comments = Col('Comments', td_html_attrs = {'class': 'col-sm-6 col-md-5 col-lg-3'})

class Results_ServiceRequestAnnualDay_Uploads(Table):
    id = Col('Upload Id')
    filename = Col('FileName', td_html_attrs = {'class': 'col-sm-6 col-md-5 col-lg-3'})

class Results_Feedback(Table):
    id = Col('Feedback(#)')
    email = Col('Email')
    teach_grade = Col('Teaching Nilai/Grade')
    teach_experience = Col('your teaching experience?')
    teach_continue = Col('Teaching next year?')
    teach_rec = Col('Recommend to other volunteers?')
    teach_ref_student = Col('Recommend to other students?')
    comments = Col('Comments', td_html_attrs = {'class': 'col-sm-6 col-md-5 col-lg-3'})
    last_updated_at = Col('Submitted Date', td_html_attrs = {'class': 'col-sm-6 col-md-3 col-lg-1'})

class Results_Prize(Table):
    id = Col('Request(#)')
    winner_name = Col('Full Name')
    winner_place = Col('Event Name')
    prize_amount = Col('Amount')
    winner_email = Col('APS Email')
    parent_email = Col('Parent Email')
    created_at = Col('Request Created On')
    status = Col('Status')

class Results_APSian(Table):
    father_name = Col('Father Name')
    mother_name = Col('Mother Name')
    email = Col('Primary Email')
    phone1 = Col('Primary Phone')
    email2 = Col('Secondary Email')
    phone2 = Col('Secondary Phone')
    parents_city = Col('City')
    parents_state = Col('State')
    parents_country = Col('Country')
    parents_zipcode = Col('ZipCode')

