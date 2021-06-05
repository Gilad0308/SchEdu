
from web_app.algorithm_classes.for_Algorithm import (
    ClassTime, Day, Equipment, Classroom, Subject,
    Teacher, StudentsGroup, CourseClass, Schedule
)

import random
import time
# import matplotlib.pyplot as plt


class Algorithm:

    # Receives:
    # A list of the classes (CourseClass objects) that should be placed in certain day, class time and classroom.
    # Three lists of the days, class times and classrooms classes can be assigned to.\
    # Each place in the schedule of day, hour and room is reffered to as "slot".
    def __init__(self, CourseClasses, days, class_times, classrooms):
        self.CourseClasses = CourseClasses
        self.days = sorted(days, key=Algorithm.get_index)
        self.class_times = sorted(class_times, key=Algorithm.get_index)
        self.classrooms = classrooms
        # A list of the best fitness scores in every generation to track the progress of the algorithm.
        # The absolute value of the fitness scores are saved
        self.best_fitness_scores = []
        # The number of generations without any progress in fitness score
        self.no_progress = 0

    # Receives a day or a class_time object and returns its index
    def get_index(day_or_hour):
        return day_or_hour.index


    # Stage in algorithm: Initial population
    # Receives the number of initial elements to create
    # Creates schedules with the classes, each one of them will be given a random day, class time and classroom.
    # Returns a list of those schedules.
    def generate_initial_schedules(self, num_elements):
        schedules_list = []
        for i in range(num_elements):
            current_assigning_dict = {}
            for current_class in self.CourseClasses:
                day = random.choice(self.days)
                class_time = random.choice(self.day_class_times(day))
                classroom = random.choice(self.classrooms)
                current_assigning_dict[current_class] = (day, class_time, classroom)

            schedules_list.append(Schedule(current_assigning_dict))

        return schedules_list


    # Receives a certain Day object and returns a list of the class times that can be in this day,
    # according to the last class time of the day.
    def day_class_times(self, day):
        valid_class_times = []
        for class_time in self.class_times:
            if class_time.index <= day.last_class_time.index:
                valid_class_times.append(class_time)
        return valid_class_times


    # Stage in algorithm: Fitness
    # Calculates the fitness scores for all schedules.
    def calculate_fitness(self, schedules_list):
        for schedule in schedules_list:
            self.evaluate_schedule(schedule)


    # Stage in algorithm: Fitness
    # Receives a Schedule and returns its total fitness score according to its suitablility to the fitness criteria.
    def evaluate_schedule(self, schedule):
        assigning_dict = schedule.assigning_dict
        total_score = 0  # Decremented (in 1) for every fitness paramter a CourseClasss doesn't fulfill.
        schedule.conflicts_dict = {"same slot": 0, "equipment": 0, "number of seats": 0, "teacher time": 0, "group time": 0}
        conflicts_dict = schedule.conflicts_dict
        
        for current_class in assigning_dict:
            current_slot = assigning_dict[current_class]

            # A dictionary of the classes and their slots that are assigned to the same day and class time as the current.
            # Doesn't include the current class.
            same_time_classes = {}
            for other_class in assigning_dict:
                other_slot = assigning_dict[other_class]
                if other_class.id != current_class.id:
                    if other_slot[0].id == current_slot[0].id and other_slot[1].id == current_slot[1].id:
                        same_time_classes[other_class] = other_slot
            
            # Fitness criterion: was the class placed in the same slot (day, class time, classroom) with other classes.
            for other_class in same_time_classes:
                other_slot = same_time_classes[other_class]
                if other_slot[2].id == current_slot[2].id:
                    total_score -= 1
                    conflicts_dict["same slot"] += 1

            # Fitness criterion: was the class placed in a room which has all the required equipment.
            if not current_slot[2].equipment.satisfies_requirements(current_class.equipment_required):
                total_score -= 1
                conflicts_dict["equipment"] += 1

            # Fitness criterion: was the class placed in a room with enough seats for all the students.
            if current_slot[2].num_seats < current_class.num_seats_required:
                total_score -= 1
                conflicts_dict["number of seats"] += 1

            # Fitness criterion: was the teacher assigned to teach more than one class at the same time (day and hour).
            for other_class in same_time_classes:
                if other_class.teacher.id == current_class.teacher.id:
                    total_score -= 1
                    conflicts_dict["teacher time"] += 1
                    break

            # Fitness criterion: was the students groups assigned to study more than one class at the same time (day and hour).
            # *Can be optimized to distinguish between a conflict with one group of students and with several groups.
            conflict = [False]
            for other_class in same_time_classes:
                
                for current_group in current_class.students_groups:
                    for other_group in other_class.students_groups:
                        if other_group.id == current_group.id:
                            total_score -= 1
                            conflicts_dict["group time"] += 1
                            conflict[0] = True
                            break
                    # Change this to distinguish between a conflict with one group of students and with several groups.
                    if conflict[0]:
                        break
                
                if conflict[0]:
                    break

        schedule.fitness_score = total_score


    # Stage in algorithm: Selection
    # Receives a list of schedules and the number of schedules to select.
    # Returns this number of schedules with the best fitness scores.
    # In addition, checks if there is progress in the fitness values over generations.
    def select_fittest_schedules(self, schedules_list, num_to_select):
        schedules_list.sort(key=self.fitness_score, reverse=True)
        current_best_score = abs(schedules_list[0].fitness_score)
        
        if len(self.best_fitness_scores) > 0:
            if current_best_score >= self.best_fitness_scores[-1]:
                self.no_progress += 1
            else:
                self.no_progress = 0
        self.best_fitness_scores.append(current_best_score)
        return schedules_list[0:num_to_select]

    # Receives a schedule and returns its fitness score (in order to sort the schedules by fitness).
    def fitness_score(self, schedule):
        return schedule.fitness_score


    # Stage in algorithm: Crossover
    # Creates a new generation of schedules by combining data in every two different schedules from those which were selected.
    # ***Can be optimized to crossover between every two schedules only once (currently its twice).
    def schedules_crossover(self, selected_schedules):
        new_generation_schedules = []
        for schedule_1 in selected_schedules:
            for schedule_2 in selected_schedules:
                if schedule_1 is not schedule_2:
                    new_schedule = self.two_schedules_crossover(schedule_1, schedule_2)
                    new_generation_schedules.append(new_schedule)

        return new_generation_schedules


    # Stage in algorithm: Crossover
    # Receives two schedules and combines the tuples of day, time and rooms in both of them
    # with the classes (both of them have the same classes) to a dictionary in a new schedule.
    # Returns the new schedule.
    def two_schedules_crossover(self, schedule_1, schedule_2):
        current_schedule = schedule_1
        original_assigning_dict = schedule_1.assigning_dict
        new_assigning_dict = {}
        num_classes = len(original_assigning_dict)
        num_to_pick = random.randint(1, int(num_classes/2))
        
        for current_class in original_assigning_dict:
            new_slot = current_schedule.assigning_dict[current_class]
            new_assigning_dict[current_class] = new_slot
            num_to_pick -= 1

            if num_to_pick == 0:
                num_to_pick = random.randint(1, int(num_classes/2))
                if current_schedule is schedule_1:
                    current_schedule = schedule_2
                else:
                    current_schedule = schedule_1

        return Schedule(new_assigning_dict)


    # Stage in algorithm: Mutation
    # Receives a schedule.
    # Picks a random class from the assigning dictionary and gives it a new randomly generated slot (day, class time, classroom).
    def new_place_mutation(self, schedule):
        # pick a random class
        picked_class = random.choice(list(schedule.assigning_dict.keys()))
        current_slot = schedule.assigning_dict[picked_class]
        
        new_slot = current_slot
        # Place the class to move in a new randomly chosen slot
        while new_slot == current_slot:
            day = random.choice(self.days)
            class_time = random.choice(self.day_class_times(day))
            classroom = random.choice(self.classrooms)
            new_slot = (day, class_time, classroom)

        schedule.assigning_dict[picked_class] = new_slot


    # Stage: Mutation
    # Receives a schedule
    # Randomly chooses two classes from the assigning dictionary and swaps between their slots (day, class time, classroom).
    def swap_classes_mutation(self, schedule):
        # pick two random classes
        dict_classes_list = list(schedule.assigning_dict.keys())
        class_1 = random.choice(dict_classes_list)
        class_2 = random.choice(dict_classes_list)
        while class_2.is_same(class_1):
            class_2 = random.choice(dict_classes_list)

        # swaps between the tuples of the two classes
        new_slot_1 = schedule.assigning_dict[class_2]
        new_slot_2 = schedule.assigning_dict[class_1]

        schedule.assigning_dict[class_1] = new_slot_1
        schedule.assigning_dict[class_2] = new_slot_2


    # Stage of algorithm: Mutation
    # Receives the list of selected schedules, mutation size, mutation chance, and chance for swap place mutation.
    # Performs a mutation in some random schedules according to the mutation chance.
    # The mutation size defines the number of changes to perform in a single schedule.
    # Before change in a schedule randomly picks the type of the mutation to perform.
    def schedules_mutation(self, schedules, mutation_size, mutation_chance, new_place_chance):
        for schedule in schedules:
            mutate = random.random()
            if mutate < mutation_chance:
                for i in range(mutation_size):
                    new_place = random.random()
                    if new_place < new_place_chance:
                        self.new_place_mutation(schedule)
                    else:
                        self.swap_classes_mutation(schedule)


    # According to the data received, performs the genetic algorithm and creates generations of schedules
    # until a perfect schedule with no conflicts is created, or after a certain number of generations 
    # with no progress in fitness score.
    # If the algorithm succeeds to create a perfect schedule, returns True and the schedule.
    # If the algorithm fails, returns False, and a list of messages containing the conflicts.
    def perform_algorithm(self):
        # In case same algorithm was performed more than once
        self.best_fitness_scores = []
        self.no_progress = 0
        
        num_elements = 10
        num_to_select = 10
        mutation_size = 1  # The number of changes in a schedule if it have had a mutation.
        mutation_chance = 0.5  # The probability that a mutation will occure in a schedule.
        new_place_chance = 0.5  # 1 minus 'new_place_chance' is the chance for swap classes mutation.
        no_progress_stop = 150  # The number of generations without progress in fitness score , that after them the program will stop.

        current_generation = self.generate_initial_schedules(num_elements)
        previous_generation = [None]
        gen_num = 0
        while True:

            self.calculate_fitness(current_generation)

            """
            print(f"Genereation {gen_num} fitness scores: ")
            for schedule in current_generation:
                print(f"{schedule.fitness_score}, ")
            print("\n")
            """

            selected_schedules = []
            if previous_generation[0] is None:
                selected_schedules = self.select_fittest_schedules(current_generation, num_to_select)
            else:
                selected_schedules = self.select_fittest_schedules(current_generation + previous_generation, num_to_select)

            # Conditions to stop calculation.
            if selected_schedules[0].fitness_score == 0:
                print("Calculated " + str(gen_num) + " generations")
                return True, selected_schedules[0]
            if self.no_progress > no_progress_stop:
                print("Calculated " + str(gen_num) + " generations")
                return False, self.conflicts_messages(selected_schedules[0])

            new_generation = self.schedules_crossover(selected_schedules)
            self.schedules_mutation(new_generation, mutation_size, mutation_chance, new_place_chance)
            previous_generation = current_generation  # Commenting this line will abolishing the use of the previous generation
            current_generation = new_generation
            gen_num += 1


    # This function is called if the program failed to create a perfect schedule (with zero conflicts)
    # Receives the schedule with the best fitness score and returns a list of messages suitable to the conflicts it has.
    def conflicts_messages(self, schedule):
        conflicts_dict = schedule.conflicts_dict
        messages = []
        
        if conflicts_dict["same slot"] > 0:
            messages.append("Schedule conflict: can't assign class/es to different day, hour and classroom")
        if conflicts_dict["equipment"] > 0:
            messages.append("Schedule conflict: can't satisfy all equipment rquirements")
        if conflicts_dict["number of seats"] > 0:
            messages.append("Schedule conflict: can't assign class/es to classroom/s with enough seats")
        if conflicts_dict["teacher time"] > 0:
            messages.append("Schedule conflict: can't assign class/es with the same teacher to different day, hour and classroom")
        if conflicts_dict["group time"] > 0:
            messages.append("Schedule conflict: can't assign class/es with the same study group to different day, hour and classroom")
        return messages
        

    # Runs the function perform_algorithm and displays a graph that shows the progress of the schedules through out the generations.
    def run(self):
        # Check for conditions that don't allow the algorithm to run properly
        messages = []
        if len(self.CourseClasses) < 2:
            messages.append("Needs at least two classes in order to create schedule.")
        if self.less_than_two_slots():
            messages.append("Needs at least two differet combinations of day, hour and classroom, in order to create schedule.")
        if len(messages) > 0:
            return False, messages
        
        start = time.time()
        result = self.perform_algorithm()
        end = time.time()
        print(f"Algorithm Calculation took {end-start} seconds.")
        # Algorithm.progress_graph(self.best_fitness_scores)

        return result


    # A function that checkes if there are less than two slots (combinations of day, classtime and classroom)
    # Returns true if there are less than two, else returns false.
    def less_than_two_slots(self):
        num_slots = 0
        for day in self.days:
            num_slots += day.last_class_time.index
        num_slots = num_slots*len(self.classrooms)

        if num_slots < 2:
            return True
        return False


    # Displays a graph that shows the decline in the number of conflicts (improved fitness) over generations.
    # Should be called from a separate thread, to avoid interrupting the communication between the client and server.
    def progress_graph(best_fitness_scores):
        # x axis values 
        x = range(len(best_fitness_scores))
        # corresponding y axis values 
        y = best_fitness_scores
        
        # plotting the points  
        plt.plot(x, y) 
        
        # naming the x axis 
        plt.xlabel('Generation') 
        # naming the y axis 
        plt.ylabel('Conflicts') 
        
        # giving a title to the graph 
        plt.title('Conflicts(Generation)') 
        
        # function to show the plot 
        plt.show()
