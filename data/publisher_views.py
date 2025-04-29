import logging
from json import JSONDecodeError

from django.http import HttpResponse, Http404
import json

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from pstf.decorators import is_publisher_user

logger = logging.getLogger(__name__)

# TODO Make sure connection creation is efficient


@is_publisher_user
def search(request):
    """
    This view acts as a proxy to Elasticsearch to accommodate Edges.
    (https://github.com/CottageLabs/edges)
    It takes a get parameter with the key ''source'', parses its value as a JSON object and
    passes to Elasticsearch as the query to the ''journals'' index.
    :param request:
    :return:
    """

    client = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    source = request.GET.get('source', '')
    response = {'results': 0}

    if source != '':
        try:
            publisher_id = request.user.publisher.id
            source = json.loads(source)
            s = Search.from_dict(source).using(client).index(settings.ELASTICSEARCH_ALIAS)
            # Apply a hard constraint on the publisher_id
            s = s.query("term", **{"publisher_id": publisher_id})
            print("Limited query: ", s.to_dict())
            response_obj = s.execute()
            response = response_obj.to_dict()
        except KeyError as ke:
            logger.debug(f'"Query" parameter incorrect. {ke}')
        except JSONDecodeError as jde:
            logger.debug(f'JSON incorrectly formatted. {jde}')
        except Exception as e:
            logger.debug(f'"Unknown error. {e}')

    return HttpResponse(json.dumps(response), content_type='application/json')


@is_publisher_user
def autocomplete(request, type, query):
    """
    Test endpoint for building the search interface autocompletes.  Will need to be replaced with
    a proper implementation
    """
    publisher_id = request.user.publisher.id
    response = []
    if type == "journal":
        return _journal_ac(query, publisher_id)
    elif type == "discipline":
        return _discipline_ac(query)

    return HttpResponse(json.dumps(response), content_type="application/json")


def _discipline_ac(query, size=10):
    str = query.lower().strip()
    q = {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "should": [
                            {"prefix": {"name.raw": str}},
                            {"prefix": {"name_ac.raw": str}},
                            {"prefix": {"name": str}},
                            {"prefix": {"name_ac": str}},
                            {"match": {"name": str}},
                            {"match": {"name_ac": str}}
                        ]
                    }
                },
                "functions": [
                    {
                        "filter": {"term": {"name.raw": str}},
                        "weight": 20
                    },
                    {
                        "filter": {"prefix": {"name.raw": str}},
                        "weight": 15
                    },
                    {
                        "filter": {"term": {"name_ac.raw": str}},
                        "weight": 15
                    },
                    {
                        "filter": {"prefix": {"name_ac.raw": str}},
                        "weight": 5
                    }
                ]
            }
        },
        "size": size
    }

    client = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    s = Search.from_dict(q).using(client).index(settings.ES_AUTOCOMPLETE_DISCIPLINE_ALIAS)
    response_obj = s.execute()
    response = response_obj.to_dict()

    ac = []
    for r in response.get("hits", {}).get("hits", []):
        s = r.get("_source", {})
        ac.append(s.get("name"))

    return HttpResponse(json.dumps(ac), content_type='application/json')


def _journal_ac(query, publisher_id, size=10):
    str = query.lower().strip()
    q = {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "must": [
                            {"term" : {"publisher_id": publisher_id}}
                        ],
                        "should": [
                            {"prefix": {"title.raw": str}},
                            {"prefix": {"title_ac.raw": str}},
                            {"prefix": {"issn.raw": str}},
                            {"prefix": {"issn_ac.raw": str}},
                            {"prefix": {"title": str}},
                            {"prefix": {"title_ac": str}},
                            {"prefix": {"issn_ac": str}},
                            {"match": {"title": str}},
                            {"match": {"title_ac": str}},
                            {"match": {"issn_ac": str}}
                        ]
                    }
                },
                "functions": [
                    {
                        "filter": {"term": {"issn.raw": str}},
                        "weight": 20
                    },
                    {
                        "filter": {"prefix": {"issn.raw": str}},
                        "weight": 15
                    },
                    {
                        "filter": {"term": {"title.raw": str}},
                        "weight": 15
                    },
                    {
                        "filter": {"term": {"title_ac.raw": str}},
                        "weight": 10
                    },
                    {
                        "filter": {"prefix": {"title.raw": str}},
                        "weight": 5
                    },
                    {
                        "filter": {"prefix": {"title_ac.raw": str}},
                        "weight": 4
                    }
                ]
            }
        },
        "size": size
    }

    client = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    s = Search.from_dict(q).using(client).index(settings.ES_AUTOCOMPLETE_JOURNAL_ALIAS)
    response_obj = s.execute()
    response = response_obj.to_dict()

    ac = []
    for r in response.get("hits", {}).get("hits", []):
        s = r.get("_source", {})
        ac.append({"title" : s.get("title"), "issn": s.get("issn")})

    return HttpResponse(json.dumps(ac), content_type='application/json')
