import logging
from json import JSONDecodeError
import datetime

from django.http import HttpResponse, Http404, JsonResponse
import json

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from pstf.decorators import is_institutional_user
from data.models import InformationPower, FairOpenAccessAlliance

logger = logging.getLogger(__name__)


@is_institutional_user
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
            source = json.loads(source)
            s = Search.from_dict(source).using(client).index(settings.ELASTICSEARCH_ALIAS)
            response_obj = s.execute()
            response = response_obj.to_dict()
        except KeyError as ke:
            logger.debug(f'"Query" parameter incorrect. {ke}')
        except JSONDecodeError as jde:
            logger.debug(f'JSON incorrectly formatted. {jde}')
        except Exception as e:
            logger.debug(f'"Unknown error. {e}')

    return HttpResponse(json.dumps(response), content_type='application/json')


@is_institutional_user
def autocomplete(request, type, query=None):
    """
    Test endpoint for building the search interface autocompletes.  Will need to be replaced with
    a proper implementation
    """

    response = []
    if type == "journal":
        return _journal_ac(query)
    elif type == "publisher":
        return _publisher_ac(query)
    elif type == "discipline":
        return _discipline_ac(query)
    elif type == "year":
        return _year_ac(query)

    return HttpResponse(json.dumps(response), content_type="application/json")


@is_institutional_user
def publisher_lookup(request, id) :
    q = {
        "query": {
            "bool": {
                "must": [
                    {"term" : {"publisher_id": id}}
                ]
            }
        }
    }

    client = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    s = Search.from_dict(q).using(client).index(settings.ES_AUTOCOMPLETE_PUBLISHER_ALIAS)
    response_obj = s.execute()
    response = response_obj.to_dict()

    ac = []
    hits = response.get("hits", {}).get("hits", [])
    if len(hits) == 0:
        raise Http404()

    s = hits[0].get("_source", {})
    obj = {"name": s.get("name"), "country": s.get("country"), "id": s.get("publisher_id")}
    return HttpResponse(json.dumps(obj), content_type='application/json')

def _year_ac(query=None):
    """
    Get the years list matching the requested year.
    If not mentioned any specific year, get all the years in descending order.
    Years starts from 2021 as that is the year user started uploading.
    Latest is the last year as user can upload data for last year only
    """
    current_year = datetime.datetime.now().year
    years = [year for year in range(current_year - 1, 2020, -1 )]
    matching_years = []
    if query:
        for year in years:
            if str(year).startswith(query):
                matching_years.append(year)
    else:
        matching_years = years
    return HttpResponse(json.dumps(matching_years), content_type='application/json')


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


def _publisher_ac(query, size=10):
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
    s = Search.from_dict(q).using(client).index(settings.ES_AUTOCOMPLETE_PUBLISHER_ALIAS)
    response_obj = s.execute()
    response = response_obj.to_dict()

    ac = []
    for r in response.get("hits", {}).get("hits", []):
        s = r.get("_source", {})
        ac.append({"name": s.get("name"), "country" : s.get("country"), "id": s.get("publisher_id")})

    return HttpResponse(json.dumps(ac), content_type='application/json')


def _journal_ac(query, size=10):
    str = query.lower().strip()
    q = {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
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


def issns(request, year):
    """"Return all ISSNs"""
    issns = list(InformationPower.objects.filter(year=year).values('issn', 'journal_title','publisher'))
    foaa_issns = list(FairOpenAccessAlliance.objects.filter(year=year).values('issn','journal_title','publisher'))

    issns.extend(foaa_issns)

    return JsonResponse({'issns':list(issns)})
