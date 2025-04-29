import datetime
from unittest import mock
from django.utils import timezone
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import Group
from api.services import DatabaseQueryService
from accounts.models import PublisherAccount, EndUserAccount, PSTFUser
from upload.models import UploadFile


class DatabaseQueryServiceTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        publisher_group = Group.objects.create(name='SuperPublisher')
        organisation_group = Group.objects.create(name='InstitutionalSuperUser')

        # Create test PublisherAccount
        publisher = PublisherAccount.objects.create(publisher_name="Test Publisher", )
        publisher2 = PublisherAccount.objects.create(publisher_name="apple ltd")

        # Create test EndUserAccount
        organisation = EndUserAccount.objects.create(organisation_name="Test Organisation")

        # Create test PSTFUser objects
        # Add specific dates for testing sort by date
        specific_datetime = timezone.make_aware(datetime.datetime(2023, 10, 1, 12, 0))
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=specific_datetime)):
            user1 = PSTFUser.objects.create(
                title="Mr", email="user1@example.com", name="User 1", phone="1234567890", publisher=publisher,
                organisation=None
            )
            user1.groups.set([publisher_group])

        # Create test PSTFUser objects
        specific_datetime2 = timezone.make_aware(datetime.datetime(2023, 1, 1, 12, 0))
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=specific_datetime2)):
            user2 = PSTFUser.objects.create(
                title="Mr", email="user2@example.com", name="User 2",phone="1234567891",publisher=publisher2,
                organisation=None
            )
            user2.groups.set([publisher_group])
        upload_file = UploadFile.objects.create(original_file_name='Test File', framework='ip',
                                                publisher=publisher, data_year='2022')

        user3 = PSTFUser.objects.create(
            title="Ms",
            email="user3@example.com",
            name="User 3",
            phone="9876543210",
            publisher=None,
            organisation=organisation
        )
        user3.groups.set([organisation_group])

    def test_search(self):
        # Create a test query object
        # Create a test request object with the query parameters
        request = self.factory.get('/search', {'sort': ['name', 'date'], 'sort_dir': 'asc'})

        # Access the query parameters using the request.GET attribute
        query = request.GET

        # Call the search method with the test query
        result = DatabaseQueryService.search(query)

        # Assert the expected result based on your test case
        self.assertEqual(len(result.object_list), 3)

        # Add more assertions as needed

    def test_determine_sort_args(self):
        # Create a test request object with the query parameters
        request = self.factory.get('/search', {'sort': ['name'], 'sort_dir': 'asc'})

        # Access the query parameters using the request.GET attribute
        query = request.GET

        # Call the determine_sort_args method with the test query
        result = DatabaseQueryService.determine_sort_args(query)

        # Assert the expected result based on your test case
        self.assertTrue('publisher_name' in str(result))
        self.assertTrue('organisation_name' in str(result))

    def test_sort_by_name_case_insensitive(self):
        # Create a test request object with the query parameters
        request = self.factory.get('/search', {'sort': ['account_name'], 'sort_dir': 'asc', 'user_type':'publisher'})

        # Access the query parameters using the request.GET attribute
        query = request.GET

        # Call the search method with the test query
        result = DatabaseQueryService.search(query)

        # Assert the expected result based on your test case
        self.assertEqual("apple ltd", result.object_list[0].publisher.publisher_name)

    def test_sort_by_date_case_insensitive(self):
        # Create a test request object with the query parameters
        request = self.factory.get('/search', {'sort': ['application_date'], 'sort_dir': 'desc', 'user_type':'publisher'})

        # Access the query parameters using the request.GET attribute
        query = request.GET

        # Call the search method with the test query
        result = DatabaseQueryService.search(query)

        # Assert the expected result based on your test case
        self.assertEqual("Test Publisher", result.object_list[0].publisher.publisher_name)

    def test_filter_uploaded_data(self):
        # Create a test users queryset
        users = PSTFUser.objects.all()

        # Create a test request object with the query parameters
        request = self.factory.get('/search', {'has_uploaded_data': True, 'sort': ['name'], 'sort_dir': 'asc'})

        # Access the query parameters using the request.GET attribute
        query = request.GET

        # Call the filter_uploaded_data method with the test users queryset and query
        result = DatabaseQueryService.filter_uploaded_data(users, query)

        # Assert the expected result based on your test case
        self.assertEqual(len(result), 1)

        # Add more assertions as needed

    def test_paginate_results(self):
        # Create a test results list
        results = ["result1", "result2", "result3"]

        # Create a test query object
        query = {
            "page_size": 2,
            "page": 1,
        }

        # Call the paginate_results method with the test results list and query
        result = DatabaseQueryService.paginate_results(results, query)

        # Assert the expected result based on your test case
        self.assertEqual(len(result), 2)

        # Add more assertions as needed

    # Add test cases for other methods in the class

    def tearDown(self):
        # Perform any necessary cleanup after each test case
        pass
