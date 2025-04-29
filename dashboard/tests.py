from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.management import call_command
from accounts.models import *
from dashboard.report_views import *
from dashboard.export_views import *
from data import utils


class UserReportTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('create_groups', verbosity=0)

        ins_admin_user_group = Group.objects.get(name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
        ins_user_group = Group.objects.get(name=constants.INSTITUTIONAL_USER_GROUP)
        pub_admin_user_group = Group.objects.get(name=constants.SUPER_PUBLISHER_GROUP)
        pub_user_group = Group.objects.get(name=constants.PUBLISHER_GROUP)

        pub1 = PublisherAccount.objects.create(publisher_name="TestPublisher1", country="GBR", verified=True,
                                        created=True)
        pub2 = PublisherAccount.objects.create(publisher_name="TestPublisher2", country="GBR", verified=True,
                                        created=True)
        pub3 = PublisherAccount.objects.create(publisher_name="TestPublisher3", country="FRA", verified=True,
                                               created=True)
        ins1 = EndUserAccount.objects.create(organisation_name="Organisation1", country="GBR", verified=True,
                                        created=True)
        ins2 = EndUserAccount.objects.create(organisation_name="Organisation2", country="DEU", verified=True,
                                             created=True)
        pub_u1 = PSTFUser.objects.create_user(email="puser1@publisher1.com")
        pub_u1.publisher = pub1
        pub_u1.groups.add(pub_admin_user_group)
        pub_u1.save()
        pub_u2 = PSTFUser.objects.create_user(email="puser2@publisher1.com")
        pub_u2.publisher = pub1
        pub_u2.groups.add(pub_user_group)
        pub_u2.save()
        pub_u3 = PSTFUser.objects.create_user(email="puser3@publisher2.com")
        pub_u3.publisher = pub2
        pub_u3.groups.add(pub_admin_user_group)
        pub_u3.save()
        pub_u4 = PSTFUser.objects.create_user(email="puser4@publisher3.com")
        pub_u4.publisher = pub3
        pub_u4.groups.add(pub_admin_user_group)
        pub_u4.save()
        ins_u1 = PSTFUser.objects.create_user(email="insuser1@ins1.com")
        ins_u1.organisation = ins1
        ins_u1.groups.add(ins_admin_user_group)
        ins_u1.save()
        ins_u2 = PSTFUser.objects.create_user(email="insuser1@ins2.com")
        ins_u2.organisation = ins2
        ins_u2.groups.add(ins_admin_user_group)
        ins_u2.save()
        ins_u3 = PSTFUser.objects.create_user(email="insuser1@ins3.com")
        ins_u3.organisation = ins2
        ins_u3.groups.add(ins_user_group)
        ins_u3.save()

    def test_publisher_count(self):
        self.assertEqual(total_publishers().count(), 3)

    def test_countries_list_of_publishers(self):
        self.assertCountEqual(list(countries_list_of_publishers()), ['GBR', 'FRA'])

    def test_countries_list_of_institutions(self):
        self.assertEqual(list(countries_list_of_institutions()), ['GBR', 'DEU'])

    def test_users_data(self):
        data = users_data()

        self.assertEqual(data["All"]["publishers"], 3)
        self.assertEqual(data["All"]["institutions"], 2)
        self.assertEqual(data["All"]["pub_super_users"], 3)
        self.assertEqual(data["All"]["pub_users"], 4)
        self.assertEqual(data["All"]["ins_supers_users"], 2)
        self.assertEqual(data["All"]["ins_users"], 3)
        self.assertEqual(data["United Kingdom"]["publishers"], 2)
        self.assertEqual(data["United Kingdom"]["institutions"], 1)
        self.assertEqual(data["United Kingdom"]["pub_super_users"], 2)
        self.assertEqual(data["United Kingdom"]["pub_users"], 3)
        self.assertEqual(data["United Kingdom"]["ins_supers_users"], 1)
        self.assertEqual(data["United Kingdom"]["ins_users"], 1)
        self.assertEqual(data["France"]["publishers"], 1)
        self.assertEqual(data["France"]["institutions"], 0)
        self.assertEqual(data["France"]["pub_super_users"], 1)
        self.assertEqual(data["France"]["pub_users"], 1)
        self.assertEqual(data["France"]["ins_supers_users"], 0)
        self.assertEqual(data["France"]["ins_users"], 0)
        self.assertEqual(data["Germany"]["publishers"], 0)
        self.assertEqual(data["Germany"]["institutions"], 1)
        self.assertEqual(data["Germany"]["pub_super_users"], 0)
        self.assertEqual(data["Germany"]["pub_users"], 0)
        self.assertEqual(data["Germany"]["ins_supers_users"], 1)
        self.assertEqual(data["Germany"]["ins_users"], 2)


class UserExportTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(UserExportTests, cls).setUpClass()
        call_command('create_groups', verbosity=0)
        call_command('generate_db_data', 30, verbosity=0)
        cls.export_data = ExportData(121)

    @classmethod
    def tearDownClass(cls):
        super(UserExportTests, cls).tearDownClass()
        cls.export_data.delete_temp_dir()
        file_path = os.path.join(constants.TEMP_DIR, cls.export_data.context[cls.export_data.TMP_DIR_NAME] + ".zip")
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_create_package(self):
        self.export_data.create_temp_dir_path()
        self.assertTrue(self.export_data.context['tmp_dir_path'])

        self.export_data.copy_files_to_tmp()

        test_bool = os.path.exists(os.path.join(self.export_data.context[self.export_data.TMP_DIR_PATH],
                                                "data"+self.export_data.context[self.export_data.UNIQUE_ID]+".csv"))
        self.assertTrue(test_bool)

        test_bool = os.path.exists(os.path.join(self.export_data.context[self.export_data.TMP_DIR_PATH],
                                                self.export_data.AUP_FILE))
        self.assertTrue(test_bool)

        test_bool = os.path.exists(os.path.join(self.export_data.context[self.export_data.TMP_DIR_PATH],
                                                self.export_data.README_FILE))
        self.assertTrue(test_bool)

        test_list = utils.get_ip_data_for_issn_list([])
        self.assertEqual(len(test_list), 0)

        test_list = utils.get_all_ip_data()
        self.assertEqual(len(test_list), 15)

        test_list = utils.get_all_foaa_data()
        self.assertEqual(len(test_list), 15)

        #  Test csv file
        self.export_data.write_data_to_csv(test_list)
        csv_file_path = os.path.join(self.export_data.context[ExportData.TMP_DIR_PATH],
                                     "data"+self.export_data.context[self.export_data.UNIQUE_ID]+".csv")
        with open(csv_file_path, 'r') as file:
            csvreader = csv.reader(file)
            # count number of rows
            entry_count = sum(1 for row in csvreader)
            self.assertEqual(entry_count, 16)

        self.export_data.create_download_package()
        zip_file = os.path.join(constants.TEMP_DIR, self.export_data.context[self.export_data.TMP_DIR_NAME] + ".zip")
        self.assertTrue(os.path.exists(zip_file))
