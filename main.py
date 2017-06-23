#!/usr/local/bin/python3

from __future__ import print_function
import csv
from tools import get_file
from pprint import PrettyPrinter
from tabulate import tabulate
from termcolor import colored

pp = PrettyPrinter(indent=4)

# Read the home school and host school registration records, create student 
# and class records, and identify any students not registered in both systems.

class Institution():

    def __init__(self, name):
        self.name = name
        self.students = {}
        self.read_home_roster()
        self.read_foreign_roster()

    def add_student(self, *args, **kwargs):

        # Create a Student object and add it to the dict of the institution's students.

        s = Student(*args, **kwargs)
        self.students[s.name] = s

    def make_dict(self, location, student_id_column, course_section_column):

        # Turn a CSV into a three-level dictionary containing the same data.
        # The dicts look like: data = {student_id: {class_1: {'header like Student Name': 'value like Joe Schmoe',
        #                                                     'header like Birth Date': 'value like 04/19/2000'}...}...}

        data = {}
        with open(location, 'r') as infile:
            reader = csv.reader(infile)
            headers = next(reader)
            for row in reader:

                # Use student home institution IDs as the first-level dict key.

                p_key = row[student_id_column]
                if not p_key in data:
                    data[p_key] = {}
                course = row[course_section_column]

                # Use the host institution's course section name as the second-level dict key.

                data[p_key][course] = {}
                for i, val in enumerate(row):

                    # Name the third-level keys after the CSV's original headers.

                    data[p_key][course][headers[i]] = val
        print('Read {} student records from {}.\n'.format(len(data), location))
        return data

    def read_home_roster(self):

        # Read the SIS output data from the students' home institution.

        csv_file = get_file('IntegCrsOff_BCB2BCM_*.csv', target_dir='/home/iroh/cross-reg/')
        data = self.make_dict(csv_file, student_id_column=9, course_section_column=6)

        # Interpret the data by creating Student objects and adding them to institution.students.

        for student_id in data:
            courses = data[student_id]
            for course in courses:
                record = courses[course]
                if not student_id in self.students:
                    self.add_student(name=student_id, data=record)

        # Add each class that the student is in to the student's home registrations list.

                student = self.students[student_id]
                record['active'] = (record['Add or Drop'] == 'Add')
                names = {'eff date': 'Last Revision', 'grade': 'Final Grade', 'active': 'active'}
                student.register(mode='home', course_sec=course, course_data=record, names=names)


    def read_foreign_roster(self):

        # Read the SIS output data from the host institution.

        csv_file = get_file('BoCo Integrated Offerings Registrations for A Given Term*.csv', target_dir='/home/iroh/Downloads')
        data = self.make_dict(csv_file, student_id_column=0, course_section_column=3)

        # Some students without home institution IDs entered into the host system, either
        # because their data was entered incompletely or not at all or because they are not students
        # from this institution at all, will all get crammed into data[''].
        # Delete data[''] for that reason and handle these instead later with: try: data[student_id]; except KeyError: ...

        del(data[''])

        # Interpret the data by creating Student objects and adding them to institution.students.

        for student_id in data:
            courses = data[student_id]
            for course in courses:
                record = courses[course]
                host_equivs = {'Student': record['Name'], 'BCM_StudID': record['Berklee ID'], 'DOB': None,
                               'Email': None}
                for equiv in host_equivs:
                    record[equiv] = host_equivs[equiv]
                if not student_id in self.students:
                    self.add_student(name=student_id, data=record)

        # For each student, find their registrations at the host school and add them to 
        # the student's host registrations list.

        for student_id in self.students:
            student = self.students[student_id]
            try:
                student_registrations = data[student_id]
                for course in student_registrations:
                    record = student_registrations[course]
                    record['active'] = (record['Status- Current'][0] in ['A', 'N'])
                    names = {'eff date': 'Chg- Date', 'grade': 'Grade- Verified', 'active': 'active'}
                    student.register(mode='foreign', course_sec=course, course_data = record, names=names)

        # If the student isn't on the host registrations list, and should be according to the home institution,
        # then raise this error containing the information needed to add them to the host SIS.
        # TODO: update this to print out in a nice table like the other errors.

            except KeyError:
                if student.active:
                    print('Active student {} missing Colleague data:'.format(student.real_name))
                    print('Berklee ID: {}'.format(student.for_key.zfill(7)))
                    print('BoCo ID:', student_id.zfill(9))
                    print('Birth date: {}'.format(student.dob))
                    print('Email: {}'.format(student.email))
                    print('home registrations:')
                    pp.pprint(student.registrations['home'])
                    print()


