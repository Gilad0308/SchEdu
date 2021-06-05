# All the classes for the algorithm calculation.


class ClassTime:

    def __init__(self, id, start_time, end_time, index):
        self.id = id
        self.start_time = start_time  # The time the lesson starts - a string. For example: 9:55
        self.end_time = end_time  # The time the lesson ends - a string. For example: 10:40
        # The number of the lesson in the day (starting from 1). The indexes of all classtimes have to be sequential, 
        # and they represent the order of them in the day
        self.index = index

    def __str__(self):
        return f"Class Time: id: {self.id}, start time: {self.start_time}, end time: {self.end_time}, lesson number: {self.index}"


class Day:

    def __init__(self, id, name, index, last_class_time):
        self.id = id
        self.name = name
        # The number of the day in the week (starting from 1). The indexes of all days have to be sequential, 
        # and they represent the order of them in the week
        self.index = index
        self.last_class_time = last_class_time

    def __str__(self):
        return f"Day: id: {self.id}, name: {self.name}, day number: {self.index}, last lesson in day: {self.last_class_time.index}"


class Equipment:

    def __init__(self, is_comp_lab=False, is_phy_lab=False, is_chem_lab=False, is_bio_lab=False):
        self.is_comp_lab = is_comp_lab  # Whether or not the room has computers (assumes that if it's true there is a computer for each seat).
        self.is_phy_lab = is_phy_lab  # Whether or not the there is equipment for physics teaching and experiments.
        self.is_chem_lab = is_chem_lab  # Whether or not there is equipment for chemistry teaching and experiments.
        self.is_bio_lab = is_bio_lab  # Whether or not there is equipment for bilology teaching and experiments.

    # Receives an Equipment object and returns if its the same as this (doesn't check identidy)
    def is_same(self, other):
        is_same = self.is_comp_lab == other.is_comp_lab and self.is_phy_lab == other.is_phy_lab
        is_same = is_same and self.is_chem_lab == other.is_chem_lab and self.is_bio_lab == other.is_bio_lab
        return is_same
    
    # Receives another Equipment object that represents the equipment requirements of a class,
    # and returns true if it satisfys these requirements.
    def satisfies_requirements(self, requirements):
        if requirements.is_comp_lab:
            if not self.is_comp_lab:
                return False
        if requirements.is_phy_lab:
            if not self.is_phy_lab:
                return False
        if requirements.is_chem_lab:
            if not self.is_chem_lab:
                return False
        if requirements.is_bio_lab:
            if not self.is_bio_lab:
                return False
        
        return True

    def __str__(self):
        has_equipment = False
        description = ""
        if self.is_comp_lab:
            description += "Computers"
            has_equipment = True
        if self.is_phy_lab:
            if has_equipment:
                description += ", Physics lab"
            else:
                description += "Physics lab"
                has_equipment = True
        if self.is_chem_lab:
            if has_equipment:
                description += ", Chemistry lab"
            else:
                description += "Chemistry lab"
                has_equipment = True
        if self.is_bio_lab:
            if has_equipment:
                description += ", Biology lab"
            else:
                description += "Biology lab"
                has_equipment = True

        if not has_equipment:
            description += "No equipment"
        description += " "
        
        return description


class Classroom:

    def __init__(self, id, name, num_seats, equipment):
        self.id = id
        self.name = name
        self.num_seats = num_seats
        self.equipment = equipment

    def __str__(self):
        return f"Classroom: id: {self.id}, name: {self.name}, num_seats: {self.num_seats}, equipment: {self.equipment.__str__()} "


class Subject:

    def __init__(self, id, name, level):
        self.id = id
        self.name = name
        self.level = level  # The level the subject in "study points". For example: 5 points Mathematics.

    def __str__(self):
        return f"Subject: Id: {self.id}, name: {self.name}, level: {self.level}"


class Teacher:
 
    def __init__(self, id, name, teaching_subjects):
        self.id = id
        self.name = name
        # A list of the subjects a teacher is teaching.
        self.teaching_subjects = teaching_subjects

    # Currently without description of the teaching subjects.
    def __str__(self):
        return f"Teacher: Id: {self.id}, name: {self.name} "


class StudentsGroup:

    def __init__(self, id, name, num_students, studying_subjects):
        self.id = id
        self.name = name
        self.num_students = num_students
        # A list of the subjects the students are studying.
        self.studying_subjects = studying_subjects

    # Currently without description of the studying subjects.
    def __str__(self):
        return f"Students Group: id: {self.id}, name: {self.name}, number of students: {self.num_students} "


class CourseClass:

    def __init__(self, id, subject, teacher, students_groups, equipment_required):
        self.id = id
        self.subject = subject  # Subject object.
        self.teacher = teacher  # Teacher object of the teacher teaching the class.
        
        # A list of the students groups participating in the class.
        # For example: Yud Bet 3 - 5 points Physics, Yud Bet 4 - 5 points Physics and Yud Bet 5 - 5 points Physics.
        self.students_groups = students_groups

        self.equipment_required = equipment_required  # The equipment needed for the class.

        self.num_seats_required = 0  # The number of seats needed for a lesson with all the groups in the course.
        for group in students_groups:
            self.num_seats_required += group.num_students


    # Receives a CourseClass object and returns true if it the same as this (doesn't check identity)
    def is_same(self, other):
        if self.id == other.id:
            return True
        is_same = self.subject.id == other.subject.id and self.teacher.id == other.teacher.id
        is_same = is_same and self.equipment_required.is_same(other.equipment_required)
        if not is_same:
            return False
        if len(self.students_groups) != len(other.students_groups):
            return False
        for this_group in self.students_groups:
            found = [False]
            for other_group in other.students_groups:
                if other_group.id == this_group.id:
                    found[0] = True
            if not found[0]:
                return False
        
        return True
    

    def __str__(self):
        students_groups_str = "Participating: "
        for group in self.students_groups:
            add = "\n\t\t\t"  + group.__str__()
            students_groups_str += add
        return f"Class: \n\t\tId: {self.id} \n\t\t{self.subject.__str__()} \n\t\t{self.teacher.__str__()} \
        \n\t\t{students_groups_str} \n\t\tequipment required: {self.equipment_required.__str__()} \
        \n\t\tnumber of seats required: {self.num_seats_required} "


class Schedule:

    # Receives a dictionary whose keys are CourseClass objects (refferences to those objects) and its values are tuples.
    # Each tuple consists of a Day, ClassTime, Classroom objects that represent it's place in the schedule.
    def __init__(self, assigning_dict):
        self.assigning_dict = assigning_dict
        self.fitness_score = 0
        # A dictionary whose keys are the type of conflict/criteria not fulfilled, and values are the number each conflict occures in the schedule.
        # This attribute is needed in order to detect the type of conflicts that the schedule still has, if the algorithm failes.
        # Its keys and values are assigned when the algorithm runs, according to the fitness criteria chosen.
        self.conflicts_dict = {}