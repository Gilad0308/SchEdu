from flask import render_template, request, redirect, url_for, flash, Blueprint, session
from .models import ClassTime, Day, Classroom, Equipment, Subject, Teacher, StudentsGroup, CourseClass, Schedule
from . import db
from flask_login import login_required, current_user


views = Blueprint('views', __name__)

# A dictionary that gives every day a number to each day according to its place in the week, 
days_order_dict = {"Sunday": 1, "Monday": 2, "Tuesday": 3, "Wednesday": 4, "Thursday": 5, "Friday": 6, "Saturday": 7}

# A list of the names of different equipment in classrooms
equipment_options = ["Computers", "Physics lab", "Chemistry lab", "Biology lab"]


# The base url of the site, later on it can be something like 'www.yourdomain.com/'
@views.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)


# Class Times And Study Days---------------------------------------------------------------------------------------


# Viewing the existing classtimes and adding new ones
# If GET request - returnes the page with all the class times
# If POST request - creates a new class time from the posted data, gives it a suitable index compared to the existing class times,
# adds it to the database and redirects back to this page.
@views.route('/classtimes', methods=['GET', 'POST'])
@login_required
def classtimes():
    sorted_classtimes = sorted(current_user.classtimes, key=get_index)
    if request.method == 'POST':
        start_time = str(request.form["start_time"])
        end_time = str(request.form["end_time"])
        if overlaps(start_time, end_time, sorted_classtimes):
            flash("Invalid class hour: overlaps an existing one.", category="error")
        else:
            index = find_index_update_others((start_time, end_time), sorted_classtimes)
            new_class_time = ClassTime(start_time=start_time, end_time=end_time, index=index, user=current_user)
            db.session.add(new_class_time)
            db.session.commit()
        return redirect(url_for('views.classtimes'))
    else:
        return render_template('classtimes.html', user=current_user, classtimes=sorted_classtimes)


# Deleting a class time.
# If there is a class time with the posted id, and this classtime isn't the last class time of a day,
# removes it from the database and redirects to the class time page.
# Updates the indexes of the other days.
@views.route('/classtimes/delete', methods=['POST'])
@login_required
def delete_ct():
    class_time = ClassTime.query.get(request.form['id'])
    if class_time is not None:
        if len(class_time.days_ending_this_time) > 0:
            flash("Can't delete class hour because it is the last lesson of certain day/s.", category="error")
        else:
            sorted_classtimes = sorted(current_user.classtimes, key=get_index)
            update_indexes_before_delete(class_time.index, sorted_classtimes)
            db.session.delete(class_time)
            db.session.commit()
    return redirect(url_for('views.classtimes'))


# Editing a class time
# Updates the class time according to the posted data and redirects back to the class times page.
# Updates its index and the indexes of the other days.
@views.route('/classtimes/edit', methods=['POST'])
@login_required
def edit_ct():
    action = request.form['action']
    class_time = ClassTime.query.get(request.form['id'])
    if action == 'retrieve':
        classtimes = current_user.classtimes

        start_time = str(request.form["start_time"])
        end_time = str(request.form["end_time"])
        classtimes.remove(class_time)
        if overlaps(start_time, end_time, classtimes):
            flash("Invalid class hour: overlaps an existing one.", category="error")
        else:
            classtimes.append(class_time)
            sorted_classtimes = sorted(classtimes, key=get_index)
            update_indexes_before_delete(class_time.index, sorted_classtimes)
            sorted_classtimes.remove(class_time)
            index = find_index_update_others((start_time, end_time), sorted_classtimes)
            class_time.index = index
            class_time.start_time = start_time
            class_time.end_time = end_time
            db.session.commit()
        return redirect(url_for('views.classtimes'))
    else:
        return render_template('edit_classtime.html', user=current_user, class_time=class_time)


# Receives the start time and end time the user has entered/chosen and a list of classtimes
# and returns True if they overlap an existing classtime, else returns False.
def overlaps(start_time, end_time, ct_list):
    for ct in ct_list:
        if is_before("t", ct.start_time, start_time) and is_before("t", start_time, ct.end_time):
            return True
        if is_before("t", ct.start_time, end_time) and is_before("t", end_time, ct.end_time):
            return True
        if is_before("t", start_time, ct.start_time) and is_before("t", ct.end_time, end_time):
            return True
        if start_time.__eq__(ct.start_time) and end_time.__eq__(ct.end_time):
            return True
    return False


