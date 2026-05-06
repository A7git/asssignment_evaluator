"""Seed demo data for testing the system."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.assignment import Assignment, Rubric
from app.models.submission import Submission
from app.models.evaluation import Evaluation
from app.models.user import User


def seed():
    app = create_app()
    with app.app_context():
        # Tables are created in __init__.py, but ensure admin exists
        from app import _seed_admin
        _seed_admin(app)

        # Check if data already exists
        if Assignment.query.count() > 0:
            print('Data already seeded. Skipping.')
            return

        admin = User.query.filter_by(role='faculty').first()
        
        # Create a demo student
        student = User.query.filter_by(username='student1').first()
        if not student:
            student = User(
                username='student1',
                email='student1@university.edu',
                full_name='Arjun Sharma',
                role='student',
                student_id='2024CS001'
            )
            student.set_password('student123')
            db.session.add(student)
            
        student2 = User.query.filter_by(username='student2').first()
        if not student2:
            student2 = User(
                username='student2',
                email='student2@university.edu',
                full_name='Priya Patel',
                role='student',
                student_id='2024CS002'
            )
            student2.set_password('student123')
            db.session.add(student2)
        
        db.session.commit()

        # Create more students
        students = []
        for i in range(3, 15):
            s = User(
                username=f'student{i}',
                email=f'student{i}@university.edu',
                full_name=f'Student User {i}',
                role='student',
                student_id=f'2024CS{i:03d}'
            )
            s.set_password('student123')
            db.session.add(s)
            students.append(s)
        
        db.session.commit()
        
        all_students = [student, student2] + students

        # --- Assignment 1: Python Coding ---
        a1 = Assignment(
            faculty_id=admin.id,
            title='Binary Search Implementation',
            description='Implement a binary search function that takes a sorted list and a target value. Return the index of the target if found, or -1 if not found.',
            assignment_type='coding',
            language='python',
            reference_solution='''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

arr = list(map(int, input().split()))
target = int(input())
print(binary_search(arr, target))''',
        )
        a1.test_cases = [
            {'input': '1 3 5 7 9 11\n7', 'expected_output': '3'},
            {'input': '2 4 6 8 10\n5', 'expected_output': '-1'},
            {'input': '1\n1', 'expected_output': '0'},
        ]
        db.session.add(a1)
        db.session.flush()

        for c, w, d in [('Correctness', 40, 'Test cases pass rate'),
                         ('Code Quality', 25, 'Style and readability'),
                         ('Originality', 20, 'Not plagiarized'),
                         ('Efficiency', 15, 'Algorithm efficiency')]:
            db.session.add(Rubric(assignment_id=a1.id, criterion=c, weight=w, description=d))

        # --- Assignment 2: Descriptive ---
        a2 = Assignment(
            faculty_id=admin.id,
            title='Operating System Concepts Essay',
            description='Write an essay explaining the key differences between process and thread. Include examples of when each is preferred.',
            assignment_type='descriptive',
            reference_solution='A process is an independent execution unit with its own memory space, while a thread is a lightweight execution unit within a process that shares the same memory space. Processes are isolated and communicate via IPC mechanisms like pipes, sockets, and shared memory. Threads within the same process share heap memory but have their own stack. Processes are preferred for isolation and security, such as running separate applications. Threads are preferred for parallelism within a single application, such as handling multiple client requests in a web server. Context switching between threads is faster than between processes because threads share memory.',
        )
        db.session.add(a2)
        db.session.flush()

        for c, w, d in [('Correctness', 30, 'Accuracy of content'),
                         ('Clarity', 25, 'Writing quality'),
                         ('Completeness', 25, 'Topic coverage'),
                         ('Originality', 20, 'Original writing')]:
            db.session.add(Rubric(assignment_id=a2.id, criterion=c, weight=w, description=d))

        db.session.commit()

        # --- Generate Mock Submissions ---
        from app.routes.evaluation import perform_evaluation
        import random

        # Variations of binary search
        bs_good = '''def binary_search(arr, target):
    l, r = 0, len(arr) - 1
    while l <= r:
        m = (l + r) // 2
        if arr[m] == target: return m
        if arr[m] < target: l = m + 1
        else: r = m - 1
    return -1
arr = list(map(int, input().split()))
target = int(input())
print(binary_search(arr, target))'''

        bs_bad = '''def search(a, t):
    for i in range(len(a)):
        if a[i] == t: return i
    return -1
arr = list(map(int, input().split()))
target = int(input())
print(search(arr, target))''' # Linear instead of binary

        bs_error = '''def binary_search(arr, target)
    return -1''' # Syntax error

        # variations of OS essay
        os_good = "A process is an instance of a computer program that is being executed. It contains the program code and its current activity. A thread is the smallest unit of processing that can be performed in an OS. Threads are part of a process. Processes have separate address spaces, while threads share them. For example, a web browser process might have many threads for rendering, networking, and UI."
        os_copied = "A process is an independent execution unit with its own memory space, while a thread is a lightweight execution unit within a process that shares the same memory space. Processes are isolated and communicate via IPC. Threads within the same process share heap memory but have their own stack." # Highly similar to reference

        for i, s in enumerate(all_students):
            # Assignment 1 Submissions
            content1 = bs_good if i % 2 == 0 else (bs_bad if i % 3 == 0 else bs_error)
            sub1 = Submission(
                assignment_id=a1.id, user_id=s.id,
                student_id=s.student_id, student_name=s.full_name,
                file_path=f'sub1_{s.username}.py', file_name='solution.py',
                file_type='py', extracted_text=content1, status='pending'
            )
            db.session.add(sub1)
            db.session.flush()
            perform_evaluation(sub1.id)

            # Assignment 2 Submissions (half the students)
            if i % 2 == 0:
                content2 = os_good if i % 4 != 0 else os_copied
                if i == 0: content2 = "Processes and threads are different. Processes are big, threads are small." # Low quality
                
                sub2 = Submission(
                    assignment_id=a2.id, user_id=s.id,
                    student_id=s.student_id, student_name=s.full_name,
                    file_path=f'sub2_{s.username}.txt', file_name='essay.txt',
                    file_type='txt', extracted_text=content2, status='pending'
                )
                db.session.add(sub2)
                db.session.flush()
                perform_evaluation(sub2.id)

        db.session.commit()
        print('[OK] Enhanced demo data seeded and evaluated successfully!')
        print(f'   - {Assignment.query.count()} assignments')
        print(f'   - {Submission.query.count()} submissions')
        print(f'   - {Evaluation.query.count()} evaluations')


if __name__ == '__main__':
    seed()
