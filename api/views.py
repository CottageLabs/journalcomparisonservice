from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services import DatabaseQueryService
from .serializers import ElasticsearchSerializer
from pstf.decorators import user_group
from pstf import constants


@require_GET
@user_group(constants.COALITION_S_GROUP)
def search(request):

    page = DatabaseQueryService.search(request.GET)
    results = ElasticsearchSerializer.serialize(page)

    return JsonResponse(results)
