# question_service/question_service/view.py
from django.db.models import F, Q, Value, FloatField, Case, When
from django.db.models.functions import Coalesce, Cast
from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.db import connection
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, ChoiceFilter, NumberFilter
from .models import Question, Difficulty
from .serializer import QuestionListSerializer, QuestionDetailSerializer

class QuestionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"  # keep compatibility
    max_page_size = 100

    def get_page_size(self, request):
        # Support alias 'limit' in addition to default page_size
        limit = request.query_params.get("limit")
        if limit is not None:
            try:
                size = int(limit)
                if size < 1:
                    return self.page_size
                return min(size, self.max_page_size)
            except (TypeError, ValueError):
                return self.page_size
        return super().get_page_size(request)

class QuestionFilter(FilterSet):
    topic = CharFilter(method="filter_topic")
    category = CharFilter(method="filter_topic")  # alias of topic
    difficulty = ChoiceFilter(choices=Difficulty.choices)
    status = CharFilter(method="filter_status")  # active/inactive/true/false
    popularity_min = NumberFilter(method="filter_popularity_min")
    solved_by_user = CharFilter(method="filter_solved_by_user")  # placeholder hook

    def filter_topic(self, qs, name, value):
        values = self.request.query_params.getlist("topic") or [value]
        q = Q()
        for v in values:
            q |= Q(topics__icontains=v)  # JSON contains; swap for ArrayField with overlap if you change type
        return qs.filter(q)

    def filter_popularity_min(self, qs, name, value):
        return qs.filter(stats__attempts__gte=value)

    def filter_solved_by_user(self, qs, name, value):
        # TODO: join to your user progress model if/when available
        return qs

    def filter_status(self, qs, name, value):
        val = str(value).strip().lower()
        if val in ("1", "true", "active", "yes"):
            return qs.filter(is_active=True)
        if val in ("0", "false", "inactive", "no"):
            return qs.filter(is_active=False)
        return qs

    class Meta:
        model = Question
        fields = ["difficulty", "status"]

class QuestionViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = (Question.objects.all().filter(is_active=True).select_related("stats","score"))
    pagination_class = QuestionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = QuestionFilter

    def get_serializer_class(self):
        return QuestionDetailSerializer if self.action == "retrieve" else QuestionListSerializer

    def get_queryset(self):
        # annotate sortable fields with explicit Float casting and zero-guard
        solved_float = Cast(F("stats__solved"), FloatField())
        attempts_float = Cast(F("stats__attempts"), FloatField())
        percentage_expr = Case(
            When(stats__attempts__gt=0, then=(solved_float * Value(100.0)) / attempts_float),
            default=Value(0.0),
            output_field=FloatField(),
        )
        return (super().get_queryset()
                .annotate(
                    popularity=Coalesce(F("stats__attempts"), Value(0)),
                    percentage_solved_annot=percentage_expr,
                ))

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        # sorting
        sort = request.query_params.get("sort", "created_at")
        order = request.query_params.get("order", "desc")
        prefix = "-" if order == "desc" else ""
        sort_map = {
            "newest": f"{prefix}created_at",
            "created_at": f"{prefix}created_at",
            "difficulty": f"{prefix}difficulty",
            "percentage_solved": f"{prefix}percentage_solved_annot",
            "popularity": f"{prefix}popularity",
            "topic": f"{prefix}title",
            "category": f"{prefix}title",
        }
        qs = qs.order_by(sort_map.get(sort, f"-created_at"))

        # sparse fieldsets (?fields=title,topics,...)
        fields_param = request.query_params.get("fields")
        serializer_kwargs = {}
        if fields_param and self.action == "list":
            serializer_kwargs["fields"] = [f.strip() for f in fields_param.split(",") if f.strip()]

        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True, **serializer_kwargs)
        return self.get_paginated_response(serializer.data)

class TopicsView(APIView):
    def get(self, request):
        topics_list = []
        engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
        if 'postgresql' in engine:
            # Use Postgres JSONB unnest for distinct topic values
            sql = """
                SELECT DISTINCT jsonb_array_elements_text(q.topics) AS topic
                FROM questions q
                WHERE q.is_active = TRUE
                ORDER BY topic
            """
            with connection.cursor() as cursor:
                cursor.execute(sql)
                topics_list = [row[0] for row in cursor.fetchall()]
        else:
            # SQLite/dev fallback: flatten in Python
            seen = set()
            for arr in Question.objects.filter(is_active=True).values_list('topics', flat=True):
                if isinstance(arr, list):
                    for t in arr:
                        if isinstance(t, str):
                            seen.add(t)
            topics_list = sorted(seen)
        return Response({"topics": topics_list})