# Receives a day or a classtime and returns its index.
def get_index(day_or_time):
    return day_or_time.index

# Receives a character "t" for a time string and "d" for a day string, and two strings of that type.
# Returns True if the first argument should come before the second (it comes before the other in the day/week), 
# therefore its index should be smaller.
def is_before(time_or_day, str_1, str_2):
    if time_or_day == "t":
        if int(str_1.replace(':', '')) < int(str_2.replace(':', '')):
            return True
        return False
    else:
        if days_order_dict[str_1] < days_order_dict[str_2]:
            return True
        return False


# Receives a tuple that its first value is a list of ClassTime objects or Day objects sorted by their index
# (in case of Class Time includes also: start time, end time). Returns the index that the new classtime should have.
# Calculates the index the new Object should have, updates the indexes of the others (as if it was added).
def find_index_update_others(data_tuple, sorted_objects):
    found_new_place = False
    current_index = 0
    new_index = 0
    
    for current_object in sorted_objects:
        current_index = current_object.index
        second_str = ""
        time_or_day = "t"
        if len(data_tuple) == 1:
            second_str = current_object.name
            time_or_day = "d"
        else:
            second_str = current_object.start_time

        if is_before(time_or_day, data_tuple[0], second_str):
            if not found_new_place:
                new_index = current_index
                found_new_place = True
            current_object.index = current_index + 1
    db.session.commit()

    if not found_new_place:
        new_index = current_index + 1

    return new_index


# Receives the index of a ClassTime or a Day that will be deleted and a list of Those objects sorted by their index, and updates the indexes of the others.
def update_indexes_before_delete(index_delete, sorted_objects):
    passed_delete = False
    for current_object in sorted_objects:
        current_index = current_object.index
        if passed_delete:
            current_object.index = current_index - 1
        if current_index == index_delete:
            passed_delete = True
    db.session.commit()


# Only Study Days------------------------------------------------

# Viewing the existing days and adding new ones
# If GET request - returnes the page with all the days
# If POST request - creates a new day from the posted data, gives it a suitable index
# compared to the existing days, adds it to the database and redirects back to this page.
@views.route('/days', methods=['GET', 'POST'])
@login_required
def days():
    sorted_days = sorted(current_user.days, key=get_index)
    if request.method == 'POST':
        day_name = request.form["day_name"]
        index = find_index_update_others((day_name,), sorted_days)
        last_class_time = ClassTime.query.get(request.form["last_ct_id"])
        new_day = Day(name=day_name, index=index, last_class_time=last_class_time, user=current_user)
        db.session.add(new_day)
        db.session.commit()
        return redirect(url_for('views.days'))
    else:
        sorted_classtimes = sorted(current_user.classtimes, key=get_index)
        left_days_dict = left_days(sorted_days)
        return render_template('days.html', user=current_user, days=sorted_days, left_days_dict=left_days_dict, classtimes=sorted_classtimes)


# Receives a sorted list of the user's days and returns a dictionary
# Which it's keys are the names of the days and values are boolean - true if the day hasn't been chosen yet.
def left_days(days):
    left_days_dict = {}
    for str_day in days_order_dict:
        left_days_dict[str_day] = True
    for day in days:
        left_days_dict[day.name] = False
    return left_days_dict


# Deleting a day.
# If there is a day with the posted id, removes it from the database and redirects to the days page.
# Updates the indexes of the other days.
@views.route('/days/delete', methods=['POST'])
@login_required
def delete_day():
    day = Day.query.get(request.form['id'])
    if day is not None:
        sorted_days = sorted(current_user.days, key=get_index)
        update_indexes_before_delete(day.index, sorted_days)
        db.session.delete(day)
        db.session.commit()
    return redirect(url_for('views.days'))


