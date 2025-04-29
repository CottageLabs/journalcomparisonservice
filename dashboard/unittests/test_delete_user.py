from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import Group
from django.http import HttpRequest
from accounts import models
from upload.models import UploadFile
from dashboard import views, ins_views


def mock_message(*newargs, **newkeywargs):
    pass


def mock_storage_delete(*newargs, **newkeywargs):
    pass


def get_request(post_data):
    request = HttpRequest()
    request.method = 'POST'
    request.POST = post_data
    request.META['SERVER_NAME'] = '127.0.0.1'
    request.META['SERVER_PORT'] = '8000'
    return request


class DeleteUserTestCase(TestCase):
    def create_publisher_super_user(self, id, publisher):
        # Create test PublisherAccount
        p_user = models.PSTFUser.objects.create(id=id, name='test_super_user' + str(id),
                                                email='test_suser' + str(id) + '@test.com', publisher=publisher,
                                                organisation=None)
        p_user.groups.set([self.super_publisher_group])

    def create_institution_super_user(self, id, institution):
        # Create test PublisherAccount
        p_user = models.PSTFUser.objects.create(id=id, name='test_super_user' + str(id),
                                                email='test_suser' + str(id) + '@test.com', publisher=None,
                                                organisation=institution)
        p_user.groups.set([self.super_organisation_group])

    def create_publisher_users(self):
        # Create test PublisherAccount
        self.publisher = models.PublisherAccount.objects.create(publisher_name="Publisher1", id=1011)
        self.p_user1 = models.PSTFUser.objects.create(id=202, name='test_super_user1', email='test_user1@test.com',
                                                      publisher=self.publisher, organisation=None)
        self.p_user1.groups.set([self.super_publisher_group])
        self.p_user2 = models.PSTFUser.objects.create(id=203, name='test_user2', email='test_user2@test.com',
                                                      publisher=self.publisher, organisation=None)
        self.p_user2.groups.set([self.publisher_group])

    def create_institutional_users(self):
        # Create test Institution user Accounts
        self.institution = models.EndUserAccount.objects.create(id=1012, organisation_name="Institution")
        self.i_user1 = models.PSTFUser.objects.create(id=104, name='test_user4', email='ins_user4@test.com',
                                                      organisation=self.institution, publisher=None)
        self.i_user1.groups.set([self.super_organisation_group])
        self.i_user2 = models.PSTFUser.objects.create(id=105, name='test_user5', email='ins_user5@test.com',
                                                      organisation=self.institution, publisher=None)
        self.i_user2.groups.set([self.organisation_group])

    def setUp(self):
        self.super_publisher_group = Group.objects.create(name='SuperPublisher')
        self.super_organisation_group = Group.objects.create(name='InstitutionalSuperUser')
        self.publisher_group = Group.objects.create(name='Publisher')
        self.organisation_group = Group.objects.create(name='InstitutionalUser')
        self.coalitions_group = Group.objects.create(name='CoalitionS')
        self.coalitions_user1 = models.PSTFUser.objects.create(id=4, name='coalitionS user1',
                                                               email='coalitions_user1@test.com')
        self.coalitions_user1.groups.set([self.coalitions_group])

    @patch('django.contrib.messages.success', mock_message)
    def test_super_publisher_delete_user(self):
        """Delete a super publisher user if more than one super publisher user exists"""
        self.create_publisher_users()
        self.create_publisher_super_user(2011, self.publisher)
        self.p_user1.rejected = True
        self.p_user1.save()
        request = get_request({'delete': ''})
        request.user = self.coalitions_user1
        response = views.publisher_archived_superuser(request, 202)
        self.assertEqual(models.PSTFUser.objects.filter(id=202).count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    def test_super_publisher_do_not_delete_user(self):
        """Do not delete a super publisher user if only one super publisher user exists"""
        self.create_publisher_users()
        self.p_user1.rejected = True
        self.p_user1.save()
        request = get_request({'delete': ''})
        request.user = self.coalitions_user1
        response = views.publisher_archived_superuser(request, 202)
        self.assertEqual(models.PSTFUser.objects.filter(id=202).count(), 1)

    @patch('django.contrib.messages.success', mock_message)
    def test_super_publisher_force_delete_user(self):
        """Delete a super publisher user even if only one super publisher user exists"""
        self.create_publisher_users()
        self.p_user1.rejected = True
        self.p_user1.save()
        request = get_request({'delete_user_confirm': ''})
        request.user = self.coalitions_user1
        response = views.publisher_archived_superuser(request, 202)
        self.assertEqual(models.PSTFUser.objects.filter(id=202).count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    @patch('django.core.files.storage.default_storage.delete', mock_storage_delete)
    def test_delete_publisher_account(self):
        """Delete the publisher account of a publisher user"""
        self.create_publisher_users()
        # Upload file for the publisher
        upload_file = UploadFile.objects.create(original_file_name='Test File', framework='ip',
                                                publisher=self.publisher, data_year='2022')
        self.p_user1.rejected = True
        self.p_user1.save()
        request = get_request({'delete_account': ''})
        request.user = self.coalitions_user1
        response = views.publisher_archived_superuser(request, 202)
        self.assertEqual(models.PublisherAccount.objects.filter(id=1011).count(), 0)

        # Make uploaded files for the publisher also gets deleted
        self.assertEqual(UploadFile.objects.filter(original_file_name='Test File').count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    def test_delete_publisher_user(self):
        """Delete a publisher user"""
        self.create_publisher_users()
        self.p_user2.rejected = True
        self.p_user2.save()
        request = get_request({'delete': ''})
        request.user = self.p_user1
        response = views.publisher_archived_user(request, 203)
        self.assertEqual(models.PSTFUser.objects.filter(id=203).count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    def test_institution_delete_super_user(self):
        """Delete a super institution user if more than one super institution user exists"""
        self.create_institutional_users()
        self.create_institution_super_user(3021, self.institution)
        self.i_user1.rejected = True
        self.i_user1.save()
        request = get_request({'delete': ''})
        request.user = self.coalitions_user1
        response = ins_views.archived_ins_superuser(request, 104)
        self.assertEqual(models.PSTFUser.objects.filter(id=104).count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    def test_institution_do_not_delete_super_user(self):
        """Do not delete a super institution user if only one super institution user exists"""
        self.create_institutional_users()
        self.i_user1.rejected = True
        self.i_user1.save()
        request = get_request({'delete': ''})
        request.user = self.coalitions_user1
        response = ins_views.archived_ins_superuser(request, 104)
        self.assertEqual(models.PSTFUser.objects.filter(id=104).count(), 1)

    @patch('django.contrib.messages.success', mock_message)
    def test_institution_force_delete_super_user(self):
        """Do not delete a super institution user if only one super institution user exists"""
        self.create_institutional_users()
        self.i_user1.rejected = True
        self.i_user1.save()
        request = get_request({'delete_user_confirm': ''})
        request.user = self.coalitions_user1
        response = ins_views.archived_ins_superuser(request, 104)
        self.assertEqual(models.PSTFUser.objects.filter(id=104).count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    def test_delete_institution_account(self):
        """Do not delete a super institution user if only one super institution user exists"""
        self.create_institutional_users()
        self.i_user1.rejected = True
        self.i_user1.save()
        request = get_request({'delete_account': ''})
        request.user = self.coalitions_user1
        response = ins_views.archived_ins_superuser(request, 104)
        self.assertEqual(models.EndUserAccount.objects.filter(id=1012).count(), 0)

    @patch('django.contrib.messages.success', mock_message)
    def test_delete_institution_user(self):
        """Delete an institution user"""
        self.create_institutional_users()
        self.i_user2.rejected = True
        self.i_user2.save()
        request = get_request({'delete': ''})
        request.user = self.i_user1
        response = ins_views.ins_archived_user(request, 105)
        self.assertEqual(models.PSTFUser.objects.filter(id=105).count(), 0)
