from django.utils.html import escape
from accounts.models import PSTFUser


class ElasticsearchSerializer:

    @classmethod
    def is_status_approved(cls, user):
        return user.is_active

    @classmethod
    def is_status_awaiting(cls, user):
        return not user.is_active and not user.rejected and user.review_status == PSTFUser.ReviewStatus.AWAITING_REVIEW

    @classmethod
    def is_status_archived(cls, user):
        return user.rejected

    @classmethod
    def is_status_awaiting_contract_signing(cls, user):
        return not user.is_active and not user.rejected and \
               user.review_status == PSTFUser.ReviewStatus.AWAITING_CONTRACT_SIGNING

    @classmethod
    def serialize(cls, page):
        hits = []
        total_items = page.paginator.object_list
        approved_users_count = sum(1 for result in total_items if cls.is_status_approved(result))
        awaiting_users_count = sum(1 for result in total_items if cls.is_status_awaiting(result))
        archived_users_count = sum(1 for result in total_items if cls.is_status_archived(result))
        awaiting_contract_signing = sum(1 for result in total_items if cls.is_status_awaiting_contract_signing(result))
        publisher_users = sum(1 for result in total_items if result.groups.filter(name='SuperPublisher').exists())
        institutional_users = sum(1 for result in total_items if result.groups.filter(
            name='InstitutionalSuperUser').exists())
        uploads_count = sum(1 for result in total_items if result.has_uploads)

        for item in page.object_list:
            user_id = item.id
            status = "pending" if cls.is_status_awaiting(item) else "approved" if cls.is_status_approved(item) \
                     else "rejected" if cls.is_status_archived(item) else "awaiting_contract_signing" if \
                     cls.is_status_awaiting_contract_signing(item) else None

            name = item.publisher.publisher_name if item.publisher else item.organisation.organisation_name

            if item.is_publisher:
                status_param = "approvedusers" if status == "approved" else "awaitingusers" if status == "pending" \
                    else "archived_user" if status == "rejected" else "awaiting_contract_signing_users" \
                    if status == "awaiting_contract_signing" else None
            else:
                status_param = "approved_ins_users" if status == "approved" else "awaiting_ins_users" \
                    if status == "pending" else "archived_ins_users" if status == "rejected" \
                    else "awaiting_contract_signing_ins_users" if status == "awaiting_contract_signing" else None

            if status_param:
                title = "<a href='/dashboard/coalitions/" + status_param + "/" + str(user_id) + "/'>" + escape(name) + "</a>"
            else:
                title = name

            hits.append(
                {
                    "_source":
                        {
                            "id": user_id,
                            "name": title,
                            "username": escape(item.name),
                            "email": escape(item.email),
                            "application_submitted": item.created.strftime("%B %d, %Y"),
                            "workflow_status": status,
                            "upload_years": item.upload_years,
                            "framework": item.frameworks,
                            "has_uploaded_data": item.has_uploads,
                            "is_publisher": item.is_publisher
                        }
                }
            )

        result = {
            "hits": {
                "total": {
                    "relation": "eq",
                    "value": page.paginator.count  # the total number of records that match the query
                },
                "hits": hits
            },
            "aggregations": {
                "workflow_status": {
                    "buckets": [
                        {"key": "approved", "doc_count": approved_users_count},
                        {"key": "awaiting_contract_signing", "doc_count": awaiting_contract_signing},
                        {"key": "pending", "doc_count": awaiting_users_count},
                        {"key": "rejected", "doc_count": archived_users_count}
                    ]
                },
                "user_type": {
                    "buckets": [
                        {"key": "publisher", "doc_count": publisher_users},
                        {"key": "institutional", "doc_count": institutional_users}
                    ]
                },
                "has_uploads": {
                    "buckets": [
                        {"key": "has_uploads", "doc_count": uploads_count}
                    ]
                },
                "data_years": {
                    "buckets": []
                },
                "framework": {
                    "buckets": []
                }
            }
        }

        data_years_set = set()
        for item in total_items:
            for year in item.data_years:
                data_years_set.add(year)

        years_buckets = result['aggregations']['data_years']['buckets']

        for year in data_years_set:
            count = sum(1 for result in total_items if year in result.data_years)
            years_buckets.append({"key": year, "doc_count": count})

        framework_set = set()
        for item in total_items:
            for framework in item.frameworks:
                framework_set.add(framework)

        years_buckets = result['aggregations']['framework']['buckets']

        for framework in framework_set:
            count = sum(1 for result in total_items if framework in result.frameworks)
            years_buckets.append({"key": framework, "doc_count": count})

        cls.filter_empty_buckets(result)

        return result

    @classmethod
    def filter_empty_buckets(cls, data):
        """
        Remove the buckets whose count is 0
        :param data: data object
        """
        data["aggregations"]["workflow_status"]["buckets"] = [
            bucket for bucket in data["aggregations"]["workflow_status"]["buckets"] if bucket["doc_count"] > 0
        ]
        data["aggregations"]["user_type"]["buckets"] = [
            bucket for bucket in data["aggregations"]["user_type"]["buckets"] if bucket["doc_count"] > 0
        ]
        data["aggregations"]["has_uploads"]["buckets"] = [
            bucket for bucket in data["aggregations"]["has_uploads"]["buckets"] if bucket["doc_count"] > 0
        ]

