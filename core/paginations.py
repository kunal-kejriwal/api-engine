from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.conf import settings

from .paginations_config import PLAN_PAGINATION_LIMITS


class PlanBasedPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"

    def get_page_size(self, request):
        user = request.user

        # Default fallback (unauthenticated / system calls)
        default_page_size = 10

        if not user.is_authenticated:
            return default_page_size

        profile = getattr(user, "profile", None)
        if not profile or not profile.plan:
            return default_page_size

        plan_name = profile.plan.name.upper()  # e.g. FREE, PRO

        plan_config = PLAN_PAGINATION_LIMITS.get(plan_name)
        if not plan_config:
            return default_page_size

        requested_size = request.query_params.get(self.page_size_query_param)

        # If user explicitly requests page_size
        if requested_size:
            try:
                requested_size = int(requested_size)
            except ValueError:
                raise ValidationError("Invalid page_size value")

            if requested_size > plan_config["max_page_size"]:
                raise ValidationError(
                    f"Max page size for {plan_name} plan is {plan_config['max_page_size']}"
                )

            return requested_size

        # Default page size per plan
        return plan_config["page_size"]
    
    def get_paginated_response(self, data):
        user = self.request.user
        plan = getattr(getattr(user, "profile", None), "plan", None)

        return Response({
            "plan": plan.name if plan else "UNKNOWN",
            "count": self.page.paginator.count,
            "page": self.page.number,
            "total_pages": self.page.paginator.num_pages,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