# Editing a day
# Updates the day according to the posted data and redirects back to the days page.
# Updates its index and the indexes of the other days.
@views.route('/days/edit', methods=['POST'])
@login_required
def edit_day():
    action = request.form['action']
    day = Day.query.get(request.form['id'])
    sorted_days = sorted(current_user.days, key=get_index)
    if action == 'retrieve':
        day_name = request.form["day_name"]
        update_indexes_before_delete(day.index, sorted_days)
        sorted_days.remove(day)
        index = find_index_update_others((day_name,), sorted_days)
        last_class_time = ClassTime.query.get(request.form["last_ct_id"])
        day.name = day_name
        day.index = index
        day.last_class_time = last_class_time
        db.session.commit()
        return redirect(url_for('views.days'))

    else:
        sorted_classtimes = sorted(current_user.classtimes, key=get_index)
        sorted_days.remove(day)
        left_days_dict = left_days(sorted_days)
        return render_template('edit_day.html', user=current_user, day=day, left_days_dict=left_days_dict, classtimes=sorted_classtimes)


# Classrooms-------------------------------------------------------------------------------------------------------------

# Viewing the existing classrooms and adding new ones
# If GET request - returnes the page with all the classrooms
# If POST request - creates a new classroom and equipment related to it from the posted data,
# adds it to the database and redirects back to this page.
@views.route('/classrooms', methods=['GET', 'POST'])
@login_required
def classrooms():
    if request.method == 'POST':
        name = request.form['name']
        num_seats = int(request.form['num_seats'])
        computers_lab = equipment_options[0] in request.form
        physics_lab = equipment_options[1] in request.form
        chemistry_lab = equipment_options[2] in request.form
        biology_lab = equipment_options[3] in request.form
        new_cr_equipment = Equipment(computers_lab=computers_lab, physics_lab=physics_lab, chemistry_lab=chemistry_lab, biology_lab=biology_lab, user=current_user)
        db.session.add(new_cr_equipment)
        db.session.flush()
        new_classroom = Classroom(name=name, num_seats=num_seats, equipment=new_cr_equipment, user=current_user)
        db.session.add(new_classroom)
        db.session.commit()
        return redirect(url_for('views.classrooms'))
    else:
        classrooms = current_user.classrooms
        return render_template('classrooms.html', user=current_user, classrooms=classrooms, equipment_options=equipment_options)


# Deleting a classroom.
# If there is a classroom with the posted id, removes it and the equipment related to it from the database,
# and redirects to the classrooms page.
@views.route('/classrooms/delete', methods=['POST'])
@login_required
def delete_cr():
    classroom = Classroom.query.get(request.form['id'])
    if classroom is not None:
        db.session.delete(classroom.equipment)
        db.session.delete(classroom)
        db.session.commit()
    return redirect(url_for('views.classrooms'))


# Editing a classroom
# Updates the classroom and the equipment related to it according to the
# posted data and redirects back to the classrooms page.
@views.route('/classrooms/edit', methods=['POST'])
@login_required
def edit_classroom():
    action = request.form['action']
    classroom = Classroom.query.get(request.form['id'])
    if action == 'retrieve':
        name = request.form['name']
        num_seats = int(request.form['num_seats'])

        db.session.delete(classroom.equipment)
        computers_lab = equipment_options[0] in request.form
        physics_lab = equipment_options[1] in request.form
        chemistry_lab = equipment_options[2] in request.form
        biology_lab = equipment_options[3] in request.form
        new_equipment = Equipment(computers_lab=computers_lab, physics_lab=physics_lab, chemistry_lab=chemistry_lab, biology_lab=biology_lab, user=current_user)
        db.session.add(new_equipment)
        db.session.flush()

        classroom.name = name
        classroom.num_seats = num_seats
        classroom.equipment = new_equipment
        db.session.commit()
        return redirect(url_for('views.classrooms'))
    else:
        return render_template('edit_classroom.html', user=current_user, classroom=classroom, equipment_options=equipment_options)

# Subjects---------------------------------------------------------------------------------------------------------------------


# Viewing the existing subjects and adding new ones
# If GET request - returnes the page with all the subjects
# If POST request - creates a new subject from the posted data, adds it to the database and redirects back to this page.
@views.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    if request.method == 'POST':
        name = request.form['name']
        level = int(request.form['level'])
        new_subject = Subject(name=name, level=level, user=current_user)
        db.session.add(new_subject)
        db.session.commit()
        return redirect(url_for('views.subjects'))
    else:
        subjects = current_user.subjects
        return render_template('subjects.html', user=current_user, subjects=subjects)


