from . import db
from flask_login import UserMixin


# The table linking between the subjects and the teachers.
# There is a Many-To-Many relationship between them: 
# A teacher can teach multiple subjects and a subject can be taught by multiple teachers.
teachers_subjects = db.Table("teachers_subjects",
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.teacher_id')),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.subject_id'))
)

# The table linking between the subjects and the groups of students.
# There is a Many-To-Many relationship between them: 
# A students group can study multiple subjects and a subject can be studied by multiple students groups.
groups_subjects = db.Table("groups_subjects",
    db.Column('group_id', db.Integer, db.ForeignKey('students_group.group_id')),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.subject_id'))
)

# The table linking between the classes (CourseClass objects) and the groups of students.
# There is a Many-To-Many relationship between them:
# A class can have multiple groups in it, and a group can participate in multiple classes.
classes_groups = db.Table("classes_groups",
    db.Column('class_id', db.Integer, db.ForeignKey('course_class.class_id')),
    db.Column('group_id', db.Integer, db.ForeignKey('students_group.group_id'))
)


class Day(db.Model):
    day_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    # The number of the day in the week (starting from 1). The indexes of all days have to be sequential, 
    # and they represent the order of them in the week
    index = db.Column(db.Integer)
    # One-To-Many: a Day can have only one last classTime but a classTime can be the last lesson in multiple days.
    last_class_time_id = db.Column(db.Integer, db.ForeignKey('class_time.class_time_id'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))

    # For calculation results
    # One-To-Many: every row has one day but every day can appear in multiple rows
    classes = db.relationship('CourseClass', backref='day')

    # Receives a list of DB CourseClass objects and returns
    # a list which represents the intersection between this object's scheduled classes and the received list.
    # Average complexity: O(n)
    def intersection(self, other_lst):
        # Use of hybrid method
        this_lst = self.classes
        temp = set(other_lst)
        intersection_lst = [value for value in this_lst if value in temp]
        return intersection_lst


class ClassTime(db.Model):
    class_time_id = db.Column(db.Integer, primary_key=True)
    # The start time and end time will be in the form of hh:mm.
    start_time = db.Column(db.String(20))
    end_time = db.Column(db.String(20))
    # The number of the lesson in the day (starting from 1). The indexes of all classtimes have to be sequential, 
    # and they represent the order of them in the day
    index = db.Column(db.Integer)
    # One-To-Many: a Day can have only one last classTime but a classTime can be the last lesson in multiple days.
    days_ending_this_time = db.relationship('Day', backref='last_class_time')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))

    # For calculation results
    # One-To-Many: every row has one classtime but every classtime can appear in multiple rows
    classes = db.relationship('CourseClass', backref='class_time')

    # Receives a list of DB CourseClass objects and returns
    # a list which represents the intersection between this object's scheduled classes and the received list.
    # Average complexity: O(n)
    def intersection(self, other_lst):
        # Use of hybrid method
        this_lst = self.classes
        temp = set(other_lst)
        intersection_lst = [value for value in this_lst if value in temp]
        return intersection_lst


class Classroom(db.Model):
    classroom_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    num_seats = db.Column(db.Integer)
    # One-To-One: a classroom has only one equipment object and every equipment object "belongs" to one class.
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id'))
    equipment = db.relationship('Equipment', uselist=False, back_populates='classroom')
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))
    
    # For calculation results
    # One-To-Many: every row has one classroom but every classroom can appear in multiple rows
    classes = db.relationship('CourseClass', backref='classroom')

    # Receives a list of DB CourseClass objects and returns
    # a list which represents the intersection between this object's scheduled classes and the received list.
    # Average complexity: O(n)
    def intersection(self, other_lst):
        # Use of hybrid method
        this_lst = self.classes
        temp = set(other_lst)
        intersection_lst = [value for value in this_lst if value in temp]
        return intersection_lst


