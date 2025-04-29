from django.core.paginator import Paginator
from django.db.models import Q, F, Value, When, CharField, Case
from django.db.models.functions import Coalesce, Lower
from accounts import models
from upload.models import UploadFile
from pstf import constants


class DatabaseQueryService:

    @classmethod
    def search(cls, query):
        q_object = cls.build_query_object(query)
        # sort a field to sort by, options account_name and application_date (default to account_name)
        sort_args = cls.determine_sort_args(query)

        ordered_users = models.PSTFUser.objects.filter(q_object).annotate(
            publisher_name=Coalesce('publisher__publisher_name', Value('')),
            organisation_name=Coalesce('organisation__organisation_name', Value(''))
        ).order_by(sort_args)

        results = cls.filter_uploaded_data(ordered_users, query)

        page_obj = cls.paginate_results(results, query)

        return page_obj

    @classmethod
    def determine_sort_args(cls, query):
        sort_by = query.get("sort", "account_name")
        sort_dir = query.get("sort_dir", "asc")

        sort_by_name_asc = Case(
            When(Q(publisher__isnull=False), then=Lower(F('publisher_name'))),
            When(Q(organisation__isnull=False), then=Lower(F('organisation_name'))),
            default=Value(''),
            output_field=CharField(),
        ).asc(nulls_last=True)

        sort_by_name_desc = Case(
            When(Q(publisher__isnull=False), then=Lower(F('publisher_name'))),
            When(Q(organisation__isnull=False), then=Lower(F('organisation_name'))),
            default=Value(''),
            output_field=CharField(),
        ).desc(nulls_last=True)

        if sort_dir == 'asc' and sort_by == 'application_date':
            return 'created'
        elif sort_dir == 'asc' and sort_by == 'account_name':
            return sort_by_name_asc
        elif sort_dir == 'desc' and sort_by == 'application_date':
            return '-created'
        elif sort_dir == 'desc' and sort_by == 'account_name':
            return sort_by_name_desc
        else:
            return sort_by_name_asc

    @classmethod
    def filter_uploaded_data(cls, users, query):
        users_to_filter = []
        query_has_uploaded_data = query.get("has_uploaded_data")
        query_data_year = query.get("data_years")
        query_framework = query.get("framework")

        for user in users:
            data_years = []
            frameworks = []
            upload_years = []
            user.has_uploads = False
            user.is_publisher = False
            if user.groups.filter(name=constants.SUPER_PUBLISHER_GROUP).exists():
                user.is_publisher = True
                publisher = user.publisher
                upload_files = UploadFile.objects.filter(publisher=publisher)
                if upload_files and upload_files.count() > 0:
                    user.has_uploads = True
                    for upload_file in upload_files:
                        upload_years.append({"year": upload_file.data_year, "framework": upload_file.framework})
                        data_years.append(upload_file.data_year)
                        frameworks.append(upload_file.framework)

                if query_has_uploaded_data and not user.has_uploads:
                    users_to_filter.append(user)

                if query_data_year and (int(query_data_year) not in data_years):
                    if user not in users_to_filter:
                        users_to_filter.append(user)
                if query_framework and (query_framework not in frameworks):
                    if user not in users_to_filter:
                        users_to_filter.append(user)

            # Remove any other users if there is a query on upload data because
            # upload data is only related to publishers
            elif query_has_uploaded_data or query_data_year or query_framework:
                users_to_filter.append(user)

            user.data_years = data_years
            user.frameworks = frameworks
            user.upload_years = upload_years

        users_list = list(users)
        for user in users_to_filter:
            users_list.remove(user)

        return users_list

    @classmethod
    def paginate_results(cls, results, query):
        page_size = int(query.get("page_size", 5))
        page_number = int(query.get("page", 1))

        paginator = Paginator(results, page_size)
        page_obj = paginator.get_page(page_number)

        return page_obj

    @classmethod
    def build_query_object(cls, query):
        q_object = None
        q_list = []
        # q - a free text query( if omitted, don't filter by query)
        q = query.get("q", None)
        if q:
            free_text_obj = cls.build_free_text(q)
            q_list.append(free_text_obj)

        # workflow_status - a workflow status keyword(approved, pending, etc)( if omitted, don 't filter)
        workflow_status = query.getlist("workflow_status")
        if workflow_status:
            q_list.append(cls.build_workflow_status(workflow_status))

        # user_type - institutional or publisher (only searches super admins, I think) (if omitted, don't filter)
        user_type = query.get("user_type")
        group = cls.user_group(user_type)
        if group:
            q_list.append(group)

        if q_list:
            q_object = q_list.pop()
            for q in q_list:
                q_object &= q
        else:
            q_object = Q()

        return q_object

    @classmethod
    def build_free_text(cls, free_text):
        fields = ["email", "name", "publisher__publisher_name", "publisher__journal", "organisation__organisation_name"]
        q_list = [Q(**{f"{field}__icontains": free_text}) for field in fields]
        q_object = q_list.pop()
        for q in q_list:
            q_object |= q

        return q_object

    @classmethod
    def build_workflow_status(cls, workflow_status):
        query = Q()
        if 'pending' in workflow_status:
            query |= Q(is_active=False) & Q(rejected=False) & \
                   Q(review_status=models.PSTFUser.ReviewStatus.AWAITING_REVIEW)
        if 'approved' in workflow_status:
            query |= Q(is_active=True)
        if 'rejected' in workflow_status:
            query |= Q(rejected=True)
        if 'awaiting_contract_signing' in workflow_status:
            query |= Q(is_active=False) & Q(rejected=False) & \
                   Q(review_status=models.PSTFUser.ReviewStatus.AWAITING_CONTRACT_SIGNING)

        return query

    @classmethod
    def user_group(cls, user_type):
        if user_type == 'publisher':
            return Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
        elif user_type == 'institutional':
            return Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
        else:
            return Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP) | \
                    Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
