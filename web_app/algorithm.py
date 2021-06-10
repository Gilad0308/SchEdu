# Algorithm python classes are imported as A<class name>
from .algorithm_classes.for_Algorithm import (
    ClassTime as AClassTime, Day as ADay, Equipment as AEquipment,
    Classroom as AClassroom, Subject as ASubject, Teacher as ATeacher,
    StudentsGroup as AStudentsGroup, CourseClass as ACourseClass
)
from .algorithm_classes.Algorithm import Algorithm

from . import db
from .models import ClassTime, Day, Equipment, Classroom, Subject, Teacher, StudentsGroup, CourseClass, Schedule
from flask import request, redirect, url_for, flash, Blueprint, session
from flask_login import login_required, current_user
from datetime import datetime
import pytz


algorithm = Blueprint('algorithm', __name__)


# Runs the algorithm by passing it data from the database, receives the results and inserts them into the database,
# then posts the new schedule id to the show schedule page.
# If the algorithm fails to create a schedule, displayes a suitable message,
# then redirects to the schedules page.
@algorithm.route('/create_schedule', methods=['GET', 'POST'])
@login_required
def create_schedule():
    if request.method == 'POST':
        schedule_name = None
        if 'name' in request.form:
            schedule_name = request.form['name']
        current_tz = request.form['time_zone']
        date_created = datetime.now(pytz.timezone(current_tz))

        # Activates algorithm
        schedule = Schedule(name=schedule_name, user=current_user, date_created=date_created)
        ACourseClasses, a_days, a_classtimes, a_classrooms = data_from_db(schedule)
        algorithm = Algorithm(ACourseClasses, a_days, a_classtimes, a_classrooms)
        returned_tuple = algorithm.run()

        if returned_tuple[0]:
            session["schedule_id"] = schedule.schedule_id
            a_schedule = returned_tuple[1]
            data_from_algorithm(a_schedule)
            return redirect(url_for('views.show_schedule'))

        # If there are conflicts discovered during calculation, that the algorithm can't overcome
        delete_schedule(schedule)
        for message in returned_tuple[1]:
            flash(message, category='error')
        return redirect(url_for('views.schedules'))


# Deletes the schedule if classes couldn't be assigned to it successfuly.
def delete_schedule(schedule):
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


# Receives a list of objects to delete, and deletes them, without commiting.
# If the list is None, won't do anything.
def delete_all(objects_lst):
    try:
        for obj in objects_lst:
            db.session.delete(obj)
    except:
        pass


