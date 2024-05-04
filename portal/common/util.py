from datetime import datetime
from flask import url_for, make_response
from io import BytesIO
import unicodecsv as csv
import sys
from flask_user import current_user

def count(key_list) :
    max_count = 0
    for key in key_list :
        if '-' in key :
            key_parts = key.split('-')
            count = int(key_parts[1])
            if count > max_count :
                max_count = count
    return max_count + 1

def list_to_str(key_list, sep=',') :
    return sep.join([str(s) for s in key_list])

def str_to_list(str_list, sep=',') :
    if str_list :
        return str_list.split(sep)

def calc_final_score( row ):
    if not row.attendance or not row.hw_audio or not row.hw_written or not row.exam_1 or not row.exam_2 or not row.exam_3 :
        return None
    final_score = min(row.exam_1,100) * 0.15 + min(row.exam_2, 100) * 0.15 + min(row.exam_3, 100) * 0.2 \
            + min(row.attendance, 25)/25 * 20 + row.hw_audio/20 * 15 + row.hw_written/20 * 15
    return round(final_score,1)

def calc_final_grade( row ):
    if row.final_score :
        if row.final_score >= 90 :
            final_grade = 'A'
        elif row.final_score >= 80 :
            final_grade = 'B'
        elif row.final_score >= 70 :
            final_grade = 'C'
        elif row.final_score >= 60 :
            final_grade = 'D'
        else :
            final_grade = '-'
        return final_grade
    else :
        return None

def get_url_string(end_point, display, param_1, param_key = None, param_value = None  ) :
    if not display or display == 0 or display is None or display == 'nan' :
        return ''
    else:
        if param_key :
            param = { param_key : param_value  }
            return f'<a href="%s">%s</a>' %(url_for(end_point, id=param_1, **param ), display )
        else :
            return f'<a href="%s">%s</a>' %(url_for(end_point, id=param_1 ), display )

def get_url_attend( row ):
    return get_url_string('attendance.attendance_detail', row.attendance, row.link_id )

def get_url_hw( row, type = 0 ):
    if type == 0 :
        return get_url_string('homework.homework_detail', row.hw_written, row.link_id )
    else :
        return get_url_string('homework.homework_detail', row.hw_audio, row.link_id, "type" , type )

def get_url_term( row, term ):
    if term == 1 :
        return get_url_string('exam.term_detail', row.exam_1, row.link_id )
    elif term == 2 :
        return get_url_string('exam.term_detail', row.exam_2, row.link_id )
    else:
        return get_url_string('exam.term_detail', row.exam_3, row.link_id )

def get_url_term_dashboard( row, by ):
    if by == 'term' :
        return get_url_string('exam.term_detail', row.term_combined, row.link_id )
    else:
        return get_url_string('exam.term_detail', row.section, row.section_id )


def get_url_tracking( row, by ):
    if by == 'date' :
        return get_url_string('class_tracking.class_tracking_list', row.school_date, row.date_id )
    else:
        return get_url_string('class_tracking.class_tracking_list', row.section, row.section_id )


def get_name_part( name, part ):
    if not name :
        return ""
    name_list = name.split(" ")
    count = len(name_list)

    if part == 3 and count == 2 :
        return name_list[1]

    if part == 2 and count == 2 :
        return ""

    if count < part :
        return ""

    if part == 3 and count > 3 :
        return " ".join([name_list[i]  for i in range(part-1, count) ])

    return name_list[part - 1]


def download( rows, file_name , query = None ) :
    si = BytesIO()
    cw = csv.writer(si, encoding='utf-8-sig')
    if query :
        cw.writerow([col['name'] for col in query.column_descriptions])
        cw.writerows(rows)
    else :  ## Results as df
        cw.writerow(rows.columns)
        cw.writerows(rows.values.tolist())

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=%s' %file_name
    response.headers["Content-type"] = "text/csv"
    return response

def conv_to_float(num) :
    return float(num) if num and num.replace('.', '').isnumeric() else 0

def clean_list( _list ) :
    return [val for val in _list if val]

def format_date( _date ) :
    if type(_date) == str :
        return datetime.strptime(_date, "%Y-%m-%d").strftime("%d-%b-%Y")
    else :
        return _date.strftime("%d-%b-%Y")

def download_requests( rows, file_name , query = None ) :
    si = BytesIO()
    cw = csv.writer(si, encoding='utf-8-sig')
    if query :
        cw.writerow([col['name'] for col in query.column_descriptions])
        cw.writerows(rows)
    else :  ## Results as df
        # cw.writerow(rows.columns)
        # cw.writerows(rows.values.tolist())
        cw.writerows(rows)

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=%s' %file_name
    response.headers["Content-type"] = "text/csv"
    return response

def download_registrations( rows, file_name , query = None ) :
    si = BytesIO()
    cw = csv.writer(si, encoding='utf-8-sig')
    if query :
        cw.writerow([col['name'] for col in query.column_descriptions])
        cw.writerows(rows)
    else :  ## Results as df
        cw.writerow(rows.columns)
        cw.writerows(rows.values.tolist())
        # cw.writerows(rows)

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=%s' %file_name
    response.headers["Content-type"] = "text/csv"
    return response

def trace() :
    print( "%s : %s()" %(current_user.id if current_user else "" , sys._getframe(1).f_code.co_name ))