class Equipment(db.Model):
    equipment_id = db.Column(db.Integer, primary_key=True)
    computers_lab = db.Column(db.Boolean)
    physics_lab = db.Column(db.Boolean)
    chemistry_lab = db.Column(db.Boolean)
    biology_lab = db.Column(db.Boolean)

    # One-To-On: a class has only one equipment object and equipment every equipment object "belongs" to one class.
    course_class = db.relationship('CourseClass', back_populates='equipment_required')
    # One-To-One: a classroom has only one equipment object and every equipment object "belongs" to one class.
    classroom = db.relationship('Classroom', back_populates='equipment')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))

    def __str__(self):
        has_equipment = False
        description = ""
        if self.computers_lab:
            description += "Computers"
            has_equipment = True
        if self.physics_lab:
            if has_equipment:
                description += ", Physics lab"
            else:
                description += "Physics lab"
                has_equipment = True
        if self.chemistry_lab:
            if has_equipment:
                description += ", Chemistry lab"
            else:
                description += "Chemistry lab"
                has_equipment = True
        if self.biology_lab:
            if has_equipment:
                description += ", Biology lab"
            else:
                description += "Biology lab"
                has_equipment = True

        if not has_equipment:
            description += " - "

        return description
    
    # Receives another Equipment object that represents the equipment requirements of a class
    # and returns true if it satisfys these requirements.
    def satisfies_requirements(self, requirements):
        if requirements.computers_lab:
            if not self.computers_lab:
                return False
        if requirements.physics_lab:
            if not self.physics_lab:
                return False
        if requirements.chemistry_lab:
            if not self.chemistry_lab:
                return False
        if requirements.chemistry_lab:
            if not self.chemistry_lab:
                return False

        return True


class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    level = db.Column(db.Integer)
    # The first value passed is the name of the other Class ('Teacher').
    # The value inserted to 'secondary' is the name of the linking table
    # The first value passed to 'backref' ('subjects') is the name of the list in the other class ('Teacher') of instances of this Class.
    teaching_subjects = db.relationship('Teacher', secondary=teachers_subjects, backref=db.backref('subjects', lazy='dynamic'))
    # 'subjects' is the name of the list in the 'Teacher' object that represent the subjects the teacher teaches.
    studied_subjects = db.relationship('StudentsGroup', secondary=groups_subjects, backref=db.backref('subjects', lazy='dynamic'))
    # One-To-Many: a subject can be taught in multiple classes but every class has only one subject.
    classes = db.relationship('CourseClass', backref='subject')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))

    def __str__(self):
        return f"{self.name} - {self.level} points"


class Teacher(db.Model):
    teacher_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    # One-To-Many: a teacher can teach multiple classes but a single class has only one teacher.
    classes = db.relationship('CourseClass', backref='teacher')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))


class StudentsGroup(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    num_students = db.Column(db.Integer)
    # 'students_groups' is the name of the list in the 'CourseClass' object that represents the participating students groups.
    participating_groups = db.relationship('CourseClass', secondary=classes_groups, backref=db.backref('students_groups', lazy='dynamic'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))


class CourseClass(db.Model):
    class_id = db.Column(db.Integer, primary_key=True)
    # One-To-Many: a subject can be taught in multiple classes but every class has only one subject.
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'))
    # One-To-Many: a teacher can teach multiple classes but a single class has only one teacher.
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.teacher_id'))
    # One-To-One: a class has only one equipment object and every equipment object "belongs" to one class.
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id'))
    equipment_required = db.relationship('Equipment', uselist=False, back_populates='course_class')
    # The number of classes identical to this per week
    num_per_week = db.Column(db.Integer) 

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # For calculation results
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))

    # One-To-Many: every row has one day but every day can appear in multiple rows
    day_id = db.Column(db.Integer, db.ForeignKey('day.day_id'))
    # One-To-Many: every row has one classtime but every classtime can appear in multiple rows
    class_time_id = db.Column(db.Integer, db.ForeignKey('class_time.class_time_id'))
    # One-To-Many: every row has one classroom but every classroom can appear in multiple rows
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.classroom_id'))

    # Receives a list of subjects and returns true if the object's subject appears in it.
    def subject_in_list(self, subjects):
        return self.subject in subjects

    # Receives a list of teachers and returns true if the object's teacher appears in it.
    def teacher_in_list(self, teachers):
        return self.teacher in teachers

    # Receives a list of DB StudentsGroup objects and returns
    # a list which represents the intersection between this object's students groups and the received list.
    # Average complexity: O(n)
    def groups_intersection(self, other_lst):
        # Use of hybrid method
        this_lst = self.students_groups
        temp = set(other_lst)
        intersection_lst = [value for value in this_lst if value in temp]
        return intersection_lst


