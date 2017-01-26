import csv
from tools import get_file
from pprint import PrettyPrinter
from dateutil import parser
from ids_hack import ids as missing_ids
# Read the BoCo and Berklee rosters, create student and class records, 
# and identify any students not registered in both systems.

pp = PrettyPrinter(indent=4)

class Institution():
    def __init__(self, name):
        self.name = name
        self.students = {}

    def add_student(self, **kwargs):
        s = Student(**kwargs)
        self.students[s.name] = s

    def make_dict(self, location, student_id_column, course_section_column):

        # Make a big dictionary of the data:

        data = {}
        with open(location, 'r') as infile:
            reader = csv.reader(infile)
            headers = next(reader)
            for row in reader:
                p_key = row[student_id_column]
                if not p_key in data:
                    data[p_key] = {}
                course = row[course_section_column]
                data[p_key][course] = {}
                for i, val in enumerate(row):
                    data[p_key][course][headers[i]] = val
        print('Read', len(data), 'student records from', location)
        return data

    def read_home_roster(self):
        data = self.make_dict('/home/iroh/cross-reg/IntegCrsOff_BCB2BCM_2017-01-25.csv',
                              student_id_column=9, course_section_column=6)

        # Interpret the data by creating Student objects:

        for student_id in data:
            courses = data[student_id]
            for course in courses:
                record = courses[course]
                if not student_id in self.students:
                    self.add_student(name=student_id, real_name=record['Student'], for_key=record['BCM_StudID'])
                student = self.students[student_id]
                active = (record['Add or Drop'] == 'Add')
                student.register_home(course, active=active, date=record['Last Revision']) # or use parser.parse if you want to
                #pp.pprint(record)

    def read_foreign_roster(self):
        data = self.make_dict('/home/iroh/Downloads/BoCo Integrated Offerings Registrations for A Given Term.csv',
                              student_id_column=0, course_section_column=3)
        del(data[''])
        for student_id in self.students:
            student = self.students[student_id]
            try:
                student_registrations = data[student_id]
                for course in student_registrations:
                    record = student_registrations[course]
                    active = record['Status- Current'][0] in ['A', 'N']
                    student.register_foreign(course, active=active, date = record['Chg- Date'])
            except KeyError:
                if student.active:
                    pass
                    print('Active student {} missing Colleague data:'.format(student.real_name), 'Berklee ID: {}'.format(student.for_key.zfill(7)), 'BoCo ID:', student_id.zfill(9), sep='\n')
                    print('home registrations:')
                    pp.pprint(student.home_registrations)
                    print('foreign registrations:')
                    pp.pprint(student.for_registrations)
        #pp.pprint(data)


class Student():
    def __init__(self, name, real_name=None, for_key=None):
        self.name = name #home key
        self.real_name = real_name
        self.for_key = for_key
        self.home_registrations = {}
        self.for_registrations = {}
        self.active = False

        # Hack to deal with missing Berklee IDs from BoCo Data:
        if not self.for_key:
            try:
                self.for_key = missing_ids[name]
            except KeyError:
                pass # student might not be in Colleague yet; will handle later during read_foreign_roster

    def register_home(self, course_sec, active=True, date = None):
        self.home_registrations[course_sec] = {}
        self.home_registrations[course_sec]['active'] = active
        self.home_registrations[course_sec]['eff date'] = date
        for sec in self.home_registrations:
            if self.home_registrations[sec]['active']:
                self.active = True
                break

    def register_foreign(self, course_sec, active=True, date = None):
        # I know, I know
        self.for_registrations[course_sec] = {}
        self.for_registrations[course_sec]['active'] = active
        self.for_registrations[course_sec]['eff date'] = date
        for sec in self.for_registrations:
            if self.for_registrations[sec]['active']:
                self.active = True
                break

    def reckon(self):
        for course in self.home_registrations:
            course_data = self.home_registrations[course]
            if course in self.for_registrations:
                if course_data['active'] == self.for_registrations[course]['active']:
                    continue
                else:
                    print(self.name, '({})'.format(self.for_key), 'missing registration', course,
                          '(active status: {})'.format(course_data['active']), sep='\t')
            elif course_data['active']:
                print(self.name, '({})'.format(self.for_key), 'missing registration', course, sep='\t')


def main():

    # Doing work

    boco = Institution('Boston Conservatory')
    boco.read_home_roster()
    boco.read_foreign_roster()

    # Reviewing the data

    for student_id in boco.students:
        stud = boco.students[student_id]
        #pp.pprint(stud.home_registrations)
        #for course in stud.home_registrations:
        stud.reckon()

if __name__ == '__main__':
    main()