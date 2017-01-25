import csv
from tools import get_file
from pprint import PrettyPrinter

# Read the BoCo and Berklee rosters, create student and class records, 
# and identify any students not registered in both systems.

pp = PrettyPrinter(indent=4)

class Institution():
    def __init__(self, name):
        self.name = name
        self.students = {}
        self.classes = []
        self.roster_data = []
        #home_loc = get_file('*csv', description='{} roster file'.format(name))
        #self.read_roster(home_loc)

    def add_student(self, **kwargs):
        s = Student(**kwargs)
        self.students[s.name] = s

    def read_roster(self, location, p_key_column, foreign=False):
        # Make a big dictionary of the data:
        data = {}
        with open(location, 'r') as infile:
            reader = csv.reader(infile)
            headers = next(reader)
            for row in reader:
                p_key = row[p_key_column]
                if not p_key in data:
                    data[p_key] = {}
                course = row[headers.index('BCM_CrsNo')]
                data[p_key][course] = {}
                for i, val in enumerate(row):
                    data[p_key][course][headers[i]] = val
        #pp.pprint(data)


        # Interpret the data by creating Student objects:
        for student in data:
            courses = data[student]
            for course in courses:
                record = courses[course]
                if not student in self.students:
                    self.add_student(name=student, real_name=record['Student'], for_key=record['BCM_StudID'])
                #pp.pprint(record)

            #self.add_student()

        print('Read', len(data), 'student records from', location)


class Student():
    def __init__(self, name, real_name=None, for_key=None):
        self.name = name #home key
        self.real_name = real_name
        self.for_key = for_key
        self.registrations = {}

    def register(self, course_sec, active=True):
        self.registrations[course_sec] = active

def main():
    berklee = Institution('Berklee')
    berklee.read_roster('/home/iroh/cross-reg/IntegCrsOff_BCB2BCM_2017-01-25.csv', p_key_column=9)


if __name__ == '__main__':
    main()