class Schedule(db.Model):
    schedule_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))  # Can be None if the user chooses not to enter a name. 

    # One-To-Many: every Scheduled class belongs to one Schedule but every schedule consists of multiple classes.
    classes = db.relationship('CourseClass', backref='schedule')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    classtimes = db.relationship('ClassTime', backref='schedule')  # Assigned to the database sorted by index
    days = db.relationship('Day', backref='schedule')  # Assigned to the database sorted by index
    classrooms = db.relationship('Classroom', backref='schedule')
    equipments = db.relationship('Equipment', backref='schedule')
    subjects = db.relationship('Subject', backref='schedule')
    students_groups = db.relationship('StudentsGroup', backref='schedule')
    teachers = db.relationship('Teacher', backref='schedule')
    classes = db.relationship('CourseClass', backref='schedule')

    date_created = db.Column(db.DateTime)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    name = db.Column(db.String(150))
    password = db.Column(db.String(150))

    classtimes = db.relationship('ClassTime', backref='user')
    days = db.relationship('Day', backref='user')
    classrooms = db.relationship('Classroom', backref='user')
    equipments = db.relationship('Equipment', backref='user')
    subjects = db.relationship('Subject', backref='user')
    students_groups = db.relationship('StudentsGroup', backref='user')
    teachers = db.relationship('Teacher', backref='user')
    classes = db.relationship('CourseClass', backref='user')

    schedules = db.relationship('Schedule', backref='user')