# Deleting a subject.
# If there is a subject with the posted id, and it's not related to existing study groups/ teachers/ classes,
# removes it from the database and redirects to the subjects page.
@views.route('/subjects/delete', methods=['POST'])
@login_required
def delete_subject():
    subject = Subject.query.get(request.form['id'])
    if subject is not None:
        associated_classes = False
        associated_teachers = False
        associated_groups = False
        if len(subject.classes) > 0:
            associated_classes = True
        for teacher in current_user.teachers:
            if subject in teacher.subjects:
                associated_teachers = True
                break
        for group in current_user.students_groups:
            if subject in group.subjects:
                associated_groups = True
                break

        if associated_classes or associated_teachers or associated_groups:
            error_message = related_message(associated_classes, associated_teachers, associated_groups)
            flash(error_message, category="error")
        else:
            db.session.delete(subject)
            db.session.commit()
    
    return redirect(url_for('views.subjects'))


# Receives the lists of the associated classes, teachers and groups and returns
# a suitable message that should be displayed to the user.
def related_message(associated_classes, associated_teachers, associated_groups):
    error_message = "Can't delete subject because it's associated with certain"
    if associated_classes:
        error_message += " classes"
    if associated_teachers:
        if associated_classes and associated_groups:
            error_message += ","
        elif associated_classes and not associated_groups:
            error_message += " and"
        error_message += " teachers"
    if associated_groups:
        if associated_classes or associated_teachers:
            error_message += " and"
        error_message += " study groups"
    error_message += "."
    return error_message


# Editing a subject
# Updates the subject according to the posted data and redirects back to the subjects page.
@views.route('/subjects/edit', methods=['POST'])
@login_required
def edit_subject():
    action = request.form['action']
    subject = Subject.query.get(request.form['id'])
    if action == 'retrieve':
        name = request.form['name']
        level = int(request.form['level'])
        subject.name = name
        subject.level = level
        db.session.commit()
        return redirect(url_for('views.subjects'))
    else:
        return render_template('edit_subject.html', user=current_user, subject=subject)

# Teachers--------------------------------------------------------------------------------------------------------

# Viewing the existing teachers and adding new ones
# If GET request - returnes the page with all the teachers
# If POST request - creates a new teacher from the posted data, adds it to the database and redirects back to this page.
@views.route('/teachers', methods=['GET', 'POST'])
@login_required
def teachers():
    if request.method == 'POST':
        name = request.form['name']
        new_teacher = Teacher(name=name, user=current_user)
        db.session.add(new_teacher)
        for subject_id in request.form.getlist('subject_ids'):
            new_teacher.subjects.append(Subject.query.get_or_404(subject_id))
        db.session.commit()
        return redirect(url_for('views.teachers'))
    else:
        teachers = current_user.teachers
        subjects = current_user.subjects
        return render_template('teachers.html', user=current_user, teachers=teachers, subjects=subjects)


# Deleting a teacher.
# If there is a teacher with the posted id, and it's not related to existing classes,
# removes it from the database and redirects to the teachers page.
@views.route('/teachers/delete', methods=['POST'])
@login_required
def delete_teacher():
    teacher = Teacher.query.get(request.form['id'])
    if teacher is not None:
        if len(teacher.classes) > 0:
            flash("Can't delete teacher because it's associated with certain classes.", category="error")
        else:
            db.session.delete(teacher)
            db.session.commit()
    return redirect(url_for('views.teachers'))


# Editing a teacher
# Updates the teacher according to the posted data and redirects back to the teachers page.
@views.route('/teachers/edit', methods=['POST'])
@login_required
def edit_teacher():
    action = request.form['action']
    teacher = Teacher.query.get(request.form['id'])
    if action == 'retrieve':
        name = request.form['name']
        teacher.name = name
        previous_subjects = teacher.subjects
        for subject in previous_subjects:
            teacher.subjects.remove(subject)
        for subject_id in request.form.getlist('subject_ids'):
            teacher.subjects.append(Subject.query.get_or_404(subject_id))
        db.session.commit()
        return redirect(url_for('views.teachers'))
    else:
        subjects = current_user.subjects
        return render_template('edit_teacher.html', user=current_user, teacher=teacher, subjects=subjects)