class Student():

    def __init__(self, name, data):
        
        # Save student data from the dictionary that came from the CSV.
        
        self.name = name #home key
        self.real_name = data['Student']
        self.for_key = data['BCM_StudID']
        self.dob = data['DOB']
        self.email = data['Email']
        self.registrations = {'home': {}, 'foreign': {}}
        self.active = False

        # Hack to deal with missing host school IDs from home school data.
        # Some students will not be in host school SIS yet at all; handle this later during read_foreign_roster.

        try:
            from ids_hack import ids as missing_ids
            if not self.for_key and name in missing_ids:
                self.for_key = missing_ids[name]

        except ImportError:
            missing_ids = {}


    def register(self, mode, course_sec, course_data, names):

        # Save course data from the dictionary that came from the CVS.

        self.registrations[mode][course_sec] = {}
        for name in names:
            self.registrations[mode][course_sec][name] = course_data[names[name]]
        if course_data['active'] and mode == 'home':
            self.active = True


    def reckon(self):
    
        updates = {'Home System': [], 'Host System': []}

        # Evaluate the home school registrations for missing data in the host school.

        for course in self.registrations['home']:
            course_data = self.registrations['home'][course]
            show_status = {0: colored('Drop', 'red', attrs=['bold']), 1: colored('Add', 'green', attrs=['bold'])}
            log = [self.real_name, self.name.zfill(9), self.for_key.zfill(7), course,
                   show_status[course_data['active']], course_data['grade'], course_data['eff date']]
            if course in self.registrations['foreign']:
                if not course_data['active'] == self.registrations['foreign'][course]['active']:
                    updates['Host System'].append(log)
                if not course_data['grade'] == self.registrations['foreign'][course]['grade']:
                    log[4] = 'Update with Grade'
                    updates['Host System'].append(log)
            elif course_data['active']:
                     updates['Host System'].append(log)

        # Check the host school registrations for missing data in the home school system.

        for course in self.registrations['foreign']:
            course_data = self.registrations['foreign'][course]
            log = [self.real_name, self.name.zfill(9), self.for_key.zfill(7), course,
                  colored('Appears in host but not home system?', 'red', attrs=['bold']), course_data['eff date']]
            if not course in self.registrations['home'] and course_data['active']:
                updates['Home System'].append(log)

        return updates

def main():

    # Create an institution object for my use case, the Boston Conservatory.
    print()
    boco = Institution('Boston Conservatory')

    all_output = {'Host System': [], 'Home System': []}
    for student_id in sorted(boco.students):
        stud = boco.students[student_id]
        output = stud.reckon()
        for system in all_output:
            to_append = output[system]
            for line in to_append:
                all_output[system].append(line)
    heads = ['Name', 'BoCo ID', 'Berklee ID', 'Class', 'What To Do', 'Grade', 'Update Date']
    translations = {'Home System': 'PowerCampus', 'Host System': 'Colleague'}
    for system in all_output:
        if all_output[system]:
            print(colored('Updates for {}\n'.format(translations[system]), attrs=['bold']))
            print(tabulate(sorted(all_output[system]), headers=heads), '\n')
    return boco

if __name__ == '__main__':
    main()