# Used to insert data to database before website was created.
def insert_data():
    # Adding instances of ClassTime to table
    lesson_1 = ClassTime(start_time="8:00", end_time="8:50", index=1)
    lesson_2 = ClassTime(start_time="8:50", end_time="9:35", index=2)
    lesson_3 = ClassTime(start_time="9:55", end_time="10:40", index=3)
    lessons = [lesson_1, lesson_2, lesson_3]
    db.session.add_all(lessons)
    db.session.commit()

    # Adding instances of Day to table
    sunday = Day(name="Sunday", index=1, last_class_time=lesson_3)
    tuesday = Day(name="Tuesday", index=2, last_class_time=lesson_3)
    thursday = Day(name="Thursday", index=3, last_class_time=lesson_3)
    days = [sunday, tuesday, thursday]
    db.session.add_all(days)
    db.session.commit()

    # Adds instances of Equipment to table
    regular = Equipment(computers_lab=False, physics_lab=False, chemistry_lab=False, biology_lab=False)
    computers_lab = Equipment(computers_lab=True, physics_lab=False, chemistry_lab=False, biology_lab=False)
    physics_lab = Equipment(computers_lab=False, physics_lab=True, chemistry_lab=False, biology_lab=False)
    equipments = [regular, computers_lab, physics_lab]
    db.session.add_all(equipments)
    db.session.commit()

    # Adding instances of Classroom to table
    room_1 = Classroom(name="Room 1", num_seats=40, equipment=regular)
    room_2 = Classroom(name="Room 2", num_seats=35, equipment=computers_lab)
    room_3 = Classroom(name="Room 3", num_seats=37, equipment=physics_lab)
    rooms = [room_1, room_2, room_3]
    db.session.add_all(rooms)
    db.session.commit()

    # Adding instances of Subject to table
    cyber = Subject(name="Cyber", level=10)
    physics = Subject(name="Physics", level=5)
    civics = Subject(name="Civics", level=2)
    computer_science = Subject(name="Computer  Science", level=5)
    history = Subject(name="History", level=2)
    subjects = [cyber, physics, civics, computer_science, history]
    db.session.add_all(subjects)
    db.session.commit()

    # Adding instances of Teacher to table.
    nir = Teacher(name="Nir")
    eli = Teacher(name="Eli")
    oren = Teacher(name="Oren")
    eynat = Teacher(name="Eynat")
    teachers = [nir, eli, oren, eynat]
    db.session.add_all(teachers)
    db.session.commit()

    # Adding instances of StudentsGroup to table
    students_3 = StudentsGroup(name="Yud Bet 3", num_students=35)
    students_4 = StudentsGroup(name="Yud Bet 4", num_students=25)
    students_groups = [students_3, students_4]
    db.session.add_all(students_groups)
    db.session.commit()

    # Links between subjects and teachers, subjects and students groups (adds subjects to the teachers/groups).
    nir.subjects.append(cyber)
    nir.subjects.append(computer_science)
    eli.subjects.append(cyber)
    oren.subjects.append(physics)
    eynat.subjects.append(civics)
    eynat.subjects.append(history)
    db.session.commit()

    students_3.subjects.append(cyber)
    students_3.subjects.append(physics)
    students_3.subjects.append(civics)
    db.session.commit()

    students_4.subjects.append(cyber)
    students_4.subjects.append(physics)
    students_4.subjects.append(civics)
    db.session.commit()

    # Add instances of CourseClass to table, and links them to students groups (adds groups to the classes)
    # In One-To-Many and One-To-One relationships, the constructor receives the values (they don't need to be added to some list after the instance has been created).

    CourseClasses = []

    # Civics for students_3
    CourseClasses.append(CourseClass(subject=civics, teacher=eynat, equipment_required=regular))
    CourseClasses.append(CourseClass(subject=civics, teacher=eynat, equipment_required=regular))
    CourseClasses[0].students_groups.append(students_3)
    CourseClasses[1].students_groups.append(students_3)
    db.session.commit()

    # Civics for students_4
    CourseClasses.append(CourseClass(subject=civics, teacher=eynat, equipment_required=regular))
    CourseClasses.append(CourseClass(subject=civics, teacher=eynat, equipment_required=regular))
    CourseClasses.append(CourseClass(subject=civics, teacher=eynat, equipment_required=regular))
    CourseClasses[2].students_groups.append(students_4)
    CourseClasses[3].students_groups.append(students_4)
    CourseClasses[4].students_groups.append(students_4)
    db.session.commit()

    # Cyber for students_3
    CourseClasses.append(CourseClass(subject=cyber, teacher=nir, equipment_required=computers_lab))
    CourseClasses.append(CourseClass(subject=cyber, teacher=nir, equipment_required=computers_lab))
    CourseClasses.append(CourseClass(subject=cyber, teacher=nir, equipment_required=computers_lab))
    CourseClasses[5].students_groups.append(students_3)
    CourseClasses[6].students_groups.append(students_3)
    CourseClasses[7].students_groups.append(students_3)
    db.session.commit()


    # Cyber for students_4
    CourseClasses.append(CourseClass(subject=cyber, teacher=eli, equipment_required=computers_lab))
    CourseClasses.append(CourseClass(subject=cyber, teacher=eli, equipment_required=computers_lab))
    CourseClasses.append(CourseClass(subject=cyber, teacher=eli, equipment_required=computers_lab))
    CourseClasses.append(CourseClass(subject=cyber, teacher=eli, equipment_required=computers_lab))
    CourseClasses[8].students_groups.append(students_4)
    CourseClasses[9].students_groups.append(students_4)
    CourseClasses[10].students_groups.append(students_4)
    CourseClasses[11].students_groups.append(students_4)
    db.session.commit()

    # Physics for students_3
    CourseClasses.append(CourseClass(subject=physics, teacher=oren, equipment_required=physics_lab))
    CourseClasses.append(CourseClass(subject=physics, teacher=oren, equipment_required=physics_lab))
    CourseClasses.append(CourseClass(subject=physics, teacher=oren, equipment_required=physics_lab))
    CourseClasses.append(CourseClass(subject=physics, teacher=oren, equipment_required=physics_lab))
    CourseClasses[12].students_groups.append(students_3)
    CourseClasses[13].students_groups.append(students_3)
    CourseClasses[14].students_groups.append(students_3)
    CourseClasses[15].students_groups.append(students_3)
    db.session.commit()

    # Physics for students_4
    CourseClasses.append(CourseClass(subject=physics, teacher=oren, equipment_required=physics_lab))
    CourseClasses.append(CourseClass(subject=physics, teacher=oren, equipment_required=physics_lab))
    CourseClasses[16].students_groups.append(students_4)
    CourseClasses[17].students_groups.append(students_4)
    db.session.commit()

    db.session.add_all(CourseClasses)
    db.session.commit()