# Study Groups---------------------------------------------------------------------------------------------------

# Viewing the existing study groups and adding new ones
# If GET request - returnes the page with all the study groups
# If POST request - creates a new study group from the posted data, adds it to the database and redirects back to this page.
@views.route('/studygroups', methods=['GET', 'POST'])
@login_required
def studygroups():
    if request.method == 'POST':
        name = request.form['name']
        num_students = int(request.form['num_students'])
        new_group = StudentsGroup(name=name, num_students=num_students, user=current_user)
        db.session.add(new_group)
        for subject_id in request.form.getlist('subject_ids'):
            new_group.subjects.append(Subject.query.get_or_404(subject_id))
        db.session.commit()
        return redirect(url_for('views.studygroups'))
    else:
        groups = current_user.students_groups
        subjects = current_user.subjects
        return render_template('studygroups.html', user=current_user, groups=groups, subjects=subjects)


# Deleting a study group.
# If there is a study group with the posted id, and it's not related to existing classes,
# removes it from the database and redirects to the study groups page.
@views.route('/studygroups/delete', methods=['POST'])
@login_required
def delete_sg():
    group = StudentsGroup.query.get(request.form['id'])
    if group is not None:
        associated_classes = False
        for course_class in current_user.classes:
            if group in course_class.students_groups:
                associated_classes = True
        
        if associated_classes:
            flash("Can't delete study group beacuse it's associated with certian classes.", category="error")
        else:
            db.session.delete(group)
            db.session.commit()
    return redirect(url_for('views.studygroups'))


# Editing a study group.
# Updates the study group according to the posted data and redirects back to the study groups page.
@views.route('/studygroups/edit', methods=['POST'])
@login_required
def edit_sg():
    action = request.form['action']
    group = StudentsGroup.query.get(request.form['id'])
    if action == 'retrieve':
        name = request.form['name']
        num_students = int(request.form['num_students'])
        group.name = name
        group.num_students = num_students
        previous_subjects = group.subjects
        for subject in previous_subjects:
            group.subjects.remove(subject)
        for subject_id in request.form.getlist('subject_ids'):
            group.subjects.append(Subject.query.get_or_404(subject_id))
        db.session.commit()
        return redirect(url_for('views.studygroups'))
    else:
        subjects = current_user.subjects
        return render_template('edit_studygroup.html', user=current_user, group=group, subjects=subjects)


# Classes----------------------------------------------------------------------------------------------------


# Viewing the existing classes and adding new ones
# If GET request - returnes the page with all the classes
# If POST request - creates a new class and equipment related to it from the posted data,
# adds it to the database and redirects back to this page.
@views.route('/classes', methods=['GET', 'POST'])
@login_required
def classes():
    if request.method == 'POST':
        subject = Subject.query.get(request.form['subject_id'])
        teacher = Teacher.query.get(request.form['teacher_id'])
        
        computers_lab = equipment_options[0] in request.form
        physics_lab = equipment_options[1] in request.form
        chemistry_lab = equipment_options[2] in request.form
        biology_lab = equipment_options[3] in request.form
        equipment_required = Equipment(computers_lab=computers_lab, physics_lab=physics_lab, chemistry_lab=chemistry_lab, biology_lab=biology_lab, user=current_user)
        db.session.add(equipment_required)
        db.session.flush()

        num_per_week = int(request.form['num_per_week'])
        new_class = CourseClass(subject=subject, teacher=teacher, equipment_required=equipment_required, num_per_week=num_per_week, user=current_user)
        db.session.add(new_class)
        db.session.flush()

        for group_id in request.form.getlist('group_ids'):
            new_class.students_groups.append(StudentsGroup.query.get(group_id))
        db.session.commit()

        return redirect(url_for('views.classes'))
    else:
        subjects = current_user.subjects
        teachers = current_user.teachers
        groups = current_user.students_groups
        classes = current_user.classes
        return render_template('classes.html', user=current_user, classes=classes, subjects=subjects, teachers=teachers, groups=groups, equipment_options=equipment_options)