# Receives the schedule database object (not related yet to other objects).
# Extracts from the database the input data for the algorithm.
# Creates entirely new objects with new relations of all the database objects needed for creating a schedule.
# Creates new python objects for the algorithm.
# Does that using dictionaries whose keys are the ids of the original objects and the values are the duplicated objects.
def data_from_db(schedule):
    classtimes_dict = {}
    a_classtimes_dict = {}
    for ct in current_user.classtimes:
        ct_dup = ClassTime(start_time=ct.start_time, end_time=ct.end_time, index=ct.index, user=None, schedule=schedule)
        db.session.add(ct_dup)
        db.session.flush()
        classtimes_dict[ct.class_time_id] = ct_dup
        a_classtimes_dict[ct.class_time_id] = AClassTime(ct_dup.class_time_id, ct_dup.start_time, ct_dup.end_time, ct_dup.index)
    db.session.commit()
    a_classtimes = list(a_classtimes_dict.values())

    days_dict = {}
    a_days_dict = {}
    for day in current_user.days:
        last_ct_id = day.last_class_time.class_time_id  # The id of the original last class time
        day_dup = Day(name=day.name, index=day.index, last_class_time=classtimes_dict[last_ct_id], user=None, schedule=schedule)
        db.session.add(day_dup)
        db.session.flush()
        days_dict[day.day_id] = day_dup
        a_days_dict[day.day_id] = ADay(day_dup.day_id, day_dup.name, day_dup.index, a_classtimes_dict[last_ct_id])
    db.session.commit()
    a_days = list(a_days_dict.values())

    classrooms_dict = {}
    a_classrooms_dict = {}
    for classroom in current_user.classrooms:
        eq_to_dup = classroom.equipment
        equipment_dup = Equipment(computers_lab=eq_to_dup.computers_lab, physics_lab=eq_to_dup.physics_lab, chemistry_lab=eq_to_dup.chemistry_lab, biology_lab=eq_to_dup.biology_lab, user=None, schedule=schedule)
        db.session.add(equipment_dup)
        db.session.flush()
        classroom_dup = Classroom(name=classroom.name, num_seats=classroom.num_seats, equipment=equipment_dup, user=None, schedule=schedule)
        db.session.add(classroom_dup)
        db.session.flush()
        classrooms_dict[classroom.classroom_id] = classroom_dup

        a_equipment = AEquipment(equipment_dup.computers_lab, equipment_dup.physics_lab, equipment_dup.chemistry_lab, equipment_dup.biology_lab)
        a_classrooms_dict[classroom.classroom_id] = AClassroom(classroom_dup.classroom_id, classroom_dup.name, classroom_dup.num_seats, a_equipment)
    db.session.commit()
    a_classrooms = list(a_classrooms_dict.values())

    subjects_dict = {}
    a_subjects_dict = {}
    for subject in current_user.subjects:
        subject_dup = Subject(name=subject.name, level=subject.level, user=None, schedule=schedule)
        db.session.add(subject_dup)
        db.session.flush()
        subjects_dict[subject.subject_id] = subject_dup
        a_subjects_dict[subject.subject_id] = ASubject(subject_dup.subject_id, subject_dup.name, subject_dup.level)
    db.session.commit()

    teachers_dict = {}
    a_teachers_dict = {}
    for teacher in current_user.teachers:
        teacher_dup = Teacher(name=teacher.name, user=None, schedule=schedule)
        db.session.add(teacher_dup)
        db.session.flush()
        a_teaching_subjects = []
        for subject in teacher.subjects:
            teacher_dup.subjects.append(subjects_dict[subject.subject_id])
            a_teaching_subjects.append(a_subjects_dict[subject.subject_id])
        
        teachers_dict[teacher.teacher_id] = teacher_dup
        a_teachers_dict[teacher.teacher_id] = ATeacher(teacher_dup.teacher_id, teacher_dup.name, a_teaching_subjects)
    db.session.commit()

    groups_dict = {}
    a_groups_dict = {}
    for group in current_user.students_groups:
        group_dup = StudentsGroup(name=group.name, num_students=group.num_students, user=None, schedule=schedule)
        db.session.add(group_dup)
        db.session.flush()
        a_studying_subjects = []
        for subject in group.subjects:
            group_dup.subjects.append(subjects_dict[subject.subject_id])
            a_studying_subjects.append(a_subjects_dict[subject.subject_id])

        groups_dict[group.group_id] = group_dup
        a_groups_dict[group.group_id] = AStudentsGroup(group_dup.group_id, group_dup.name, group_dup.num_students, a_studying_subjects)
    db.session.commit()


    ACourseClasses = []
    for course_class in current_user.classes:
        num_per_week = course_class.num_per_week
        for i in range(num_per_week):
            eq_to_dup = course_class.equipment_required
            equipment_dup = Equipment(computers_lab=eq_to_dup.computers_lab, physics_lab=eq_to_dup.physics_lab, chemistry_lab=eq_to_dup.chemistry_lab, biology_lab=eq_to_dup.biology_lab, user=None, schedule=schedule)
            db.session.add(equipment_dup)
            db.session.flush()
            course_class_dup = CourseClass(subject=subjects_dict[course_class.subject_id], teacher=teachers_dict[course_class.teacher_id], equipment_required=equipment_dup, num_per_week=num_per_week, user=None, schedule=schedule)
            db.session.add(course_class_dup)
            db.session.flush()
            
            a_participating_groups = []
            for group in course_class.students_groups:
                course_class_dup.students_groups.append(groups_dict[group.group_id])
                a_participating_groups.append(a_groups_dict[group.group_id])
            db.session.flush()

            a_equipment_required = AEquipment(equipment_dup.computers_lab, equipment_dup.physics_lab, equipment_dup.chemistry_lab, equipment_dup.biology_lab)
            ACourseClasses.append(ACourseClass(course_class_dup.class_id, a_subjects_dict[course_class.subject_id], a_teachers_dict[course_class.teacher_id], a_participating_groups, a_equipment_required))
    db.session.commit()


    return ACourseClasses, a_days, a_classtimes, a_classrooms


# Inserts the algorithm calculation results to the database
def data_from_algorithm(a_schedule):
    assigning_dict = a_schedule.assigning_dict
    for a_course_class in assigning_dict:
        current_class = CourseClass.query.get(a_course_class.id)
        current_slot = assigning_dict[a_course_class]
        current_class.day = Day.query.get(current_slot[0].id)
        current_class.class_time = ClassTime.query.get(current_slot[1].id)
        current_class.classroom = Classroom.query.get(current_slot[2].id)
    db.session.commit()

