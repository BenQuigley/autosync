import csv
from tools import get_file
from pprint import PrettyPrinter
from ids_hack import ids as missing_ids
from tabulate import tabulate

# Read the BoCo and Berklee rosters, create student and class records, 
# and identify any students not registered in both systems.

pp = PrettyPrinter(indent=4)

class Institution():
    def __init__(self, name):
        self.name = name
        self.students = {}

    def add_student(self, *args, **kwargs):

        # Create a Student object and add it to the dict of the institution's students.

        s = Student(*args, **kwargs)
        self.students[s.name] = s

    def make_dict(self, location, student_id_column, course_section_column):

        # Make a big dictionary of data from a file.
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
        print('Read {} student records from {}.'.format(len(data), location))
        return data

    def read_home_roster(self):

        # Read the SIS output data from the students' home institution:

        data = self.make_dict('/home/iroh/cross-reg/IntegCrsOff_BCB2BCM_2017-01-26.csv',
                              student_id_column=9, course_section_column=6)

        # Interpret the data by creating Student objects:

        for student_id in data:
            courses = data[student_id]
            for course in courses:
                record = courses[course]
                if not student_id in self.students:
                    self.add_student(name=student_id, data=record)
                student = self.students[student_id]
                record['active'] = (record['Add or Drop'] == 'Add')
                names = {'eff date': 'Last Revision', 'grade': 'Final Grade', 'active': 'active'}
                student.register(mode='home', course_sec=course, course_data=record, names=names)


    def read_foreign_roster(self):

        # Read the SIS output data from the host institution:

        data = self.make_dict('/home/iroh/Downloads/BoCo Integrated Offerings Registrations for A Given Term.csv',
                              student_id_column=0, course_section_column=3)

        # Some students without home institution IDs entered into the host system, either
        # because their data was entered incompletely or not at all or because they are not students
        # from this institution at all, will all get crammed into data[''].
        # Delete data[''] for that reason and raise them in a few lines with try: data[student_id]; except KeyError: ...

        del(data[''])

        for student_id in self.students:
            student = self.students[student_id]
            try:
                student_registrations = data[student_id]
                for course in student_registrations:
                    record = student_registrations[course]
                    record['active'] = (record['Status- Current'][0] in ['A', 'N'])
                    names = {'eff date': 'Chg- Date', 'grade': 'Grade- Verified', 'active': 'active'}
                    student.register(mode='foreign', course_sec=course, course_data = record, names=names)
            except KeyError:
                if student.active:
                    pass
                    print('Active student {} missing Colleague data:'.format(student.real_name), 'Berklee ID: {}'.format(student.for_key.zfill(7)), 'BoCo ID:', student_id.zfill(9), sep='\n')
                    print('home registrations:')
                    pp.pprint(student.registrations['home'])
                    print('foreign registrations:')
                    pp.pprint(student.registrations['foreign'])

class Student():

    def __init__(self, name, data):
        self.name = name #home key
        self.real_name = data['Student']
        self.for_key = data['BCM_StudID']
        self.registrations = {'home': {}, 'foreign': {}}
        self.active = False

        # Hack to deal with missing Berklee IDs from BoCo Data.
        # Some students will not be in host school SIS yet at all; handle this later during read_foreign_roster.

        if not self.for_key and name in missing_ids:
                self.for_key = missing_ids[name]


    def register(self, mode, course_sec, course_data, names):
        # Save the column headers for the respective
        course_sec = course_sec.replace('LAHS-223W-001', 'LAHS-223-W001')
        self.registrations[mode][course_sec] = {}
        for name in names:
            self.registrations[mode][course_sec][name] = course_data[names[name]]
        if course_data['active'] and mode == 'home':
            self.active = True


    def reckon(self):
        errors = []

        # Check the home school registrations for courses that have the wrong status in the 
        # host school, or that don't appear in the host school.
    
        for course in self.registrations['home']:
            course_data = self.registrations['home'][course]
            log = [self.real_name, self.name.zfill(9), self.for_key.zfill(7), course,
                   {0: 'Drop', 1: 'Add'}[course_data['active']], course_data['eff date']]
            if course in self.registrations['foreign']:
                if not course_data['active'] == self.registrations['foreign'][course]['active']:
                    errors.append(log)
            elif course_data['active']:
                     errors.append(log)

        # Check the host school registrations for active courses that don't appear 
        # in the home school.

        for course in self.registrations['foreign']:
            course_data = self.registrations['foreign'][course]
            log = [self.real_name, self.name.zfill(9), self.for_key.zfill(7), course,
                  'Never Added', course_data['eff date']]
            if not course in self.registrations['home'] and course_data['active']:
                errors.append(log)

        return errors

def main():

    # Doing work

    boco = Institution('Boston Conservatory')
    boco.read_home_roster()
    boco.read_foreign_roster()
    output = []
    for student_id in sorted(boco.students):
        stud = boco.students[student_id]
        errors = stud.reckon()
        if errors:
            for error in errors:
                output.append(error)
    #print(output)
    print(tabulate(output, headers=['Name', 'BoCo ID', 'Berklee ID', 'Class', 'Add / Drop', 'Update Date']))

if __name__ == '__main__':
    main()