# Deleting a class.
# If there is a class with the posted id, removes it and the equipment related to it from the database,
# and redirects to the classes page.
@views.route('/classes/delete', methods=['POST'])
@login_required
def delete_class():
    class_to_delete = CourseClass.query.get(request.form['id'])
    if class_to_delete is not None:
        db.session.delete(class_to_delete.equipment_required)
        db.session.delete(class_to_delete)
        db.session.commit()
    return redirect(url_for('views.classes'))


# Editing a class
# Updates the class and the equipment related to it according to the
# posted data and redirects back to the classes page.
@views.route('/classes/edit', methods=['POST'])
@login_required
def edit_class():
    action = request.form['action']
    class_to_edit = CourseClass.query.get(request.form['id'])
    if action == "retrieve":
        subject = Subject.query.get_or_404(request.form['subject_id'])
        teacher = Teacher.query.get_or_404(request.form['teacher_id'])
        num_per_week = int(request.form['num_per_week'])
        
        db.session.delete(class_to_edit.equipment_required)
        computers_lab = equipment_options[0] in request.form
        physics_lab = equipment_options[1] in request.form
        chemistry_lab = equipment_options[2] in request.form
        biology_lab = equipment_options[3] in request.form
        equipment_required = Equipment(computers_lab=computers_lab, physics_lab=physics_lab, chemistry_lab=chemistry_lab, biology_lab=biology_lab, user=current_user)
        db.session.add(equipment_required)
        db.session.flush()

        class_to_edit.subject = subject
        class_to_edit.teacher = teacher
        class_to_edit.num_per_week = num_per_week
        class_to_edit.equipment_required = equipment_required

        previous_groups = class_to_edit.students_groups
        for group in previous_groups:
            class_to_edit.students_groups.remove(group)
        for group_id in request.form.getlist('group_ids'):
            class_to_edit.students_groups.append(StudentsGroup.query.get_or_404(group_id))
        db.session.commit()

        return redirect(url_for('views.classes'))
    else:
        subjects = current_user.subjects
        teachers = current_user.teachers
        groups = current_user.students_groups
        return render_template('edit_class.html', user=current_user, class_to_edit=class_to_edit, subjects=subjects, teachers=teachers, groups=groups, equipment_options=equipment_options)


# Schedules--------------------------------------------------------------------------------------------------------------------------------


# Viewing the names and dates created of the user's schedules, and creating a new schedule.
# If GET request - returnes the page with all the schedules.
# If POST request - passes the posted schedule id to the session and redirects to the show schedule page.
@views.route('/schedules', methods=['GET', 'POST'])
@login_required
def schedules():
    # When the user want's to view & edit one of the schedules
    if request.method == 'POST':
        session["schedule_id"] = request.form['id']
        return redirect(url_for('views.show_schedule'))

    sorted_schedules = []
    sorted_schedules = sorted(current_user.schedules, key=get_datetime, reverse=True)  # Schedules sorted by date, latest first.
    return render_template('schedules.html', user=current_user, schedules=sorted_schedules)


# Receives a schedule and returns the datetime it was created on.
def get_datetime(schedule):
    return schedule.date_created


# Viewing the full table of the schedule.
# If GET request - returns a page with the schedule's table.
# If POST request - returns a page with the schedule's table, filtered by the posted filtering choices.
@views.route('schedules/show_schedule', methods=['GET', 'POST'])
@login_required
def show_schedule():
    is_filter = False
    selected_subjects = []
    selected_teachers = []
    selected_groups = []
    or_true_and_false = True
    # The meaning of request method 'POST' is that a filter was applied by the user.
    if request.method == 'POST':
        is_filter = True
        for subject_id in request.form.getlist('subject_ids'):
            selected_subjects.append(Subject.query.get(subject_id))
        for teacher_id in request.form.getlist('teacher_ids'):
            selected_teachers.append(Teacher.query.get(teacher_id))
        for group_id in request.form.getlist('group_ids'):
            selected_groups.append(StudentsGroup.query.get(group_id))
        or_true_and_false = bool(int(request.form['or_and']))

    schedule = Schedule.query.get_or_404(session["schedule_id"])
    sorted_classtimes = sorted(schedule.classtimes, key=get_index)
    sorted_days = sorted(schedule.days, key=get_index)
    return render_template('show_schedule.html', user=current_user, schedule=schedule, sorted_classtimes=sorted_classtimes, sorted_days=sorted_days, is_filter=is_filter,
                           selected_subjects=selected_subjects, selected_teachers=selected_teachers, selected_groups=selected_groups, or_true_and_false=or_true_and_false)

