from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from search_app.models import UserProfile

class Command(BaseCommand):
    help = 'Create sample users with supervisor relationships for testing'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample users with organizational structure...')
        
        # Create supervisors first
        supervisors_data = [
            {
                'username': 'supervisor1',
                'email': 'supervisor1@test.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'password': 'supervisor123'
            },
            {
                'username': 'supervisor2', 
                'email': 'supervisor2@test.com',
                'first_name': 'Sarah',
                'last_name': 'Director',
                'password': 'supervisor123'
            },
            {
                'username': 'supervisor3',
                'email': 'supervisor3@test.com', 
                'first_name': 'Mike',
                'last_name': 'Lead',
                'password': 'supervisor123'
            }
        ]
        
        supervisors = []
        for sup_data in supervisors_data:
            supervisor, created = User.objects.get_or_create(
                username=sup_data['username'],
                defaults={
                    'email': sup_data['email'],
                    'first_name': sup_data['first_name'],
                    'last_name': sup_data['last_name']
                }
            )
            if created:
                supervisor.set_password(sup_data['password'])
                supervisor.save()
                UserProfile.objects.create(user=supervisor, is_supervisor=True)
                self.stdout.write(
                    self.style.SUCCESS(f'Created supervisor: {sup_data["username"]}/{sup_data["password"]}')
                )
            else:
                # Update existing user to be supervisor
                profile, created = UserProfile.objects.get_or_create(user=supervisor)
                profile.is_supervisor = True
                profile.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated existing user to supervisor: {sup_data["username"]}')
                )
            
            supervisors.append(supervisor)
        
        # Create regular users and assign them to supervisors
        users_data = [
            {
                'username': 'employee1',
                'email': 'employee1@test.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'password': 'employee123',
                'supervisor_index': 0  # John Manager
            },
            {
                'username': 'employee2',
                'email': 'employee2@test.com',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'password': 'employee123',
                'supervisor_index': 0  # John Manager
            },
            {
                'username': 'employee3',
                'email': 'employee3@test.com',
                'first_name': 'Carol',
                'last_name': 'Brown',
                'password': 'employee123',
                'supervisor_index': 1  # Sarah Director
            },
            {
                'username': 'employee4',
                'email': 'employee4@test.com',
                'first_name': 'David',
                'last_name': 'Wilson',
                'password': 'employee123',
                'supervisor_index': 1  # Sarah Director
            },
            {
                'username': 'employee5',
                'email': 'employee5@test.com',
                'first_name': 'Emma',
                'last_name': 'Davis',
                'password': 'employee123',
                'supervisor_index': 2  # Mike Lead
            },
            {
                'username': 'testuser',  # Keep your original testuser
                'email': 'user@test.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'testpass123',
                'supervisor_index': 0  # John Manager
            }
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name']
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                
                # Create profile and assign supervisor
                assigned_supervisor = supervisors[user_data['supervisor_index']]
                UserProfile.objects.create(
                    user=user, 
                    is_supervisor=False,
                    supervisor=assigned_supervisor
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created employee: {user_data["username"]}/{user_data["password"]} '
                        f'→ Supervisor: {assigned_supervisor.username}'
                    )
                )
            else:
                # Update existing user's supervisor if needed
                profile, created = UserProfile.objects.get_or_create(user=user)
                if not profile.supervisor:
                    assigned_supervisor = supervisors[user_data['supervisor_index']]
                    profile.supervisor = assigned_supervisor
                    profile.is_supervisor = False
                    profile.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated existing user: {user_data["username"]} '
                            f'→ Supervisor: {assigned_supervisor.username}'
                        )
                    )
        
        # # Create an admin user (optional)
        # admin, created = User.objects.get_or_create(
        #     username='admin',
        #     defaults={
        #         'email': 'admin@test.com',
        #         'first_name': 'Admin',
        #         'last_name': 'User',
        #         'is_staff': True,
        #         'is_superuser': True
        #     }
        # )
        # if created:
        #     admin.set_password('admin123')
        #     admin.save()
        #     UserProfile.objects.create(user=admin, is_supervisor=True)
        #     self.stdout.write(
        #         self.style.SUCCESS('Created admin: admin/admin123')
        #     )
        
        # Print summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('ORGANIZATIONAL STRUCTURE CREATED:'))
        self.stdout.write('='*50)
        
        for supervisor in supervisors:
            supervised_users = User.objects.filter(userprofile__supervisor=supervisor)
            self.stdout.write(f'\n👨‍💼 {supervisor.get_full_name()} ({supervisor.username})')
            self.stdout.write(f'   Supervises {supervised_users.count()} users:')
            for user in supervised_users:
                self.stdout.write(f'   ├── {user.get_full_name()} ({user.username})')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('LOGIN CREDENTIALS:'))
        self.stdout.write('='*50)
        self.stdout.write('Supervisors: supervisor1/supervisor123, supervisor2/supervisor123, supervisor3/supervisor123')
        self.stdout.write('Employees: employee1/employee123, employee2/employee123, etc.')
        self.stdout.write('Original: testuser/testpass123')
        self.stdout.write('Admin: admin/admin123')
        self.stdout.write('\nAll users created successfully! 🎉')