# Deleting a schedule
# If a schedule with the posted id exists, removed it and all the objects associated with it.
# Redirects back to the schedules page.
@views.route('/schedules/delete', methods=['POST'])
@login_required
def delete_schedule():
    schedule = Schedule.query.get(request.form['id'])
    if schedule is not None:
        delete_all(schedule.days)
        delete_all(schedule.classtimes)
        delete_all(schedule.classrooms)
        delete_all(schedule.equipments)
        delete_all(schedule.subjects)
        delete_all(schedule.teachers)
        delete_all(schedule.students_groups)
        delete_all(schedule.classes)
        db.session.commit()

        db.session.delete(schedule)
        db.session.commit()
    return redirect(url_for('views.schedules'))


# Receives a list of objects to delete, and deletes them, without commiting.
# If the list is None, won't do anything.
def delete_all(objects_lst):
    try:
        for obj in objects_lst:
            db.session.delete(obj)
    except:
        pass


# Changes the slot (day, hour and classroom) of a class in a schedule.
# Checks if it's possible (satisfies the schedule requirements), if not displays a suitable message.
# Redirects to the schedules page.
@views.route('/schedules/reschedule-class', methods=['POST'])
@login_required
def relocate_class():
    schedule = Schedule.query.get(request.form['schedule_id'])
    class_to_move = CourseClass.query.get(request.form['class_id'])
    
    day_time_tuple = request.form['day_time_ids'].split(',')
    new_day = Day.query.get(int(day_time_tuple[0]))
    new_classtime = ClassTime.query.get(int(day_time_tuple[1]))

    new_classroom = Classroom.query.get(request.form['classroom_id'])

    # Checks if new place satisfies the schedule requirements (according to 'evaluate_schedule' function in 'Algorith' module)
    num_conflicts = 0
    new_time_classes = new_day.intersection(new_classtime.classes)  # Other classes in the same day and classtime
    try:
        new_time_classes.remove(class_to_move)
    except ValueError:
        pass

    # Fitness criterion: was the class placed in the same slot with other classes.
    new_place_classes = new_classroom.intersection(new_time_classes)
    
    if len(new_place_classes) > 0:
        num_conflicts += 1
        flash("There is already a class in the chosen day, hour, and classroom.", category="error")
    # Fitness criterion: was the class placed in a room which has all the required equipment.
    if not new_classroom.equipment.satisfies_requirements(class_to_move.equipment_required):
        num_conflicts += 1
        flash("The chosen classroom doesn't include the required equipment.", category="error")
    # Fitness criterion: was the class placed in a room with enough seats for all the students.
    sum_students = 0
    students_groups = class_to_move.students_groups
    for group in students_groups:
        sum_students += group.num_students
    if new_classroom.num_seats < sum_students:
        num_conflicts += 1
        flash("There isn't enough space in the chosen classroom.", category="error")
    
    # Fitness criterion: was the teacher assigned to teach a different class at the same time (day and hour).
    teacher = class_to_move.teacher
    for current_class in new_time_classes:
        if current_class.teacher.teacher_id == teacher.teacher_id:
            num_conflicts += 1
            flash("The class's teacher already teaches in the chosen time (day & class hour).", category="error")
            break
    
    # Fitness criterion: was the students groups assigned to study a different class at the same time (day and hour).
    groups = class_to_move.students_groups
    groups_conflict = False
    for current_class in new_time_classes:
        for current_group in current_class.students_groups:
            if current_group in groups:
                groups_conflict = True
                num_conflicts += 1
                flash("One or more of the classe's study groups already study in the chosen time (day & class hour)", category="error")
                break
        if groups_conflict:
            break

    if num_conflicts == 0:
        class_to_move.day = new_day
        class_to_move.class_time = new_classtime
        class_to_move.classroom = new_classroom
        db.session.commit()
        # flash("The class has been rescheduled", category="success")

    return redirect(url_for('views.show_schedule', id=schedule.schedule_id))

